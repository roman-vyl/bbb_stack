import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import verify_mainnet_deploy as verify

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preflight', ROOT/'scripts/mainnet_preflight.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def environment(main, demo):
    values = dict(os.environ, BBB_MAINNET_DATA_ROOT=str(main), BBB_DATA_ROOT=str(main),
                  BBB_DEMO_DATA_ROOT=str(demo), ABI_MAINNET_EXPECTED_BYBIT_UID='123')
    for key, service in [(v, k) for k, v in p.SERVICES.items()]:
        values[key] = 'ghcr.io/roman-vyl/' + {'abi': 'abi_executor_bot', 'strategy-engine': 'strategy_engine',
            'strategy-runtime': 'strategy_runtime', 'market-data-service': 'market_data_service',
            'research-service': 'research_service', 'journal-service': 'journal_service'}[service] + ':' + 'a'*40
    values['COMPOSE_PROJECT_NAME'] = 'bbb_stack'
    return values


class MainnetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='bbb-mainnet-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.main, self.demo = [Path(self.temp.name).resolve()/name for name in ('mainnet', 'demo')]
        for directory in ('abi/config', 'strategy-engine', 'strategy-runtime/config', 'strategy-runtime/specs',
                          'strategy-runtime/state', 'strategy-runtime/journal', 'journal'):
            (self.main/directory).mkdir(parents=True, exist_ok=True)
        for directory in ('abi', 'strategy-engine', 'strategy-runtime', 'journal', 'mds', 'market-data', 'research'):
            (self.demo/directory).mkdir(parents=True, exist_ok=True)
        (self.demo/'market-data/market.sqlite3').write_bytes(b'fixture history')
        (self.demo/'mds/markets.toml').write_text('fixture = true\n')
        self.env = environment(self.main, self.demo)

    def rendered(self):
        return json.loads(p.compose(self.env, 'config', '--format', 'json'))

    def test_final_compose_preserves_history_and_isolates_all_trading_mounts(self):
        config = self.rendered()
        p.check_mounts(config, self.main, self.demo)
        services = config['services']
        abi = services['abi']
        for key, value in {'BYBIT_ENV': 'mainnet', 'ABI_POSITION_SIZING_MODE': 'risk',
                           'ABI_BYBIT_LINEAR_POSITION_BINDING_MODE': 'hedge', 'ABI_EXPECTED_BYBIT_UID': '123',
                           'ABI_DRY_RUN': 'false', 'ABI_LIVE_TRADING_ENABLED': 'true'}.items():
            self.assertEqual(abi['environment'][key], value)
        self.assertNotIn('BYBIT_API_KEY', abi['environment'])
        self.assertNotIn('BYBIT_API_SECRET', abi['environment'])
        self.assertEqual(abi['mem_limit'], abi['memswap_limit'])
        self.assertIn(abi['ulimits']['core'], ({}, {'soft': 0, 'hard': 0}))
        self.assertIn('mode=0700', abi['tmpfs'][0])
        self.assertIn('/health/live', ' '.join(abi['healthcheck']['test']))
        self.assertEqual(services['strategy-runtime']['depends_on']['abi']['condition'], 'service_healthy')
        self.assertIn('strategy-runtime', services['market-data-service']['depends_on'])
        self.assertNotIn('depends_on', services['journal-service'])
        for service in services.values():
            for port in service.get('ports', []):
                self.assertEqual(port['host_ip'], '127.0.0.1')
        for service in ('market-data-service', 'research-service'):
            self.assertTrue(all(v['bind']['create_host_path'] is False for v in services[service]['volumes']))

    def test_missing_mainnet_uid_fails_compose_even_if_demo_uid_exists(self):
        del self.env['ABI_MAINNET_EXPECTED_BYBIT_UID']
        self.env['ABI_EXPECTED_BYBIT_UID'] = '999'
        with self.assertRaises(subprocess.CalledProcessError):
            self.rendered()

    def test_manifest_requires_six_sha_pins_and_rejects_inherited_fallback(self):
        manifest = Path(self.temp.name)/'images.env'
        manifest.write_text('\n'.join(key+'='+self.env[key] for key in p.SERVICES.values()))
        env, main, demo = p.configuration(self.env, manifest)
        self.assertEqual(main, self.main)
        manifest.write_text(manifest.read_text().replace(env['ABI_IMAGE'], ''))
        with self.assertRaises(ValueError):
            p.configuration(self.env, manifest)
        self.env['BBB_MAINNET_DATA_ROOT'] = str(self.demo)
        with self.assertRaises(ValueError):
            p.configuration(self.env, manifest)

    def test_first_launch_refuses_old_memory_and_enabled_or_unreadable_catalog(self):
        p.check_paths(self.main, self.demo, True)
        catalog = self.main/'strategy-runtime/specs/deployment.json'
        catalog.write_text('{"enabled": false}')
        p.check_paths(self.main, self.demo, True)
        catalog.write_text('{"enabled": true}')
        with self.assertRaises(ValueError):
            p.check_paths(self.main, self.demo, True)
        catalog.write_text('invalid')
        with self.assertRaises(ValueError):
            p.check_paths(self.main, self.demo, True)
        catalog.unlink()
        for name in ('strategy-runtime/state/runtime_state.jsonl', 'strategy-runtime/journal/runtime.jsonl',
                     'abi/abi_entry_package_correlation.jsonl', 'journal/journal.sqlite3'):
            file = self.main/name
            file.write_text('old memory')
            with self.assertRaises(ValueError):
                p.check_paths(self.main, self.demo, True)
            # Subsequent deployment must neither reset memory nor require strategies disabled.
            p.check_paths(self.main, self.demo, False)
            self.assertEqual(file.read_text(), 'old memory')
            file.unlink()

    def test_symlink_and_missing_history_fail_without_writes(self):
        path = self.main/'strategy-runtime/state'
        path.rmdir()
        path.symlink_to(self.demo/'strategy-runtime', target_is_directory=True)
        with self.assertRaises(ValueError):
            p.check_paths(self.main, self.demo, False)
        path.unlink()
        path.mkdir()
        (path/'runtime_state.jsonl').symlink_to(self.demo/'journal/journal.sqlite3')
        with self.assertRaises(ValueError):
            p.check_paths(self.main, self.demo, False)
        (path/'runtime_state.jsonl').unlink()
        (self.demo/'market-data/market.sqlite3').unlink()
        with self.assertRaises(ValueError):
            p.check_paths(self.main, self.demo, False)
        self.assertFalse((self.demo/'market-data/market.sqlite3').exists())

    def test_running_demo_and_other_writers_refused_but_own_mainnet_accepted(self):
        expected = p.check_mounts(self.rendered(), self.main, self.demo)
        def container(service, project, mounts, env):
            return {'State': {'Running': True}, 'Config': {'Labels': {'com.docker.compose.project': project,
                'com.docker.compose.service': service}, 'Env': env}, 'Mounts': [{'Type': 'bind',
                'Destination': dest, 'Source': str(source)} for dest, source in mounts.items()]}
        abi = container('abi', 'bbb_stack', expected['abi'], ['BYBIT_ENV=mainnet'])
        p.check_running([abi], expected, self.demo)
        abi['Config']['Env'] = ['BYBIT_ENV=demo']
        with self.assertRaises(ValueError):
            p.check_running([abi], expected, self.demo)
        other = container('mds', 'other', {'/data': self.demo/'market-data'}, [])
        with self.assertRaises(ValueError):
            p.check_running([other], expected, self.demo)
        other['State']['Running'] = False
        p.check_running([other], expected, self.demo)

    def test_post_deploy_rejects_authorized_abi_and_enabled_first_launch(self):
        env = dict(self.env, FIRST_LAUNCH='true')
        containers = [{'Config': {'Labels': {'com.docker.compose.service': service}, 'Image': env[key],
            'Env': ['BYBIT_ENV=mainnet']}, 'State': {'Health': {'Status': 'healthy'}}} for service, key in p.SERVICES.items()]
        authorization, enabled = 'LOCKED', False
        def response(path, port):
            if path == '/health/ready' and port == 8787:
                return {'authorization': authorization}
            if path == '/execution/mode':
                return {'bybitEnvironment': 'mainnet', 'canExecuteLive': False}
            if path == '/v1/strategy-instances':
                return {'invalid_files': [], 'duplicate_identities': [], 'scanned_file_count': 1,
                        'strategy_instances': [{'enabled': enabled}]}
            return {}
        with patch.object(verify, 'configuration', return_value=(env, self.main, self.demo)), \
             patch.object(verify, 'compose', return_value=b'fixture-container'), \
             patch.object(verify.subprocess, 'check_output', return_value=json.dumps(containers).encode()), \
             patch.object(verify, 'get', side_effect=response):
            verify.verify()
            # Same pins still require LOCKED after every recreate.
            authorization = 'AUTHORIZED'
            with self.assertRaises(ValueError):
                verify.verify()
            authorization, enabled = 'LOCKED', True
            with self.assertRaises(ValueError):
                verify.verify()
            env['FIRST_LAUNCH'] = 'false'
            verify.verify()

    def test_workflow_recreates_locked_without_credentials_or_enablement(self):
        text = (ROOT/'.github/workflows/deploy-mainnet.yml').read_text()
        self.assertIn('--force-recreate', text)
        self.assertIn('scripts/mainnet_preflight.py', text)
        self.assertIn('--network none --read-only', text)
        self.assertNotIn('authorize_abi', text)
        self.assertNotIn('deploy/images.env', text)
        self.assertNotIn('down -v', text)


if __name__ == '__main__':
    unittest.main()
