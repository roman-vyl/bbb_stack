#!/usr/bin/env python3
"""Read-only checks before Mainnet deployment. Never prepares or resets data."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SERVICES = {
    'abi': 'ABI_IMAGE', 'strategy-engine': 'STRATEGY_ENGINE_IMAGE',
    'strategy-runtime': 'STRATEGY_RUNTIME_IMAGE', 'market-data-service': 'MDS_IMAGE',
    'research-service': 'RESEARCH_IMAGE', 'journal-service': 'JOURNAL_IMAGE',
}
TRADING = ('abi', 'strategy-engine', 'strategy-runtime', 'journal')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def overlap(a, b):
    return a == b or a in b.parents or b in a.parents


def read_manifest(path):
    values = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        key, value = line.split('=', 1)
        require(key in SERVICES.values() and key not in values, 'Unexpected/duplicate image manifest key')
        require(re.fullmatch(r'ghcr\.io/roman-vyl/[a-z_]+:[0-9a-f]{40}', value), 'All Mainnet images require published full SHA pins')
        values[key] = value
    require(set(values) == set(SERVICES.values()), 'Missing image pins')
    return values


def configuration(environ, manifest):
    env = dict(environ)
    for key in ('BBB_MAINNET_DATA_ROOT', 'BBB_DEMO_DATA_ROOT', 'ABI_MAINNET_EXPECTED_BYBIT_UID'):
        require(env.get(key), 'Missing ' + key)
    require(re.fullmatch(r'[1-9][0-9]*', env['ABI_MAINNET_EXPECTED_BYBIT_UID']), 'Invalid Mainnet UID')
    main = Path(env['BBB_MAINNET_DATA_ROOT'])
    demo = Path(env['BBB_DEMO_DATA_ROOT'])
    require(main.is_absolute() and demo.is_absolute(), 'Data roots must be absolute')
    main, demo = main.resolve(strict=True), demo.resolve(strict=True)
    require(not overlap(main, demo), 'Mainnet and Demo roots must be separate')
    require(env.get('BBB_DATA_ROOT') == str(main), 'BBB_DATA_ROOT must equal canonical Mainnet root')
    require(env.get('COMPOSE_PROJECT_NAME', 'bbb_stack') == 'bbb_stack', 'Use the existing bbb_stack project')
    # Explicit manifest wins over inherited runner image variables; never load Demo manifest.
    env.update(read_manifest(manifest))
    env['COMPOSE_PROJECT_NAME'] = 'bbb_stack'
    return env, main, demo


def check_paths(main, demo, first_launch):
    directories = ['abi', 'abi/config', 'strategy-engine', 'strategy-runtime/config',
                   'strategy-runtime/specs', 'strategy-runtime/state', 'strategy-runtime/journal', 'journal']
    resolved = []
    demo_paths = [(demo / name).resolve() for name in TRADING]
    preserved = [(demo / name).resolve(strict=True) for name in ('mds', 'market-data', 'research')]
    for name in directories:
        path = main / name
        require(path.is_dir(), 'Prepare required Mainnet directory: ' + name)
        target = path.resolve(strict=True)
        require(main in target.parents, 'Mainnet directory escapes its root: ' + name)
        require(not any(overlap(target, old) for old in demo_paths + preserved), 'Trading path aliases Demo/history: ' + name)
        resolved.append(target)
    # Independent trading trees must not alias each other inside Mainnet either.
    trees = [(main / name).resolve(strict=True) for name in TRADING]
    require(all(not overlap(a, b) for n, a in enumerate(trees) for b in trees[n+1:]), 'Mainnet trading directories overlap')
    require(not any(overlap(p, old) for p in preserved for old in demo_paths + trees), 'History aliases trading memory')
    for tree in trees:
        require(not any(p.is_symlink() for p in tree.rglob('*')), 'Trading trees must not contain symlinks')
    for name in ('mds', 'market-data', 'research'):
        require((demo / name).is_dir(), 'Missing preserved ' + name)
    require((demo / 'market-data/market.sqlite3').is_file(), 'Missing preserved MDS database')
    require((demo / 'mds/markets.toml').is_file(), 'Missing preserved markets.toml')
    if first_launch:
        for name in ('strategy-runtime/state', 'strategy-runtime/journal', 'journal'):
            require(not any((main / name).iterdir()), 'First launch requires fresh ' + name)
        require(all(p.name == 'config' for p in (main / 'abi').iterdir()), 'First launch requires fresh ABI var')
        # Reject hidden/unsupported files, directories and symlinks, rather than silently skip them.
        for path in (main / 'strategy-runtime/specs').iterdir():
            require(path.is_file() and not path.is_symlink() and not path.name.startswith('.') and path.suffix == '.json', 'Unexpected catalog entry')
            document = json.loads(path.read_text())
            require(isinstance(document, dict) and document.get('enabled') is False, 'First launch requires every strategy disabled')


def compose(env, *args):
    return subprocess.check_output(['docker', 'compose', '-p', 'bbb_stack', '-f', 'docker-compose.yml',
        '-f', 'docker-compose.deploy.yml', '-f', 'docker-compose.mainnet.yml', '--env-file',
        'deploy/images.mainnet.env', *args], cwd=ROOT, env=env)


def check_mounts(config, main, demo):
    expected = {
        'abi': {'/app/var': main/'abi', '/app/config': main/'abi/config'},
        'strategy-engine': {'/app/config': main/'strategy-engine'},
        'strategy-runtime': {('/runtime/'+part): main/('strategy-runtime/'+part) for part in ('config', 'specs', 'state', 'journal')},
        'market-data-service': {'/app/config': demo/'mds', '/data': demo/'market-data'},
        'research-service': {'/data': demo/'research', '/runtime-specs': main/'strategy-runtime/specs'},
        'journal-service': {'/data': main/'journal', '/sources/runtime': main/'strategy-runtime/journal'},
    }
    require(set(config['services']) == set(SERVICES), 'Unexpected services')
    for service, mounts in expected.items():
        actual = {v['target']: Path(v['source']).resolve() for v in config['services'][service]['volumes'] if v['type'] == 'bind'}
        require(actual == {target: path.resolve() for target, path in mounts.items()}, 'Unexpected mounts: ' + service)
    return expected


def check_running(containers, expected, demo):
    protected = [path.resolve() for mounts in expected.values() for path in mounts.values()]
    protected += [(demo / name).resolve() for name in TRADING]
    for container in containers:
        if not container['State']['Running']:
            continue
        labels = container['Config'].get('Labels') or {}
        service = labels.get('com.docker.compose.service')
        own = labels.get('com.docker.compose.project') == 'bbb_stack'
        mounts = {v['Destination']: Path(v['Source']).resolve() for v in container.get('Mounts', []) if v['Type'] == 'bind'}
        if own:
            require(service in expected, 'Unexpected running project service')
            require(mounts == {dest: path.resolve() for dest, path in expected[service].items()}, 'Stop Demo/foreign data stack before Mainnet deploy')
            if service == 'abi':
                require('BYBIT_ENV=mainnet' in container['Config'].get('Env', []), 'Stop Demo ABI before Mainnet deploy')
        else:
            require(not any(overlap(path, p) for path in mounts.values() for p in protected), 'Another running container uses trading/history data')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first-launch', action='store_true')
    args = parser.parse_args()
    try:
        env, main_root, demo = configuration(os.environ, ROOT/'deploy/images.mainnet.env')
        check_paths(main_root, demo, args.first_launch)
        config = json.loads(compose(env, 'config', '--format', 'json'))
        expected = check_mounts(config, main_root, demo)
        ids = subprocess.check_output(['docker', 'ps', '-q']).decode().split()
        containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids])) if ids else []
        check_running(containers, expected, demo)
        print('Mainnet preflight passed; no data or containers changed.')
    except (ValueError, OSError, subprocess.SubprocessError):
        print('Mainnet preflight failed: verify pins, UID, isolated paths, catalog and stopped Demo. No deploy performed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
