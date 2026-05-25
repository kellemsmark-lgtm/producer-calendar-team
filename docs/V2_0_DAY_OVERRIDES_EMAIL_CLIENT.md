# v2.0 Day Overrides + Email Client

This test build adds producer-facing manual override functionality and simplifies the preview surface.

## Day Inspector overrides

Selecting a calendar day now opens a Day Inspector editor. Users can assign the selected day or a date range to a phase overlay, including:

- Production (Additional Photography)
- Production
- Pre-Production
- Travel/Prep
- Post Production
- Print & Ship
- Hiatus
- R&D

Overrides are overlays only. They do not move Post Production, Print & Ship, Ready for Release, or other calculated phase handoffs. This supports additional photography or reshoots during Post while Post continues.

## Email client selection

The Email action now uses an explicit client selector:

- Apple Mail
- Outlook

The same value is available in Project Setup, the top action bar, and the output panel. Apple Mail uses the platform mailto handler. Outlook opens Microsoft 365 Outlook Web compose with the generated stakeholder summary and export links.

## Removed from the working preview

The scenario comparison panel and reasoning card were removed from the visible UI per workflow feedback. The calendar, summary, assistant, day inspector, and export workflow remain intact.

## Export behavior

Manual day overrides are included in the live calendar preview and in the Excel/PDF calendar exports. Additional Photography uses the Production blue color and appears as an overlay.
