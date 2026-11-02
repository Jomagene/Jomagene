# Profile maintenance

This is the source for the GitHub profile at `github.com/Jomagene`. The README
contains the profile text and links. Images are checked in, so visitors do not
depend on a third-party image service being available.

## Update the profile

Edit `README.md` for the bio, skills, contribution links and project descriptions.
Edit `scripts/build_artwork.py` for the header and project illustrations. The
`PROJECTS` records hold the card titles and technologies; each illustration has
its own function. Colours, typography and SVG helpers live in `profile_svg.py`.

The header, technology icons and activity cards use separate layouts below 600px.
Decorative motion
in the desktop header respects reduced-motion settings. Project cards are
illustrations, not screenshots. Skills and project descriptions are also written
as regular README text, so they remain readable on narrow screens.

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
streaks, malformed data, fork exclusions, pagination, retries, token handling and
preservation of existing output when a request fails.

## Automatic updates

The workflow tests the generator, rebuilds the artwork and refreshes both activity
cards daily at 06:17 UTC (08:17 in Lubumbashi). It also runs when the README or
scripts change. To run it manually, use **Actions → Update profile activity → Run
workflow** after pushing the files to the default branch.

No personal token is required. The workflow uses GitHub's built-in token, with
`contents: write`, to commit the images. The optional local `GH_TOKEN` is sent
only to `api.github.com`; GitLab requests are anonymous. Repository policy must
allow Actions to write to the default branch. A rejected push does not overwrite
other commits.

GitHub can delay scheduled runs or disable them after 60 days without activity
in a public repository. The last generated images remain visible with their dates;
the workflow can be re-enabled in Actions.

## Activity data

- **GitHub:** public repository count, stars on owned non-fork public repositories,
  and followers. These are not commit counts.
- **GitLab:** publicly visible calendar events over a 365-day UTC window, active
  days and the longest streak within that window. Events include pushes, merge
  requests and comments; one push can contain several commits.

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
These are static local files and are not downloaded by the daily workflow.

## References

- [GitHub contribution criteria](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
- [GitLab contribution calendar](https://docs.gitlab.com/user/profile/contributions_calendar/)
- [GitHub Actions authentication](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)
