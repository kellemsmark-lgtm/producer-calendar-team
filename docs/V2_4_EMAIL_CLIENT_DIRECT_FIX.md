# v2.4 Email Client Direct Fix

This version makes the email client selection explicit.

- Outlook App uses `ms-outlook://compose`.
- Apple Mail uses `mailto:`.
- The Email button generates Excel/PDF share links, then displays a launch sheet with direct buttons for the selected client and the alternate client.
- This is necessary because browsers can block custom app URL schemes when they are opened after asynchronous export generation. The direct button gives the browser a fresh user action.

Limitations: hosted PWAs can open drafts, but cannot silently send mail or attach files directly through local email clients. The draft includes secure download links for the generated Excel and PDF.
