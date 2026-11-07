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
        self.selection = textwrap.dedent(WORKFLOW.read_text().split("python3 - <<'PYTHON'\n", 1)[1].split('\n          PYTHON', 1)[0])

    def select(self, environment):
        with patch.dict(os.environ, dict(self.env, BYBIT_ENV=environment), clear=True):
            exec(compile(self.selection, str(WORKFLOW), 'exec'), {})
        return dict(line.split('=', 1) for line in (self.shared/'output.env').read_text().splitlines())

    def test_both_environments_use_same_images_history_and_six_services(self):
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

    def test_first_mainnet_refuses_enabled_or_invalid_deployment(self):
        file = self.shared/'mainnet/strategy-runtime/specs/strategy.json'
        for value in ('{"enabled": true}', '{"enabled": "false"}', '{}', 'not json'):
            file.write_text(value)
            with self.assertRaises((SystemExit, ValueError)):
                self.select('mainnet')
        file.write_text('{"enabled": false}')
        self.select('mainnet')
        # Normal redeployment never edits catalog or durable state.
        state = self.shared/'mainnet/strategy-runtime/state/runtime_state.jsonl'
        state.write_text('fixture durable state')
        file.write_text('{"enabled": true}')
        self.select('mainnet')
        self.assertEqual(file.read_text(), '{"enabled": true}')
        self.assertEqual(state.read_text(), 'fixture durable state')

    def test_deploy_requires_locked_socket_state_after_recreation(self):
        block = textwrap.dedent(WORKFLOW.read_text().split("python3 - <<'PYTHON'\n", 2)[2].split('\n          PYTHON', 1)[0])
        for state in ('LOCKED', 'AUTHORIZED'):
            response = io.BytesIO(json.dumps({'bybitEnvironment': 'mainnet', 'canExecuteLive': False}).encode())
            with patch.dict(os.environ, {'BYBIT_ENV': 'mainnet'}), \
                 patch('urllib.request.urlopen', return_value=response), \
                 patch('subprocess.check_output', side_effect=[b'fixture-id', json.dumps({'state': state}).encode()]):
                if state == 'LOCKED':
                    exec(compile(block, str(WORKFLOW), 'exec'), {})
                else:
                    with self.assertRaises(SystemExit):
                        exec(compile(block, str(WORKFLOW), 'exec'), {})
        self.assertIn('--force-recreate', WORKFLOW.read_text())
        self.assertIn('Stop the current stack before Deploy', WORKFLOW.read_text())

    def test_refuses_shared_memory_unknown_environment_and_missing_mainnet_uid(self):
        path = self.shared/'mainnet/abi'
        path.rmdir()
        path.symlink_to(self.shared/'abi', target_is_directory=True)
        with self.assertRaises(SystemExit):
            self.select('mainnet')
        path.unlink()
        path.mkdir()
        with self.assertRaises(SystemExit):
            self.select('other')
        del self.env['ABI_MAINNET_EXPECTED_BYBIT_UID']
        with self.assertRaises(SystemExit):
            self.select('mainnet')


if __name__ == '__main__':
    unittest.main()
