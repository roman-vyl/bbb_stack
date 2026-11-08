import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TelegramConfigurationTests(unittest.TestCase):
    def render(self, shared, trading):
        env = dict(os.environ, BBB_DATA_ROOT=str(shared),
                   BBB_TRADING_DATA_ROOT=str(trading), ABI_EXPECTED_BYBIT_UID="123")
        # A developer's shell must not influence the fixture's Telegram settings.
        for key in ("JOURNAL_TELEGRAM_BOT_TOKEN", "JOURNAL_TELEGRAM_CHAT_ID"):
            env.pop(key, None)
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.yml", "-f",
             "docker-compose.deploy.yml", "--env-file", "deploy/images.env",
             "config", "--format", "json"],
            cwd=ROOT, env=env, check=True, capture_output=True,
        )
        return json.loads(result.stdout)["services"]

    def test_optional_file_keeps_telegram_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            shared = Path(directory).resolve()
            config = self.render(shared, shared)
            journal = config["journal-service"]
            self.assertNotIn("JOURNAL_TELEGRAM_BOT_TOKEN", journal["environment"])
            self.assertNotIn("JOURNAL_TELEGRAM_CHAT_ID", journal["environment"])

    def test_secret_and_selected_specs_survive_repeated_compose_render(self):
        with tempfile.TemporaryDirectory() as directory:
            shared = Path(directory).resolve()
            (shared / "journal").mkdir()
            secret = shared / "journal/telegram.env"
            secret.write_text("JOURNAL_TELEGRAM_BOT_TOKEN=123:fixture-only\n"
                              "JOURNAL_TELEGRAM_CHAT_ID=456\n")
            before = secret.read_bytes()
            for trading in (shared, shared / "mainnet"):
                for _ in range(2):
                    services = self.render(shared, trading)
                    self.assertEqual(len(services), 6)
                    journal = services["journal-service"]
                    env = journal["environment"]
                    self.assertEqual(env["JOURNAL_TELEGRAM_BOT_TOKEN"], "123:fixture-only")
                    self.assertEqual(env["JOURNAL_TELEGRAM_CHAT_ID"], "456")
                    self.assertEqual(env["JOURNAL_TELEGRAM_SPECS_PATH"], "/sources/specs")
                    specs = next(v for v in journal["volumes"] if v["target"] == "/sources/specs")
                    self.assertEqual(Path(specs["source"]), trading / "strategy-runtime/specs")
                    self.assertTrue(specs["read_only"])
                    data = next(v for v in journal["volumes"] if v["target"] == "/data")
                    self.assertEqual(Path(data["source"]), trading / "journal")
                    self.assertFalse(data.get("read_only", False))
                    self.assertTrue(journal["image"].endswith(
                        ":364cbab80bffc36b9b6f7e03e491a7df8c26ba0a"))
                    self.assertFalse(journal.get("depends_on"))
                    for name, service in services.items():
                        if name != "journal-service":
                            self.assertNotIn("JOURNAL_TELEGRAM_BOT_TOKEN",
                                             service.get("environment", {}))
            self.assertEqual(before, secret.read_bytes())


if __name__ == "__main__":
    unittest.main()
