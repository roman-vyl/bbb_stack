"""Run inside the pinned Runtime image, network disabled and catalog mounted read-only."""
import os
from pathlib import Path
from strategy_runtime.utility.deployment_catalog import FilesystemDeploymentCatalog

snapshot = FilesystemDeploymentCatalog(Path('/runtime/specs')).load_snapshot()
if snapshot.invalid_files or snapshot.duplicate_identities:
    raise SystemExit('Mainnet catalog has invalid or duplicate deployments')
if snapshot.scanned_file_count != len(snapshot.accepted_deployments):
    raise SystemExit('Mainnet catalog contains unaccepted files')
if os.environ.get('FIRST_LAUNCH') == 'true' and any(d.enabled for d in snapshot.accepted_deployments):
    raise SystemExit('First Mainnet launch requires every strategy disabled')
print('Pinned Runtime accepted the Mainnet catalog.')
