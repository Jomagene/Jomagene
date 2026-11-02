#!/usr/bin/env python3
"""Fetch public activity and render repository-hosted profile cards."""

import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree.ElementTree import SubElement

from profile_svg import BORDER, CYAN, MUTED, PANEL, PINK, WHITE, WIDTH, Svg

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "Jomagene"
WINDOW_DAYS = 365
HEATMAP_COLORS = ("#292342", "#53335d", "#87447c", "#bd5b9b", PINK)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def nonnegative_count(value: object) -> int:
    """Reject malformed API counts, including booleans masquerading as integers."""
    if type(value) is not int or value < 0:
        raise ValueError("Expected a non-negative integer count")
    return value


@dataclass(frozen=True)
class TikiContributions:
    master_merges: int
    release_merges: int

    @property
    def total(self) -> int:
        return self.master_merges + self.release_merges

    @classmethod
    def from_api(cls, data: object) -> "TikiContributions":
        """Count merge requests, not unique fixes; keep release work separate."""
        if not isinstance(data, list):
            raise ValueError("Expected a Tiki merge-request list")
        branches = {}
        for item in data:
            if not isinstance(item, dict) or item.get("state") != "merged":
                raise ValueError("Expected merged upstream requests")
            author = item.get("author")
            username = author.get("username") if isinstance(author, dict) else None
            if not isinstance(username, str) or username.lower() != USERNAME.lower():
                raise ValueError("Unexpected merge-request author")
            iid = nonnegative_count(item.get("iid"))
            branch = item.get("target_branch")
            if (
                iid == 0
                or not isinstance(branch, str)
                or not (branch == "master" or re.fullmatch(r"\d+\.x", branch))
            ):
                raise ValueError("Expected master or a numbered Tiki release branch")
            if iid in branches and branches[iid] != branch:
                raise ValueError("Conflicting merge-request pagination data")
            branches[iid] = branch
        master = sum(branch == "master" for branch in branches.values())
        return cls(master_merges=master, release_merges=len(branches) - master)


@dataclass(frozen=True)
class ContributionCalendar:
    """A complete, chronological UTC window; missing public days count as zero."""

    days: tuple[date, ...]
    counts: tuple[int, ...]

    @classmethod
    def from_api(cls, data: object, today: date) -> "ContributionCalendar":
        if not isinstance(data, dict):
            raise ValueError("Expected a GitLab calendar object")
        for day, count in data.items():
            if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
                raise ValueError("Expected ISO calendar dates")
            nonnegative_count(count)
        days = tuple(
            today - timedelta(days=WINDOW_DAYS - 1 - index)
            for index in range(WINDOW_DAYS)
        )
        return cls(
            days=days, counts=tuple(data.get(day.isoformat(), 0) for day in days)
        )

    @property
    def total(self) -> int:
        return sum(self.counts)

    @property
    def active_days(self) -> int:
        return sum(count > 0 for count in self.counts)


def fetch_json(url: str) -> Any:
    """Read public GitLab data anonymously and retry transient failures."""
    headers = {"User-Agent": "Jomagene-profile-activity", "Accept": "application/json"}
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            permanent = (
                isinstance(error, HTTPError) and error.code not in RETRYABLE_STATUS
            )
            if permanent or attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Unreachable retry state")


def fetch_tiki_merges() -> list[dict[str, Any]]:
    requests = []
    page = 1
    while True:
        url = (
            "https://gitlab.com/api/v4/projects/tikiwiki%2Ftiki/merge_requests"
            f"?author_username={USERNAME}&state=merged&scope=all&per_page=100&page={page}"
        )
        batch = fetch_json(url)
        if not isinstance(batch, list):
            raise ValueError("Expected a Tiki merge-request list")
        requests.extend(batch)
        if len(batch) < 100:
            return requests
        page += 1


def metric(
    canvas: Svg,
    x: int,
    value: int | str,
    label: str,
    accent: str = PINK,
    note: str = "",
    width: int = 362,
    delay: float = 0,
    value_size: int | None = None,
) -> None:
    first = len(canvas.root)
    canvas.rect(x, 68, width, 111, PANEL, radius=12, stroke=BORDER)
    canvas.text(
        x + 22,
        113,
        f"{value:,}" if isinstance(value, int) else value,
        value_size or (30 if width < 200 else 36),
        accent,
        700,
        letter_spacing=-1,
    )
    canvas.text(x + 22, 142, label, 12 if width < 200 else 15, WHITE, 500)
    if note:
        canvas.text(x + 22, 164, note, 9 if width < 200 else 11, MUTED)

    canvas.entrance(list(canvas.root)[first:], delay=delay)


