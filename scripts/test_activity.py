"""Tests for data accuracy, API boundaries and preservation of published cards."""

import os
import unittest
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET

import update_activity as activity
from profile_svg import Svg


class CalendarTests(unittest.TestCase):
    today = date(2026, 11, 2)

    def test_window_excludes_old_and_future_events(self):
        start = self.today - timedelta(days=364)
        calendar = activity.ContributionCalendar.from_api(
            {
                (start - timedelta(days=1)).isoformat(): 100,
                start.isoformat(): 2,
                self.today.isoformat(): 3,
                (self.today + timedelta(days=1)).isoformat(): 100,
            },
            self.today,
        )
        self.assertEqual(len(calendar.days), 365)
        self.assertEqual(calendar.days[0], start)
        self.assertEqual(calendar.days[-1], self.today)
        self.assertEqual(calendar.total, 5)
        self.assertEqual(calendar.active_days, 2)

    def test_missing_days_break_a_streak(self):
        calendar = activity.ContributionCalendar.from_api(
            {
                (self.today - timedelta(days=4)).isoformat(): 1,
                (self.today - timedelta(days=3)).isoformat(): 10,
                (self.today - timedelta(days=1)).isoformat(): 3,
                self.today.isoformat(): 2,
            },
            self.today,
        )
        self.assertEqual(calendar.longest_streak, 2)
        self.assertEqual(calendar.active_days, 4)
        self.assertEqual(calendar.total, 16)

    def test_empty_calendar_and_leap_day(self):
        calendar = activity.ContributionCalendar.from_api({}, date(2024, 3, 1))
        self.assertIn(date(2024, 2, 29), calendar.days)
        self.assertEqual(
            (calendar.total, calendar.active_days, calendar.longest_streak), (0, 0, 0)
        )

    def test_invalid_data_is_not_reported_as_zero(self):
        invalid = [
            [],
            {"bad date": 1},
            {"2026-11-02": -1},
            {"2026-11-02": True},
            {"2026-11-02": "2"},
            {42: 1},
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                activity.ContributionCalendar.from_api(data, self.today)


class GitHubTests(unittest.TestCase):
    def test_malformed_profile_and_repository_counts_are_rejected(self):
        cases = [
            ([], []),
            ({"public_repos": True, "followers": 0}, []),
            ({"public_repos": 0, "followers": -1}, []),
            (
                {"public_repos": 1, "followers": 0},
                [{"fork": False, "stargazers_count": "10"}],
            ),
            ({"public_repos": 1, "followers": 0}, [{"stargazers_count": 10}]),
        ]
        for user, repositories in cases:
            with (
                self.subTest(user=user, repositories=repositories),
                self.assertRaises(ValueError),
            ):
                activity.GitHubStats.from_api(user, repositories)

    def test_fork_stars_are_excluded(self):
        stats = activity.GitHubStats.from_api(
            {"public_repos": 2, "followers": 3},
            [
                {"fork": False, "stargazers_count": 7},
                {"fork": True, "stargazers_count": 100},
            ],
        )
        self.assertEqual(stats, activity.GitHubStats(2, 7, 3))

    def test_pagination_includes_repositories_after_first_page(self):
        with patch.object(
            activity, "fetch_json", side_effect=[[{}] * 100, [{"name": "last"}]]
        ) as fetch:
            repositories = activity.fetch_repositories()
        self.assertEqual(len(repositories), 101)
        self.assertEqual(repositories[-1]["name"], "last")
        self.assertIn("page=2", fetch.call_args_list[1].args[0])


class FetchTests(unittest.TestCase):
    def test_token_is_sent_only_to_github(self):
        for host in ("api.github.com", "gitlab.com"):
            with (
                self.subTest(host=host),
                patch.dict(os.environ, {"GH_TOKEN": "test-only"}),
            ):
                with patch.object(
                    activity, "urlopen", return_value=BytesIO(b"{}")
                ) as fetch:
                    activity.fetch_json(f"https://{host}/example")
                request = fetch.call_args.args[0]
                self.assertEqual(
                    request.has_header("Authorization"), host == "api.github.com"
                )

    def test_transient_failure_is_retried(self):
        with patch.object(
            activity,
            "urlopen",
            side_effect=[URLError("offline"), BytesIO(b'{"ok": true}')],
        ):
            with patch.object(activity.time, "sleep") as sleep:
                self.assertEqual(
                    activity.fetch_json("https://gitlab.com/example"), {"ok": True}
                )
                sleep.assert_called_once_with(1)

    def test_permanent_http_failure_is_not_retried(self):
        error = HTTPError("https://gitlab.com/example", 404, "Not found", {}, None)
        with patch.object(activity, "urlopen", side_effect=error) as fetch:
            with self.assertRaises(HTTPError):
                activity.fetch_json("https://gitlab.com/example")
        self.assertEqual(fetch.call_count, 1)
        error.close()


class OutputTests(unittest.TestCase):
    filenames = (
        "github-stats.svg",
        "gitlab-activity.svg",
        "github-stats-mobile.svg",
        "gitlab-activity-mobile.svg",
    )

    def test_successful_update_writes_both_platforms_and_layouts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            responses = [{"public_repos": 1, "followers": 2}, [], {}]
            with (
                patch.object(activity, "ROOT", root),
                patch.object(activity, "fetch_json", side_effect=responses),
            ):
                activity.main()
            self.assertEqual(
                {p.name for p in (root / "assets").iterdir()}, set(self.filenames)
            )
            for filename in self.filenames:
                document = ET.parse(root / "assets" / filename).getroot()
                expected_width = "480" if "mobile" in filename else "1200"
                self.assertEqual(document.attrib["width"], expected_width)

    def test_calendar_layouts_keep_all_days_and_counts(self):
        today = date(2026, 11, 2)
        calendar = activity.ContributionCalendar.from_api({today.isoformat(): 5}, today)
        for compact in (False, True):
            with self.subTest(compact=compact):
                canvas = activity.render_gitlab(calendar, compact=compact)
                tooltips = [node.text for node in canvas.root.findall("rect/title")]
                self.assertEqual(len(tooltips), 365)
                self.assertEqual(tooltips[-1], "2026-11-02: 5 contribution events")

    def test_network_failure_preserves_existing_cards(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            for filename in self.filenames:
                (root / "assets" / filename).write_text("last good version")
            responses = [{"public_repos": 0, "followers": 0}, [], URLError("offline")]
            with (
                patch.object(activity, "ROOT", root),
                patch.object(activity, "fetch_json", side_effect=responses),
            ):
                with self.assertRaises(URLError):
                    activity.main()
            for filename in self.filenames:
                self.assertEqual(
                    (root / "assets" / filename).read_text(), "last good version"
                )

    def test_svg_text_is_escaped_and_accessible(self):
        canvas = Svg(200, 100, '<script> & "title"')
        canvas.text(20, 40, "<script>alert('example')</script>")
        document = ET.fromstring(ET.tostring(canvas.root))
        namespace = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(document.attrib["role"], "img")
        self.assertEqual(document.find("s:title", namespace).text, '<script> & "title"')
        self.assertEqual(document.findall(".//s:script", namespace), [])


if __name__ == "__main__":
    unittest.main()
