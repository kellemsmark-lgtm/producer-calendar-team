# Email sharing behavior

The hosted web app cannot reliably attach generated files through a browser email compose link. Instead, the app now:

1. Generates the Excel export.
2. Generates the PDF export.
3. Creates signed temporary download links for each file.
4. Opens the selected email compose provider with the links already in the message body.

Links expire after 7 days. For true one-click sending with attachments, integrate Microsoft Graph, Gmail API, or SMTP in a later phase.
