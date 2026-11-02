#!/usr/bin/env python3
"""Fetch public activity and render repository-hosted profile cards."""

import json
import os
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
class GitHubStats:
    public_repositories: int
    stars: int
    followers: int

    @classmethod
    def from_api(
        cls, user: object, repositories: list[dict[str, Any]]
    ) -> "GitHubStats":
        if not isinstance(user, dict):
            raise ValueError("Expected a GitHub profile object")
        public_repositories = nonnegative_count(user.get("public_repos"))
        followers = nonnegative_count(user.get("followers"))
        stars = 0
        for repository in repositories:
            if (
                not isinstance(repository, dict)
                or type(repository.get("fork")) is not bool
            ):
                raise ValueError("Expected repository metadata and a boolean fork flag")
            count = nonnegative_count(repository.get("stargazers_count"))
            if not repository["fork"]:
                stars += count
        return cls(
            public_repositories=public_repositories, stars=stars, followers=followers
        )


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

    @property
    def longest_streak(self) -> int:
        longest = current = 0
        for count in self.counts:
            current = current + 1 if count else 0
            longest = max(longest, current)
        return longest


def fetch_json(url: str) -> Any:
    """Retry transient failures; send the optional GitHub token only to GitHub."""
    headers = {"User-Agent": "Jomagene-profile-activity", "Accept": "application/json"}
    token = os.environ.get("GH_TOKEN")
    if url.startswith("https://api.github.com/") and token:
        headers["Authorization"] = f"Bearer {token}"
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


def fetch_repositories() -> list[dict[str, Any]]:
    repositories = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page={page}"
        batch = fetch_json(url)
        if not isinstance(batch, list):
            raise ValueError("Expected a GitHub repository list")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def metric(
    canvas: Svg,
    x: int,
    value: int,
    label: str,
    accent: str = PINK,
    note: str = "",
    width: int = 362,
    delay: float = 0,
) -> None:
    first = len(canvas.root)
    canvas.rect(x, 68, width, 111, PANEL, radius=12, stroke=BORDER)
    canvas.text(
        x + 22,
        113,
        f"{value:,}",
        30 if width < 200 else 36,
        accent,
        700,
        letter_spacing=-1,
    )
    canvas.text(x + 22, 142, label, 12 if width < 200 else 15, WHITE, 500)
    if note:
        canvas.text(x + 22, 164, note, 11, MUTED)

    canvas.entrance(list(canvas.root)[first:], delay=delay)


def render_github(stats: GitHubStats, today: date, compact: bool = False) -> Svg:
    width = 480 if compact else WIDTH
    canvas = Svg(
        width,
        231,
        "GitHub public profile statistics",
        f"{stats.public_repositories} public repositories, {stats.stars} stars on owned non-fork "
        f"public repositories, {stats.followers} followers. Updated {today} UTC.",
    )
    if compact:
        canvas.label(16, 37, "GITHUB / PUBLIC ACTIVITY", CYAN)
        metric(canvas, 16, stats.public_repositories, "Public repos", CYAN, width=132)
        metric(canvas, 174, stats.stars, "Stars earned", PINK, width=132, delay=0.08)
        metric(canvas, 332, stats.followers, "Followers", WHITE, width=132, delay=0.16)
        canvas.text(16, 210, "Stars exclude forks · Public data", 10, MUTED)
        canvas.text(464, 210, f"{today} UTC", 10, MUTED, text_anchor="end")
        return canvas
    canvas.label(32, 37, "GITHUB / PUBLIC ACTIVITY", CYAN)
    canvas.text(1166, 37, f"@{USERNAME}", 13, MUTED, mono=True, text_anchor="end")
    metric(canvas, 32, stats.public_repositories, "Public repositories", CYAN)
    metric(
        canvas,
        419,
        stats.stars,
        "Stars earned",
        PINK,
        "On owned, non-fork public repositories",
        delay=0.08,
    )
    metric(canvas, 806, stats.followers, "Followers", WHITE, delay=0.16)
    canvas.text(32, 210, "Public API data · Rebuilt daily", 12, MUTED, mono=True)
    canvas.text(
        1166, 210, f"UPDATED {today} UTC", 12, MUTED, mono=True, text_anchor="end"
    )
    return canvas


