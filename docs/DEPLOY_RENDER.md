# Deploy to Render

## 1. Create a private Git repository

Put the contents of this folder into a private GitHub/GitLab repository.

## 2. Create a Render web service

In Render, create a new Web Service from the repository and select Docker as the runtime.

## 3. Environment variables

Set:

```text
SECRET_KEY=<long random string>
SECURE_COOKIES=true
CALENDAR_USERNAME=andy.davis
CALENDAR_PASSWORD=<strong password>
```

For multiple users, set this instead of the single user variables:

```text
CALENDAR_USERS_JSON={"andy.davis":"password one","team.member":"password two"}
```

## 4. Deploy

Render will build the Dockerfile, install LibreOffice and Python dependencies, and start Gunicorn.

## 5. Share the URL

Share the HTTPS Render URL with the team. On iPhone/iPad, users can add the URL to their Home Screen from Safari.

## 6. Custom domain

Optional: add a custom domain such as:

```text
https://producer-calendar.yourcompany.com
```

## Important production notes

- Do not use the fallback demo login.
- Keep the repository private.
- Use a strong `SECRET_KEY`.
- Keep `SECURE_COOKIES=true` for HTTPS deployments.
- Use one container instance unless persistent shared session storage is added.
