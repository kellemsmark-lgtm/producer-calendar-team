# Producer Calendar - Hosted Team PWA

This is the hosted team version of the Producer Calendar app.

It runs as a secure web app/PWA with:

- Mac, iPhone, and iPad browser support
- iPhone/iPad Home Screen support
- Team login
- No Terminal for end users
- No local install for end users
- Same production schedule engine
- Same reference-style Excel export
- PDF export button that returns PDF only

## Fast deploy target

The package includes a Dockerfile and `render.yaml` for a Docker web service. It can also be deployed to any container host that supports Python + Docker.

## Required environment variables

Set at least:

```text
SECRET_KEY=<long random string>
CALENDAR_USERNAME=andy.davis
CALENDAR_PASSWORD=<strong password>
SECURE_COOKIES=true
```

For multiple users, use:

```text
CALENDAR_USERS_JSON={"andy.davis":"password one","team.member":"password two"}
```

Do not commit real passwords to source control.

## Local smoke test

```bash
python3 -m pip install -r requirements.txt
export SECRET_KEY="dev-secret-change-me"
export CALENDAR_USERNAME="andy.davis"
export CALENDAR_PASSWORD="change-me-now"
python3 app.py
```

Then open:

```text
http://127.0.0.1:8765
```

## Docker smoke test

```bash
docker build -t producer-calendar-team .
docker run --rm -p 10000:10000 \
  -e SECRET_KEY="dev-secret-change-me" \
  -e CALENDAR_USERNAME="andy.davis" \
  -e CALENDAR_PASSWORD="change-me-now" \
  producer-calendar-team
```

Then open:

```text
http://127.0.0.1:10000
```

## iPhone/iPad Home Screen

After the app is hosted at an HTTPS URL:

1. Open the URL in Safari.
2. Sign in.
3. Tap Share.
4. Tap Add to Home Screen.
5. Launch it like an app from the Home Screen.

## Notes

- The app stores exports temporarily on the server for download.
- Email draft links cannot reliably attach generated files across every provider, so the app creates downloadable Excel/PDF files and opens the chosen compose flow.
- For one-click email with attachments, the next step is Microsoft Graph or SMTP integration.

## v1.1 update

Email Draft now includes direct signed Excel/PDF download links in the message body. Links expire in 7 days. True file attachments require a provider API integration such as Microsoft Graph, Gmail API, or SMTP.


## v1.3 default period settings

Default production-period values are now Pre-Production = 12 weeks, Post Production = 26 weeks, and Print & Ship = 4 weeks. Existing browser-saved values that match prior shipped defaults are migrated automatically.

## v1.4 UX test build

This package includes the Apple-quality UX refresh for testing before replacing the live production interface. Deploy it to a separate Render web service or a test branch first if you want to compare against the current hosted version.

Core functionality is preserved: schedule calculation, Excel export, PDF export, email draft with download links, team login, and PWA/Home Screen support.

## v1.7 Monday handoff update

- Forward schedule handoffs now default to the following Monday after a phase ends.
- If Production ends mid-week, Post Production begins on the next Monday by default.
- A fixed Hiatus that begins later than the default handoff is shown as an overlay/interruption rather than creating a hidden gap that delays the next phase. Select Hiatus as the scheduling anchor if the hiatus range should drive the sequence.
- The Assistant now explains the Monday-handoff assumption during guided intake.


## v1.7 Force Default Durations

Pre-Production, Post Production, and Print & Ship now force their production-planning defaults when old browser state supplies blank or zero values. This ensures Post Production begins on the following Monday after Production ends, even during Assistant intake, unless a user explicitly anchors a different phase.


## v2.1 Ready Friday + Audit

Ready for Release defaults to the last Friday inside Print & Ship. Static assets revalidate faster during UX testing.


## v2.2 Outlook App Email

The Outlook email option now attempts to open the installed Outlook app rather than Outlook Web. If the device/browser cannot open Outlook directly, the flow falls back to the system mail handler. For Mac desktop users who want Outlook, set Outlook as the default email reader in macOS. For iPhone/iPad users, set Outlook as the default email app in iOS/iPadOS Settings.


## v2.4 direct email clients

- Outlook App selection opens the native Outlook compose URL (`ms-outlook://compose`) instead of falling back to Apple Mail.
- Apple Mail selection opens the Apple Mail/default compose route (`mailto:`).
- The email draft includes secure Excel/PDF download links; browser-based drafts cannot attach generated files directly without Microsoft Graph or another mail API.


### v2.4 Email Client Direct Fix

- Outlook App selection now uses a native `ms-outlook://compose` draft link rather than `mailto:`.
- Apple Mail selection uses the standard `mailto:` compose link.
- After export links are generated, the app shows an Email Draft Ready sheet with direct Open Outlook App and Open Apple Mail buttons. This gives Safari/Chrome a direct user gesture for app switching, which is more reliable than launching custom app schemes after an asynchronous export call.
- The hosted web/PWA app still opens a prefilled draft; it cannot silently send a message without user confirmation or attach local files directly. The draft includes secure Excel/PDF links.

## v2.6 Team Share Options

For the pre-InfoSec team pilot, the app supports three share methods without Microsoft Graph/admin consent:

- Outlook Web Draft: opens Outlook on the web compose with the schedule summary and secure Excel/PDF links.
- Apple Mail Draft: uses the device mail compose handler through `mailto:`.
- Messages / Text Links: uses the Web Share API when available, with Messages/SMS and copy fallback.

Generated files are shared as signed links that expire after 7 days. Physical email attachments still require manual download/attach unless a later Microsoft Graph-approved production path is enabled.
