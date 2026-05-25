# v2.5 Microsoft Graph / Outlook Email

This release changes the Outlook path from local Outlook deep links to Microsoft Graph sending.

## What the user experiences

When the user chooses **Outlook / Microsoft 365 Send** and clicks **Email**:

1. The app generates the Excel export.
2. The app generates the PDF export.
3. If the user has not connected Microsoft 365 yet, the app shows a **Connect Microsoft 365** sheet.
4. After Microsoft sign-in/consent, the user clicks Email again.
5. The app sends through Microsoft Graph using `/me/sendMail`.
6. The message is sent from the signed-in Outlook/Microsoft 365 mailbox and appears in that mailbox's Sent Items.

This is not a local Outlook compose window. It is the same sender/outbox result in Outlook, but it is server-side and reliable across Mac, iPhone, and iPad.

## Required Render environment variables

Set these in the Render service:

```text
MICROSOFT_TENANT_ID=<tenant ID or organizations>
MICROSOFT_CLIENT_ID=<Microsoft Entra application/client ID>
MICROSOFT_CLIENT_SECRET=<client secret value>
MICROSOFT_REDIRECT_URI=https://YOUR-RENDER-URL/auth/microsoft/callback
MICROSOFT_SCOPES=openid profile email offline_access User.Read Mail.Send
```

Optional:

```text
GRAPH_DEFAULT_RECIPIENTS=<comma-separated fallback recipients>
GRAPH_SEND_ATTACHMENTS=true
```

## Microsoft Entra app registration

A Microsoft 365 / Entra admin should:

1. Register a new app in Microsoft Entra ID.
2. Add a **Web** redirect URI that exactly matches the Render callback URL.
3. Create a client secret.
4. Add delegated Microsoft Graph permissions:
   - `User.Read`
   - `Mail.Send`
   - `offline_access`
   - `openid`, `profile`, `email`
5. Grant admin consent if required by your tenant.
6. Add the environment variables above to Render.

## UI changes

- Default email method is now **Outlook / Microsoft 365 Send**.
- Apple Mail remains available as **Apple Mail Draft**.
- Project Setup includes **Email recipients** and **Cc** fields.
- Assistant intake can capture email method and recipient intent.

## Notes

Apple Mail remains a local draft flow because a PWA cannot silently send Apple Mail messages. Microsoft Graph is the reliable Outlook path because the server sends through Microsoft 365 instead of relying on native app URL schemes.
