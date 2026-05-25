# Email sharing behavior

The hosted web app cannot reliably attach generated files through a browser email compose link. Instead, the app now:

1. Generates the Excel export.
2. Generates the PDF export.
3. Creates signed temporary download links for each file.
4. Opens the selected email compose provider with the links already in the message body.

Links expire after 7 days. For true one-click sending with attachments, integrate Microsoft Graph, Gmail API, or SMTP in a later phase.


## v2.2 Native Outlook App behavior

The normal Outlook option now prefers the installed Outlook application instead of Outlook Web. On iPhone/iPad, the app first attempts to open the Outlook mobile compose sheet. If that is unavailable, it falls back to the standards-based `mailto:` handler. On Mac, browser apps cannot reliably force a specific desktop mail client by name; setting Outlook as the default email reader makes the fallback open Outlook desktop.

Generated Excel and PDF files are still shared as temporary download links in the message body because browser compose links cannot reliably attach generated files across providers.
