#!/usr/bin/env python3
"""Read-only checks of the existing stack after Mainnet recreate."""
import json
import os
import subprocess
import time
import urllib.request
from mainnet_preflight import ROOT, SERVICES, compose, configuration, require


def get(path, port):
    with urllib.request.urlopen('http://127.0.0.1:%d%s' % (port, path), timeout=5) as response:
        return json.load(response)


def verify():
    env, _, _ = configuration(os.environ, ROOT/'deploy/images.mainnet.env')
    for attempt in range(30):
        ids = compose(env, 'ps', '-q').decode().split()
        containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids])) if ids else []
        by_service = {c['Config']['Labels']['com.docker.compose.service']: c for c in containers}
        if set(by_service) == set(SERVICES) and all(c['State'].get('Health', {}).get('Status') == 'healthy' for c in containers):
            break
        if attempt == 29:
            raise ValueError('Mainnet health timeout')
        time.sleep(5)
    for service, key in SERVICES.items():
        require(by_service[service]['Config']['Image'] == env[key], 'Image mismatch: ' + service)
    require('BYBIT_ENV=mainnet' in by_service['abi']['Config']['Env'], 'Wrong ABI environment')
    get('/health/live', 8787)
    # ABI readiness is 503 in LOCKED; still exposes authorization in its JSON body.
    import urllib.error
    try:
        health = get('/health/ready', 8787)
    except urllib.error.HTTPError as error:
        require(error.code == 503, 'Unexpected ABI readiness response')
        health = json.load(error)
    require(health['authorization'] == 'LOCKED', 'ABI did not stay LOCKED')
    mode = get('/execution/mode', 8787)
    require(mode['bybitEnvironment'] == 'mainnet' and mode['canExecuteLive'] is False, 'ABI execution gate unsafe')
    get('/health/live', 8093)
    get('/health/ready', 8093)
    if env.get('FIRST_LAUNCH') == 'true':
        catalog = get('/v1/strategy-instances', 8093)
        require(not catalog['invalid_files'] and not catalog['duplicate_identities'], 'Runtime rejected catalog')
        require(catalog['scanned_file_count'] == len(catalog['strategy_instances']), 'Runtime skipped catalog files')
        require(all(d['enabled'] is False for d in catalog['strategy_instances']), 'A strategy is enabled')
    print('Mainnet services healthy; six image refs verified; ABI LOCKED. No authorization performed.')


if __name__ == '__main__':
    try:
        verify()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError):
        raise SystemExit('Mainnet verification failed; do not authorize ABI. Inspect locally without logging credentials.')
