# v2.1 Ready Friday + Audit

Updates:

- Ready for Release now defaults to the last Friday inside Print & Ship.
- With the default 4-week Print & Ship duration, that is the 4th Friday.
- If Print & Ship changes to 3 weeks, 5 weeks, or another duration, Ready for Release becomes the final Friday inside that period.
- Ready for Release can still be manually overridden or used as an anchor.
- Updated the workbook formula source so Excel exports continue to recalculate the Ready date when Print & Ship duration changes inside Excel.
- Updated the Assistant prompt so users know Ready for Release is optional unless they want an override.
- Removed unused scenario/reasoning code paths from the front-end after those panels were removed from the UI.
- Updated static asset cache headers and service-worker cache name so Render/iPhone/iPad test deployments pick up new builds more reliably.
- Preserved Monday handoff behavior, Hiatus overlay behavior, Day Inspector manual overrides, dark mode, Excel/PDF export, email link workflow, and source holiday logic.