def render_impact(
    contributions: TikiContributions, today: date, compact: bool = False
) -> Svg:
    """Show accepted work and one reported benchmark, with its original conditions."""
    canvas = Svg(
        480 if compact else WIDTH,
        262,
        "Tiki contributions and a documented SQL benchmark",
        f"All-time upstream Tiki merge requests: {contributions.master_merges} into master, "
        f"{contributions.release_merges} into release branches; {contributions.total} total. "
        "These are MR counts, not distinct fixes. Reported local ranking benchmark in "
        "Tiki MR !11133: 1.642–1.830 seconds before, 0.033–0.043 seconds after, "
        f"27,689 score records and 399 users. Counts updated {today} UTC.",
    )
    canvas.label(16 if compact else 32, 37, "TIKI / ACCEPTED CONTRIBUTIONS", CYAN)
    xs = (16, 174, 332) if compact else (32, 419, 806)
    width = 132 if compact else 362
    metric(
        canvas,
        xs[0],
        contributions.master_merges,
        "Master MRs" if compact else "Merged into master",
        CYAN,
        width=width,
    )
    metric(
        canvas,
        xs[1],
        contributions.release_merges,
        "Release MRs" if compact else "Merged into release branches",
        PINK,
        width=width,
        delay=0.08,
    )
    metric(
        canvas,
        xs[2],
        "33–43 ms",
        "SQL query" if compact else "SQL ranking query",
        WHITE,
        "was 1.64–1.83s" if compact else "Before: 1.642–1.830s · Local benchmark",
        width=width,
        delay=0.16,
        value_size=21 if compact else 34,
    )
    if compact:
        canvas.text(
            16,
            207,
            f"{contributions.total} merged MRs · All-time · Updated {today}",
            10,
            MUTED,
        )
        canvas.text(16, 231, "SQL case: 27,689 score records / 399 users", 10, MUTED)
        canvas.text(16, 249, "Reported benchmark · Source: Tiki MR !11133", 10, MUTED)
    else:
        canvas.text(
            32,
            210,
            f"{contributions.total} merged MRs · All-time · Master/release counted separately",
            12,
            MUTED,
        )
        canvas.text(
            1166, 210, f"UPDATED {today} UTC", 12, MUTED, mono=True, text_anchor="end"
        )
        canvas.text(
            32,
            242,
            "SQL case: 27,689 score records / 399 users · Reported benchmark in Tiki MR !11133",
            12,
            MUTED,
        )
    return canvas


def render_gitlab(calendar: ContributionCalendar, compact: bool = False) -> Svg:
    start, end = calendar.days[0], calendar.days[-1]
    canvas = Svg(
        480 if compact else WIDTH,
        310 if compact else 308,
        "GitLab contribution calendar",
        f"{calendar.total} contribution events over {WINDOW_DAYS} days; {calendar.active_days} active days; "
        f"{start} through {end}. "
        "Counts reflect the publicly visible GitLab calendar, including pushes, merge requests and comments.",
    )
    left = 16 if compact else 32
    canvas.label(left, 32, "GITLAB / ACTIVITY")
    canvas.text(left, 74, f"{calendar.active_days} active days", 28, CYAN, 700)
    canvas.text(
        left,
        100,
        f"{calendar.total:,} contribution events · Past {WINDOW_DAYS} days",
        13,
        MUTED,
    )
    reveal = canvas.horizontal_reveal(
        38 if compact else 85,
        132,
        424 if compact else 1060,
        98 if compact else 126,
    )
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    previous_month = None
    for day, count in zip(calendar.days, calendar.counts, strict=True):
        offset = (day - grid_start).days
        column_step, row_step = (8, 14) if compact else (20, 18)
        x = (38 if compact else 85) + (offset // 7) * column_step
        y = 132 + (offset % 7) * row_step
        if day.month != previous_month:
            canvas.text(
                x, 120, day.strftime("%b"), 8 if compact else 11, MUTED, mono=True
            )
            previous_month = day.month
        level = sum(count >= threshold for threshold in (1, 6, 11, 21))
        cell = canvas.rect(
            x,
            y,
            6 if compact else 15,
            10 if compact else 13,
            HEATMAP_COLORS[level],
            radius=2 if compact else 3,
        )
        cell.set("clip-path", reveal)
        # A native tooltip preserves per-day detail without scripts or foreignObject.
        SubElement(cell, "title").text = f"{day}: {count} contribution events"
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        canvas.text(
            8 if compact else 32,
            143 + row * (14 if compact else 18),
            name,
            8 if compact else 11,
            MUTED,
            mono=True,
        )
    if compact:
        canvas.line(16, 246, 464, 246)
        canvas.text(16, 268, f"{start} → {end}", 10, MUTED)
        canvas.text(16, 294, "Public calendar · UTC", 10, MUTED)
    else:
        canvas.line(32, 266, 1168, 266)
        canvas.text(
            32, 291, f"{start} → {end} · Public calendar · UTC", 12, MUTED, mono=True
        )
    for index, label in enumerate(("0", "1–5", "6–10", "11–20", "21+")):
        x = (215 + index * 49) if compact else (776 + index * 77)
        canvas.rect(
            x,
            259 if compact else 281,
            9 if compact else 12,
            9 if compact else 12,
            HEATMAP_COLORS[index],
            radius=2,
        )
        canvas.text(
            x + (12 if compact else 18),
            267 if compact else 292,
            label,
            8 if compact else 10,
            MUTED,
            mono=True,
        )
    return canvas


def main() -> None:
    today = datetime.now(UTC).date()
    contributions = TikiContributions.from_api(fetch_tiki_merges())
    calendar = ContributionCalendar.from_api(
        fetch_json(f"https://gitlab.com/users/{USERNAME}/calendar.json"),
        today,
    )
    # Complete all network requests and rendering before replacing the last good cards.
    cards = {
        "tiki-impact.svg": render_impact(contributions, today),
        "gitlab-activity.svg": render_gitlab(calendar),
        "tiki-impact-mobile.svg": render_impact(contributions, today, compact=True),
        "gitlab-activity-mobile.svg": render_gitlab(calendar, compact=True),
    }
    for filename, canvas in cards.items():
        canvas.save(ROOT / "assets" / filename)
    print(f"Updated Tiki contribution and GitLab activity cards for {today}")


if __name__ == "__main__":
    main()
