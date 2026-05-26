# v2.6 Team Share Options

This pilot build avoids Microsoft Graph / InfoSec approval for team testing.

Email/share methods:

- Outlook Web Draft: opens Outlook on the web compose with the schedule summary and secure Excel/PDF links.
- Apple Mail Draft: uses mailto: to open the device default mail draft.
- Messages / Text Links: uses the Web Share API when available, with a fallback SMS/Messages URL and copy-to-clipboard.

The app cannot attach generated files directly to mailto/SMS from a hosted PWA, so the share text includes signed links to the generated Excel and PDF outputs.

Scheduling, exports, Ready Friday, Monday handoff, additional photography overrides, dark mode, and holiday logic were not changed.
