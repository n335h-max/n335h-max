import unittest
import xml.etree.ElementTree as ET

from render_dashboard import build_snapshot, render_hero, render_languages, render_stats


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.user = {
            "login": "example",
            "public_repos": 4,
            "followers": 3,
            "created_at": "2025-04-22T07:30:56Z",
        }
        self.repos = [
            {"name": "app", "fork": False, "stargazers_count": 5},
            {"name": "bot", "fork": False, "stargazers_count": 2},
            {"name": "upstream", "fork": True, "stargazers_count": 99},
            {"name": "example", "fork": False, "stargazers_count": 0},
        ]
        self.languages = {
            "app": {"TypeScript": 70, "CSS": 30},
            "bot": {"Python": 50},
        }

    def test_snapshot_counts_owned_work_and_language_bytes(self):
        snapshot = build_snapshot(self.user, self.repos, self.languages)
        self.assertEqual(snapshot["public_repos"], 4)
        self.assertEqual(snapshot["stars"], 7)
        self.assertEqual(snapshot["followers"], 3)
        self.assertEqual(snapshot["joined"], "APR 2025")
        self.assertEqual(snapshot["languages"], [("TypeScript", 70), ("Python", 50), ("CSS", 30)])

    def test_theme_variants_are_valid_svg_with_actual_values(self):
        snapshot = build_snapshot(self.user, self.repos, self.languages)
        for theme in ("light", "dark"):
            for renderer in (render_hero, render_stats, render_languages):
                svg = renderer(snapshot, theme)
                self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIn("example", svg)
            self.assertIn("APR 2025", render_stats(snapshot, theme))
            self.assertIn("TypeScript", render_languages(snapshot, theme))

    def test_languages_card_handles_empty_data(self):
        snapshot = build_snapshot(self.user, self.repos, {})
        svg = render_languages(snapshot, "dark")
        self.assertIn("No language data yet", svg)
        ET.fromstring(svg)


if __name__ == "__main__":
    unittest.main()
