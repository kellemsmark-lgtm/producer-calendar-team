# v1.5 Monday Handoff Notes

This test build updates the scenario engine to match the production-planning rule requested during assistant testing:

> When one production period ends, the next period begins the following Monday by default.

Behavior:

- Week-based phases remain Monday-Friday workweeks.
- Production still counts shoot days only and excludes weekends plus selected-location holidays.
- Forward handoffs use the Monday after the completed phase, even if the phase ends mid-week.
- If a fixed Hiatus starts later than the default handoff, the next phase begins on the default Monday and Hiatus is shown as an overlay/interruption. This prevents hidden gaps.
- If Hiatus begins exactly at the default handoff, the following phase begins on the Monday after Hiatus ends.
- If Hiatus is the selected scheduling anchor, the Hiatus range continues to drive the surrounding schedule.

Example:

- Production ends Thursday 12/03/26.
- The default Post Production start becomes Monday 12/07/26.