def render_gitlab(calendar: ContributionCalendar, compact: bool = False) -> Svg:
    start, end = calendar.days[0], calendar.days[-1]
    canvas = Svg(
        480 if compact else WIDTH,
        385 if compact else 403,
        "GitLab contribution calendar",
        f"{calendar.total} contribution events over {WINDOW_DAYS} days; {calendar.active_days} active days; "
        f"longest streak {calendar.longest_streak} days. {start} through {end}. "
        "Counts reflect the publicly visible GitLab calendar, including pushes, merge requests and comments.",
    )
    if compact:
        canvas.label(16, 37, "GITLAB / CONTRIBUTIONS")
        metric(canvas, 16, calendar.total, "Events", width=132)
        metric(
            canvas,
            174,
            calendar.active_days,
            "Active days",
            CYAN,
            width=132,
            delay=0.08,
        )
        metric(
            canvas,
            332,
            calendar.longest_streak,
            "Best streak",
            WHITE,
            width=132,
            delay=0.16,
        )
    else:
        canvas.label(32, 37, "GITLAB / CONTRIBUTIONS")
        canvas.text(
            1166,
            37,
            f"@{USERNAME} · {WINDOW_DAYS} DAYS",
            13,
            MUTED,
            mono=True,
            text_anchor="end",
        )
        metric(canvas, 32, calendar.total, "Contribution events")
        metric(canvas, 419, calendar.active_days, "Active days", CYAN, delay=0.08)
        metric(
            canvas,
            806,
            calendar.longest_streak,
            "Longest streak · days",
            WHITE,
            "Within the displayed window",
            delay=0.16,
        )
    reveal = canvas.horizontal_reveal(
        38 if compact else 85,
        218,
        424 if compact else 1060,
        98 if compact else 126,
    )
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    previous_month = None
    for day, count in zip(calendar.days, calendar.counts, strict=True):
        offset = (day - grid_start).days
        column_step, row_step = (8, 14) if compact else (20, 18)
        x = (38 if compact else 85) + (offset // 7) * column_step
        y = 218 + (offset % 7) * row_step
        if day.month != previous_month:
            canvas.text(
                x, 206, day.strftime("%b"), 8 if compact else 11, MUTED, mono=True
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
            229 + row * (14 if compact else 18),
            name,
            8 if compact else 11,
            MUTED,
            mono=True,
        )
    if compact:
        canvas.line(16, 333, 464, 333)
        canvas.text(16, 354, f"{start} → {end}", 10, MUTED)
        canvas.text(16, 374, "Streak in days · Public calendar · UTC", 10, MUTED)
    else:
        canvas.line(32, 348, 1168, 348)
        canvas.text(
            32, 373, f"{start} → {end} · Public calendar · UTC", 12, MUTED, mono=True
        )
    for index, label in enumerate(("0", "1–5", "6–10", "11–20", "21+")):
        x = (215 + index * 49) if compact else (776 + index * 77)
        canvas.rect(
            x,
            345 if compact else 363,
            9 if compact else 12,
            9 if compact else 12,
            HEATMAP_COLORS[index],
            radius=2,
        )
        canvas.text(
            x + (12 if compact else 18),
            353 if compact else 374,
            label,
            8 if compact else 10,
            MUTED,
            mono=True,
        )
    return canvas


def main() -> None:
    today = datetime.now(UTC).date()
    user = fetch_json(f"https://api.github.com/users/{USERNAME}")
    stats = GitHubStats.from_api(user, fetch_repositories())
    calendar = ContributionCalendar.from_api(
        fetch_json(f"https://gitlab.com/users/{USERNAME}/calendar.json"),
        today,
    )
    # Complete all network requests and rendering before replacing the last good cards.
    cards = {
        "github-stats.svg": render_github(stats, today),
        "gitlab-activity.svg": render_gitlab(calendar),
        "github-stats-mobile.svg": render_github(stats, today, compact=True),
        "gitlab-activity-mobile.svg": render_gitlab(calendar, compact=True),
    }
    for filename, canvas in cards.items():
        canvas.save(ROOT / "assets" / filename)
    print(f"Updated GitHub and GitLab cards for {today}")


if __name__ == "__main__":
    main()
