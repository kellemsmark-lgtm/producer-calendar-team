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
