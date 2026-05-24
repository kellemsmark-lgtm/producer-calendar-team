# Producer Calendar v1.2 - UX Polish Notes

This version refreshes the hosted team PWA without changing the core calendar engine, login, Excel export, PDF export, or email-link workflow.

## Design direction

- More spacious iOS/macOS-style visual system using system fonts, translucent panels, larger hit targets, and softer hierarchy.
- Header simplified into a project identity area with primary export actions immediately available.
- Left panel reorganized into Project Setup, Timeline, Schedule Summary, and Selected Day Inspector.
- Production phases remain editable through the same fields and IDs used by the existing API workflow.
- Calendar preview uses clearer month cards, a dark month header, accessible highlighted day states, keyboard focus states, and a concise legend.
- Mobile and iPad layouts stack cleanly while retaining all inputs and export actions.
- Home Screen PWA metadata and icon artwork refreshed.

## Preserved functionality

- Team login
- Local browser state saving
- Schedule calculation
- Production-location holiday logic
- Excel export
- PDF export
- Email draft with temporary Excel/PDF download links
- iPhone/iPad Home Screen support

## Deployment

This package keeps the same Docker, Render, and environment-variable workflow as v1.1. Push the updated files to the same GitHub repo; Render can auto-deploy on commit.


## v1.3 default period settings

Default production-period values are now Pre-Production = 12 weeks, Post Production = 26 weeks, and Print & Ship = 4 weeks. Existing browser-saved values that match prior shipped defaults are migrated automatically.
