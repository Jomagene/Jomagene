# Profile maintenance

This is the source for the GitHub profile at `github.com/Jomagene`. The README
contains the profile text and links. Images are checked in, so visitors do not
depend on a third-party image service being available.

## Update the profile

Edit `README.md` for the short bio and links. Project notes and longer contribution
explanations stay in expandable sections so the main profile remains easy to scan.
Edit `scripts/build_artwork.py` for the header and project illustrations. The
`PROJECTS` records hold the card titles and technologies; each illustration has
its own function. Colours, typography and SVG helpers live in `profile_svg.py`.

The header, technology icons and activity cards use separate layouts below 600px.
The header and contact card use moving waves; a local SVG types the profile roles.
Skill icons and metric cards enter once; the GitLab grid reveals from left to right
without changing any values. These short entrances run when each image loads,
rather than being triggered by scrolling. All effects respect reduced-motion
settings; the typing line keeps a readable static role when motion is reduced.
Project cards are illustrations, not screenshots. Core languages and QA tools
also appear as README text, with project notes in expandable sections.

The profile describes PHP, JavaScript, Smarty, SQL, Tiki development and QA work.
The linked Tiki merge requests provide examples: language handling (!11282),
Calendar loading (!11098), recurrence (!11340), SQL queries (!11102) and changed-code
coverage (!11294). The HNG result, location and Tantor description come from the
existing profile. Genz.ad is identified as team work; its link points to the public
fork. GText AI is described as the web app in its public repository.

## Build and check

Python 3.11+ is sufficient. The scripts have no third-party runtime dependencies.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/build_artwork.py
python3 scripts/update_activity.py
```

The artwork build works offline. The activity update needs an internet connection.
If Ruff is installed, `ruff check scripts` and `ruff format --check scripts` use the
repository's configuration. The tests cover counting, date boundaries, leap days,
master/release classification, duplicate IDs, malformed data, pagination, retries and
preservation of existing output when a request fails.

## Automatic updates

The workflow tests the generator, rebuilds the artwork and refreshes both activity
cards daily at 06:17 UTC (08:17 in Lubumbashi). It also runs when the README or
scripts change. To run it manually, use **Actions → Update profile activity → Run
workflow** after pushing the files to the default branch.

No personal token is required. Public GitLab requests are anonymous. The workflow
uses GitHub's built-in token with `contents: write` only to check out and commit
the images. Repository policy must
allow Actions to write to the default branch. A rejected push does not overwrite
other commits.

GitHub can delay scheduled runs or disable them after 60 days without activity
in a public repository. The last generated images remain visible with their dates;
the workflow can be re-enabled in Actions.

## Activity data

- **Tiki:** all merged upstream requests authored by `Jomagene`, paginated through
  the canonical `tikiwiki/tiki` project's public API. Counts are split by target
  branch: `master`, or numbered release branches such as `30.x`. Release counts
  include backports and changes made directly on release branches, regardless of
  title tags. Duplicate MR IDs are counted once. These are merge-request counts,
  not a count of distinct fixes; backports do not inflate the master count.
- **SQL case:** a curated, reported benchmark from [Tiki MR !11133](https://gitlab.com/tikiwiki/tiki/-/merge_requests/11133).
  The local ranking test used 27,689 score records and 399 users, with the same
  results in 0.033–0.043 seconds after, versus 1.642–1.830 seconds before. The card
  shows 33–43 ms and links to the original conditions. It is a historical example,
  rather than a measurement performed by the daily workflow.
- **GitLab calendar:** publicly visible events over a 365-day UTC window and active
  days. Events include pushes, merge requests and comments; one push can contain
  several commits. Event totals provide context for the graph, not an impact score.

Tiki merge totals are all-time; the calendar has its own labelled 365-day window.
Requests with an unexpected author, state or target-branch format stop the update
instead of silently publishing misleading counts.

GitLab activity is a separate graph in the README. It does not change GitHub's
native contribution calendar. Missing days in a successful calendar response are
zero-filled. Failed or malformed responses stop the update before saving either
card; each individual output file is replaced atomically.

The GitLab calendar JSON is a public web endpoint, not a versioned REST API. Its
format may need attention if GitLab changes it.

## Image sources

Headers, contact and project illustrations are generated from the source in this
repository. `assets/vendor/stack.svg` comes from
[Skill Icons](https://github.com/tandpfun/skill-icons); its MIT licence is included
beside the image. The four social badges come from [Shields.io](https://shields.io).
These originals are not downloaded by the daily workflow. `skills.svg` and
`skills-mobile.svg` are generated from the licensed icon files with short, staggered
entrances. The vendor originals remain unchanged.

## References

- [GitHub contribution criteria](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
- [GitLab contribution calendar](https://docs.gitlab.com/user/profile/contributions_calendar/)
- [GitHub Actions authentication](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)
