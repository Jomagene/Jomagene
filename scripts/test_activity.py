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

    def test_sparse_days_count_events_and_active_days(self):
        calendar = activity.ContributionCalendar.from_api(
            {
                (self.today - timedelta(days=4)).isoformat(): 1,
                (self.today - timedelta(days=3)).isoformat(): 10,
                (self.today - timedelta(days=1)).isoformat(): 3,
                self.today.isoformat(): 2,
            },
            self.today,
        )
        self.assertEqual(calendar.active_days, 4)
        self.assertEqual(calendar.total, 16)

    def test_empty_calendar_and_leap_day(self):
        calendar = activity.ContributionCalendar.from_api({}, date(2024, 3, 1))
        self.assertIn(date(2024, 2, 29), calendar.days)
        self.assertEqual((calendar.total, calendar.active_days), (0, 0))

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


def merged_request(iid=1, branch="master"):
    return {
        "iid": iid,
        "target_branch": branch,
        "state": "merged",
        "author": {"username": "Jomagene"},
    }


class TikiContributionTests(unittest.TestCase):
    def test_master_and_release_merges_are_separate(self):
        contributions = activity.TikiContributions.from_api(
            [
                merged_request(1),
                merged_request(2, "30.x"),
                merged_request(3, "27.x"),
            ]
        )
        self.assertEqual(contributions.master_merges, 1)
        self.assertEqual(contributions.release_merges, 2)
        self.assertEqual(contributions.total, 3)

    def test_pagination_overlap_does_not_inflate_counts(self):
        contributions = activity.TikiContributions.from_api(
            [merged_request(1), merged_request(1)]
        )
        self.assertEqual(contributions.total, 1)

    def test_invalid_or_unrelated_data_is_rejected(self):
        invalid = [
            {},
            [merged_request(True)],
            [merged_request(0)],
            [merged_request(1, "feature/demo")],
            [dict(merged_request(), state="opened")],
            [dict(merged_request(), author={"username": "other"})],
            [dict(merged_request(), author={"username": 42})],
            [merged_request(1), merged_request(1, "30.x")],
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                activity.TikiContributions.from_api(data)

    def test_release_classification_does_not_depend_on_title_tags(self):
        data = [dict(merged_request(1, "30.x"), title="Fix Calendar refresh")]
        self.assertEqual(activity.TikiContributions.from_api(data).release_merges, 1)

    def test_pagination_includes_more_than_one_hundred_merges(self):
        with patch.object(
            activity, "fetch_json", side_effect=[[{}] * 100, [{"iid": 101}]]
        ) as fetch:
            requests = activity.fetch_tiki_merges()
        self.assertEqual(len(requests), 101)
        self.assertIn("page=2", fetch.call_args_list[1].args[0])
        self.assertIn("state=merged", fetch.call_args_list[0].args[0])
        self.assertIn("tikiwiki%2Ftiki", fetch.call_args_list[0].args[0])


class FetchTests(unittest.TestCase):
    def test_public_requests_do_not_send_credentials(self):
        with patch.dict(os.environ, {"GH_TOKEN": "test-only"}):
            with patch.object(
                activity, "urlopen", return_value=BytesIO(b"{}")
            ) as fetch:
                activity.fetch_json("https://gitlab.com/example")
            self.assertFalse(fetch.call_args.args[0].has_header("Authorization"))

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
        "tiki-impact.svg",
        "gitlab-activity.svg",
        "tiki-impact-mobile.svg",
        "gitlab-activity-mobile.svg",
    )

    def test_successful_update_writes_both_platforms_and_layouts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            responses = [[], {}]
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
            responses = [[], URLError("offline")]
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
