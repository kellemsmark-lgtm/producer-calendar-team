# v1.7 Force Default Durations

This update fixes a persisted-browser-state issue during Assistant intake. Older saved states could carry `post.weeks = 0`, which suppressed the Post Production phase even though the default is 26 weeks.

Rules enforced:

- Pre-Production defaults to 12 weeks when blank or zero.
- Post Production defaults to 26 weeks when blank or zero.
- Print & Ship defaults to 4 weeks when blank or zero.
- R&D and Travel/Prep may remain 0.
- After a period ends, the next period begins the following Monday by default.
- A later fixed Hiatus is shown as an overlay/interruption unless Hiatus is selected as the anchor.
