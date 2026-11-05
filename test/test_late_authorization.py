import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("authorize_abi", ROOT / "scripts/authorize_abi.py")
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class IntegrationConfigurationTests(unittest.TestCase):
    def test_compose_preserves_one_abi_without_plaintext_credentials(self):
        env = dict(os.environ, ABI_EXPECTED_BYBIT_UID="123", BBB_DATA_ROOT="/tmp/bbb-auth-config-test")
        result = subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.demo.yml",
                                 "-f", "docker-compose.deploy.yml", "--env-file", "deploy/images.env", "config", "--format", "json"],
                                cwd=ROOT, env=env, check=True, capture_output=True)
        config = json.loads(result.stdout)
        abi = config["services"]["abi"]
        self.assertNotIn("env_file", abi)
        self.assertNotIn("BYBIT_API_KEY", abi["environment"])
        self.assertNotIn("BYBIT_API_SECRET", abi["environment"])
        self.assertEqual(abi["environment"]["ABI_POSITION_SIZING_MODE"], "risk")
        self.assertEqual(abi["environment"]["ABI_BYBIT_LINEAR_POSITION_BINDING_MODE"], "hedge")
        self.assertEqual(abi["mem_limit"], abi["memswap_limit"])
        self.assertIn("/run/abi-authorization", abi["tmpfs"][0])
        self.assertIn("/health/live", " ".join(abi["healthcheck"]["test"]))
        runtime = config["services"]["strategy-runtime"]
        self.assertEqual(runtime["environment"]["RUNTIME_ABI_BASE_URL"], "http://abi:8787")
        self.assertEqual(runtime["depends_on"]["abi"]["condition"], "service_healthy")
        self.assertEqual(len([name for name in config["services"] if name == "abi"]), 1)
        self.assertIn("/app/var", [volume["target"] for volume in abi["volumes"]])

    def test_deploy_workflow_remains_noninteractive(self):
        workflow = (ROOT / ".github/workflows/deploy-demo.yml").read_text()
        self.assertIn("up -d --no-build --remove-orphans", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s*(?:exec\s+)?age\s")
        self.assertNotIn("authorize_abi", workflow)
        self.assertIn("ABI_EXPECTED_BYBIT_UID", workflow)

    def test_operator_command_targets_existing_container_only(self):
        container = "a" * 64
        with patch("sys.argv", ["authorize_abi.py", "status", "--abi-repo", "/tmp/abi"]), patch.object(Path, "is_file", return_value=True), \
             patch.object(client.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, (container + "\n").encode())) as discover, \
             patch.object(client.subprocess, "call", return_value=0) as relay:
            self.assertEqual(client.main(), 0)
            self.assertEqual(discover.call_args.args[0][-3:], ["ps", "-q", "abi"])
            self.assertEqual(relay.call_args.args[0][-2:], [container, "status"])

    def test_operator_command_refuses_ambiguous_containers(self):
        with patch("sys.argv", ["authorize_abi.py", "status", "--abi-repo", "/tmp/abi"]), patch.object(Path, "is_file", return_value=True), \
             patch.object(client.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"aaaa\nbbbb\n")), \
             patch.object(client.subprocess, "call") as relay:
            self.assertEqual(client.main(), 1)
            relay.assert_not_called()


if __name__ == "__main__":
    unittest.main()
