import json
import io
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/deploy-demo.yml'
PARTS = ('abi', 'strategy-runtime/specs', 'strategy-runtime/journal', 'strategy-runtime/state', 'journal')


class EnvironmentSwitchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='bbb-environment-test-')
        self.addCleanup(self.temporary.cleanup)
        self.shared = Path(self.temporary.name).resolve()
        for root in (self.shared, self.shared/'mainnet'):
            for part in PARTS:
                (root/part).mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ, BBB_DATA_ROOT=str(self.shared), ABI_EXPECTED_BYBIT_UID='123',
                        ABI_MAINNET_EXPECTED_BYBIT_UID='456', GITHUB_ENV=str(self.shared/'output.env'))
        workflow = WORKFLOW.read_text()
        self.selection = textwrap.dedent(workflow.split("python3 - <<'PYTHON'\n", 1)[1].split('\n          PYTHON', 1)[0])
        self._update = textwrap.dedent(workflow.split('      - name: Update stack (no volume removal)\n        run: |\n', 1)[1].split('\n      - name:', 1)[0])
        # Fake Docker handles only discovery/inspect/up. Never contacts the host daemon.
        directory = self.shared/'bin'
        directory.mkdir()
        docker = directory/'docker'
        docker.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as out:
    out.write(json.dumps(args) + '\\n')
if 'ps' in args:
    if '-a' in args: print('existing-abi')
    elif os.environ['RUNNING'] == 'yes': print('running-service')
elif args[0] == 'inspect':
    print('BYBIT_ENV=' + os.environ['CURRENT_ENV'])
elif 'up' not in args:
    raise SystemExit('Unexpected Docker call')
''')
        docker.chmod(0o755)
        self.fake_env = dict(self.env, PATH=str(directory)+os.pathsep+os.environ['PATH'], CALLS=str(self.shared/'calls.jsonl'))

    def select(self, environment):
        with patch.dict(os.environ, dict(self.env, BYBIT_ENV=environment), clear=True):
            exec(compile(self.selection, str(WORKFLOW), 'exec'), {})
        return dict(line.split('=', 1) for line in (self.shared/'output.env').read_text().splitlines())

    def update(self, current, selected, running):
        log = self.shared/'calls.jsonl'
        log.write_text('')
        result = subprocess.run(['bash', '-c', self._update], env=dict(self.fake_env,
            CURRENT_ENV=current, BYBIT_ENV=selected, RUNNING='yes' if running else 'no'), capture_output=True)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        return result, calls

    def test_four_deploy_scenarios(self):
        for current, selected, running, allowed in [('demo', 'demo', True, True), ('mainnet', 'mainnet', True, True),
                ('demo', 'mainnet', True, False), ('demo', 'mainnet', False, True), ('mainnet', 'demo', True, False)]:
            with self.subTest(current=current, selected=selected, running=running):
                result, calls = self.update(current, selected, running)
                self.assertEqual(result.returncode == 0, allowed, result.stderr.decode())
                ups = [call for call in calls if 'up' in call]
                self.assertEqual(len(ups), int(allowed))
                if allowed:
                    self.assertEqual(ups[0][-4:], ['up', '-d', '--no-build', '--remove-orphans'])
                self.assertFalse(any(arg in ('stop', 'down', 'restart', 'exec', '--force-recreate') for call in calls for arg in call))
        # Running MDS/Runtime with a stopped Demo ABI still blocks a switch: inspect uses ps -a.
        _, calls = self.update('demo', 'mainnet', True)
        self.assertTrue(any('ps' in call and '-a' in call for call in calls))

    def test_both_environments_use_same_images_history_and_selected_memory(self):
        configs = []
        for environment in ('demo', 'mainnet'):
            selected = self.select(environment)
            env = dict(self.env, **selected, BYBIT_ENV=environment, ABI_DRY_RUN='false', ABI_LIVE_TRADING_ENABLED='true')
            config = json.loads(subprocess.check_output(['docker', 'compose', '-f', 'docker-compose.yml', '-f',
                'docker-compose.deploy.yml', '--env-file', 'deploy/images.env', 'config', '--format', 'json'], cwd=ROOT, env=env))
            configs.append(config['services'])
            abi = config['services']['abi']
            self.assertEqual(abi['environment']['BYBIT_ENV'], environment)
            self.assertEqual(abi['environment']['ABI_EXPECTED_BYBIT_UID'], '123' if environment == 'demo' else '456')
            root = self.shared if environment == 'demo' else self.shared/'mainnet'
            for service, target, suffix in [('abi', '/app/var', 'abi'), ('strategy-runtime', '/runtime/state', 'strategy-runtime/state'),
                ('journal-service', '/data', 'journal'), ('research-service', '/runtime-specs', 'strategy-runtime/specs')]:
                mount = next(v for v in config['services'][service]['volumes'] if v['target'] == target)
                self.assertEqual(Path(mount['source']).resolve(), root/suffix)
        self.assertEqual(len(configs[0]), 6)
        self.assertEqual({k: v['image'] for k, v in configs[0].items()}, {k: v['image'] for k, v in configs[1].items()})
        for service in ('market-data-service', 'strategy-engine'):
            self.assertEqual(configs[0][service]['volumes'], configs[1][service]['volumes'])
        self.assertEqual(configs[0]['strategy-runtime']['depends_on'], configs[1]['strategy-runtime']['depends_on'])

    def test_repeat_deploy_preserves_memory_and_does_not_reset_authorization(self):
        files = []
        for root in (self.shared, self.shared/'mainnet'):
            for relative in ('abi/correlation.jsonl', 'abi/facts.sqlite3', 'strategy-runtime/state/runtime_state.jsonl',
                             'strategy-runtime/journal/runtime.jsonl', 'strategy-runtime/specs/strategy.json', 'journal/journal.sqlite3'):
                file = root/relative
                file.write_bytes(b'{"enabled":true,"fixture":"previous durable data"}')
                files.append(file)
        before = {file: file.read_bytes() for file in files}
        for environment in ('demo', 'mainnet'):
            for _ in range(2):
                self.select(environment)
                result, calls = self.update(environment, environment, True)
                self.assertEqual(result.returncode, 0)
                self.assertFalse(any('credentialRelay' in arg or arg in ('exec', 'restart', '--force-recreate') for call in calls for arg in call))
        self.assertEqual(before, {file: file.read_bytes() for file in files})
        # Post-deploy verification accepts an unchanged, still-authorized ABI.
        block = textwrap.dedent(WORKFLOW.read_text().split("python3 - <<'PYTHON'\n", 2)[2].split('\n          PYTHON', 1)[0])
        with patch.dict(os.environ, {'BYBIT_ENV': 'mainnet'}), patch('urllib.request.urlopen',
                return_value=io.BytesIO(json.dumps({'bybitEnvironment': 'mainnet', 'canExecuteLive': True}).encode())):
            exec(compile(block, str(WORKFLOW), 'exec'), {})


if __name__ == '__main__':
    unittest.main()
