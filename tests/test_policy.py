import json
import re
import unittest
from pathlib import Path

POLICY = json.loads((Path(__file__).resolve().parents[1] / "config/server_policy.json").read_text())


class PolicyTests(unittest.TestCase):
    def test_channel_names_are_safe_and_unique(self):
        names = [item["name"] for item in POLICY["standard_text_channels"]]
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertRegex(name, re.compile(r"^[a-z0-9][a-z0-9_-]{0,90}$"))

    def test_topics_fit_discord_limit(self):
        for item in POLICY["standard_text_channels"]:
            self.assertLessEqual(len(item.get("topic", "")), 1024)


if __name__ == "__main__":
    unittest.main()
