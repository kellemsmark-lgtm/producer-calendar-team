# Producer Calendar Hosted Team Architecture

## Goal

Turn the local Python prototype into a team-accessible hosted app:

- Works on Mac, iPhone, and iPad
- No Terminal for users
- No local install for users
- Team login
- Shareable HTTPS URL
- Home Screen icon on iPhone/iPad
- Same Excel and PDF outputs

## Runtime architecture

```text
Mac / iPhone / iPad
        |
        | HTTPS
        v
Hosted WSGI Python app
        |
        +-- Auth/session layer
        +-- Static PWA assets
        +-- Schedule API
        +-- Excel export engine
        +-- PDF export engine
        |
        v
Temporary export files
```

## Main files

```text
app.py                         WSGI app, login, sessions, APIs, downloads
calendar_engine.py             Production schedule and holiday calculations
export_excel.py                Reference-style XLSX export
export_pdf.py                  PDF export; prefers LibreOffice XLSX-to-PDF
static/index.html              App UI
static/app.js                  Browser-side calendar interactions
static/styles.css              Responsive Mac/iPad/iPhone styling
static/manifest.webmanifest    PWA manifest
static/service-worker.js       Static asset cache only
templates/SPEBlockCalendar_Template.xlsx  Reference workbook template
Dockerfile                     Production container with LibreOffice
render.yaml                    Render blueprint starter
```

## Authentication

The hosted version uses server-side sessions and environment-configured users. Passwords are not stored in the browser. Session cookies are HttpOnly and SameSite=Lax, with Secure enabled when served over HTTPS.

Single user:

```text
CALENDAR_USERNAME=andy.davis
CALENDAR_PASSWORD=<strong password>
```

Multiple users:

```text
CALENDAR_USERS_JSON={"andy.davis":"password one","team.member":"password two"}
```

## Export flow

```text
User clicks Export Excel
        |
        v
/api/export/excel
        |
        v
export_excel.create_workbook()
        |
        v
reference-style XLSX download
```

```text
User clicks Export PDF
        |
        v
/api/export/pdf
        |
        v
export_pdf.create_pdf()
        |
        +-- Generate temporary XLSX using same layout
        +-- Convert with LibreOffice if available
        +-- Built-in PDF renderer if LibreOffice fails
        v
PDF download only
```

## PWA behavior

The service worker caches static assets only. It does not cache API responses, exports, the login page, or private calendar output.

## Deployment recommendation

Use a Docker web service for the first team deployment. Docker is recommended because the PDF export benefits from a predictable LibreOffice installation.
