#!/usr/bin/env python3
"""Hosted Producer Calendar team web app.

Pure WSGI app so it can run behind Gunicorn in Docker without a local Terminal.
It provides:
- Team login with signed server-side sessions
- Responsive PWA UI for Mac, iPhone, and iPad
- Schedule API
- Reference-format Excel export
- PDF export that produces PDF files only
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import mimetypes
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import time
from datetime import datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Any, Callable
from urllib.parse import parse_qs, quote, urlencode

from calendar_engine import calculate_schedule
from export_excel import create_workbook
from export_pdf import create_pdf

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
EXPORT_DIR = Path(os.environ.get("EXPORT_DIR", "/tmp/producer_calendar_exports"))
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = os.environ.get("APP_NAME", "Producer Calendar")
BUILD_VERSION = "v1.8-dark-mode-handoff-verified"
SESSION_COOKIE = os.environ.get("SESSION_COOKIE_NAME", "pc_session")
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(8 * 60 * 60)))
SECURE_COOKIES = os.environ.get("SECURE_COOKIES", "true").lower() in {"1", "true", "yes", "on"}
MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "12"))
LOGIN_WINDOW_SECONDS = int(os.environ.get("LOGIN_WINDOW_SECONDS", str(15 * 60)))

SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("CALENDAR_SECRET_KEY") or secrets.token_hex(32)

SESSIONS: dict[str, dict[str, Any]] = {}
LOGIN_ATTEMPTS: dict[str, list[float]] = {}


def _safe_filename(name: str) -> str:
    name = (name or "Producer Calendar").strip()
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in name)
    safe = "_".join(safe.split())
    return safe[:80] or "Producer_Calendar"


def _base_url(environ: dict[str, Any]) -> str:
    """Return the public origin URL for links included in email drafts."""
    proto = (environ.get("HTTP_X_FORWARDED_PROTO") or environ.get("wsgi.url_scheme") or "https").split(",")[0].strip()
    host = (environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_HOST") or "").split(",")[0].strip()
    if not host:
        host = "localhost"
    return f"{proto}://{host}"


def _share_token(filename: str, expires: int) -> str:
    raw = f"{filename}|{expires}"
    sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{raw}|{sig}".encode("utf-8")).decode("ascii").rstrip("=")


def _verify_share_token(filename: str, token: str) -> bool:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        token_filename, expires_s, sig = raw.rsplit("|", 2)
        if not hmac.compare_digest(token_filename, filename):
            return False
        expires = int(expires_s)
        if expires < int(time.time()):
            return False
        expected = hmac.new(SECRET_KEY.encode("utf-8"), f"{token_filename}|{expires}".encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


def _make_share_url(environ: dict[str, Any], filename: str, days: int = 7) -> str:
    expires = int(time.time()) + max(1, days) * 24 * 60 * 60
    token = _share_token(filename, expires)
    return f"{_base_url(environ)}/share/{quote(filename)}?token={quote(token)}"


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, default=str).encode("utf-8")


def _hash_password(password: str, salt: str | None = None, iterations: int = 260000) -> str:
    salt = salt or base64.urlsafe_b64encode(secrets.token_bytes(18)).decode("ascii").rstrip("=")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    digest = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        scheme, iter_s, salt, digest = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        check = _hash_password(password, salt=salt, iterations=int(iter_s))
        return hmac.compare_digest(check, stored_hash)
    except Exception:
        return False


def _load_users() -> tuple[dict[str, str], bool]:
    """Return username -> password hash and whether app is using fallback credentials.

    Preferred production config:
        CALENDAR_USERS_JSON='{"andy.davis":"strong password","team.member":"another password"}'
    or:
        CALENDAR_USERNAME='andy.davis'
        CALENDAR_PASSWORD='strong password'
    """
    users: dict[str, str] = {}
    hashes = os.environ.get("CALENDAR_PASSWORD_HASHES_JSON")
    if hashes:
        parsed = json.loads(hashes)
        return {str(k): str(v) for k, v in parsed.items()}, False

    users_json = os.environ.get("CALENDAR_USERS_JSON")
    if users_json:
        parsed = json.loads(users_json)
        for username, password in parsed.items():
            users[str(username)] = _hash_password(str(password))
        return users, False

    users_simple = os.environ.get("CALENDAR_USERS")
    if users_simple:
        # Format: username:password,another.user:another-password
        for pair in users_simple.split(","):
            if not pair.strip() or ":" not in pair:
                continue
            username, password = pair.split(":", 1)
            users[username.strip()] = _hash_password(password.strip())
        if users:
            return users, False

    username = os.environ.get("CALENDAR_USERNAME")
    password = os.environ.get("CALENDAR_PASSWORD")
    if username and password:
        return {username: _hash_password(password)}, False

    # Development-only fallback so the container can be smoke tested.
    return {"demo": _hash_password("change-me-now")}, True


USERS, USING_FALLBACK_LOGIN = _load_users()


def _sign(value: str) -> str:
    sig = hmac.new(SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{value}.{sig}"


def _unsign(value: str) -> str | None:
    if "." not in value:
        return None
    raw, sig = value.rsplit(".", 1)
    expected = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected):
        return raw
    return None


def _client_ip(environ: dict[str, Any]) -> str:
    forwarded = environ.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return environ.get("REMOTE_ADDR", "unknown")


def _is_https(environ: dict[str, Any]) -> bool:
    return environ.get("wsgi.url_scheme") == "https" or environ.get("HTTP_X_FORWARDED_PROTO", "").split(",")[0].strip() == "https"


def _cookie_header(token: str, environ: dict[str, Any], clear: bool = False) -> str:
    secure = SECURE_COOKIES and _is_https(environ)
    parts = [f"{SESSION_COOKIE}={token if not clear else ''}", "Path=/", "HttpOnly", "SameSite=Lax"]
    if secure:
        parts.append("Secure")
    if clear:
        parts.append("Max-Age=0")
    else:
        parts.append(f"Max-Age={SESSION_TTL_SECONDS}")
    return "; ".join(parts)


def _parse_cookies(environ: dict[str, Any]) -> SimpleCookie:
    c = SimpleCookie()
    raw = environ.get("HTTP_COOKIE") or ""
    try:
        c.load(raw)
    except Exception:
        pass
    return c


def _current_user(environ: dict[str, Any]) -> str | None:
    cookies = _parse_cookies(environ)
    morsel = cookies.get(SESSION_COOKIE)
    if not morsel:
        return None
    token = _unsign(morsel.value)
    if not token:
        return None
    sess = SESSIONS.get(token)
    if not sess:
        return None
    if sess.get("expires", 0) < time.time():
        SESSIONS.pop(token, None)
        return None
    sess["expires"] = time.time() + SESSION_TTL_SECONDS
    return str(sess.get("username"))


def _make_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {"username": username, "expires": time.time() + SESSION_TTL_SECONDS}
    return _sign(token)


def _cleanup_sessions() -> None:
    now = time.time()
    for token, sess in list(SESSIONS.items()):
        if sess.get("expires", 0) < now:
            SESSIONS.pop(token, None)


def _rate_limited(ip: str) -> bool:
    now = time.time()
    attempts = [t for t in LOGIN_ATTEMPTS.get(ip, []) if now - t <= LOGIN_WINDOW_SECONDS]
    LOGIN_ATTEMPTS[ip] = attempts
    return len(attempts) >= MAX_LOGIN_ATTEMPTS


def _record_failed_login(ip: str) -> None:
    LOGIN_ATTEMPTS.setdefault(ip, []).append(time.time())


def _read_body(environ: dict[str, Any]) -> bytes:
    length = int(environ.get("CONTENT_LENGTH") or 0)
    return environ["wsgi.input"].read(length) if length else b""


def _read_json(environ: dict[str, Any]) -> dict[str, Any]:
    raw = _read_body(environ)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _status(code: int) -> str:
    try:
        phrase = HTTPStatus(code).phrase
    except Exception:
        phrase = "OK"
    return f"{code} {phrase}"


def _headers(content_type: str, length: int | None = None, extra: list[tuple[str, str]] | None = None, no_store: bool = True) -> list[tuple[str, str]]:
    headers = [("Content-Type", content_type)]
    if length is not None:
        headers.append(("Content-Length", str(length)))
    if no_store:
        headers.append(("Cache-Control", "no-store"))
    headers.extend([
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "same-origin"),
    ])
    if extra:
        headers.extend(extra)
    return headers


def _response(start_response: Callable, code: int, body: bytes, content_type: str = "text/plain", extra: list[tuple[str, str]] | None = None, no_store: bool = True):
    start_response(_status(code), _headers(content_type, len(body), extra, no_store=no_store))
    return [body]


def _json_response(start_response: Callable, code: int, payload: Any, extra: list[tuple[str, str]] | None = None):
    return _response(start_response, code, _json_bytes(payload), "application/json", extra)


def _redirect(start_response: Callable, location: str, extra: list[tuple[str, str]] | None = None):
    headers = [("Location", location)]
    if extra:
        headers.extend(extra)
    return _response(start_response, 302, b"", "text/plain", headers)


def _login_page(error: str = "") -> bytes:
    fallback = ""
    if USING_FALLBACK_LOGIN:
        fallback = """
          <div class=\"warning\"><b>Setup required:</b> this deployment is using demo credentials. Set CALENDAR_USERNAME/CALENDAR_PASSWORD or CALENDAR_USERS_JSON before sharing with the team.</div>
        """
    safe_error = html.escape(error)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">
  <meta name=\"apple-mobile-web-app-capable\" content=\"yes\">
  <meta name=\"apple-mobile-web-app-title\" content=\"Producer Calendar\">
  <meta name=\"theme-color\" content=\"#101827\">
  <link rel=\"manifest\" href=\"/static/manifest.webmanifest\">
  <link rel=\"apple-touch-icon\" href=\"/static/icons/apple-touch-icon.png\">
  <title>{html.escape(APP_NAME)} Login</title>
  <style>
    * {{ box-sizing: border-box; }}
    html {{ min-height:100%; -webkit-text-size-adjust:100%; }}
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","SF Pro Display","Segoe UI",Helvetica,Arial,sans-serif; background:radial-gradient(circle at 10% 0,rgba(10,132,255,.22),transparent 34%),radial-gradient(circle at 90% 4%,rgba(112,173,71,.18),transparent 30%),linear-gradient(180deg,#f5f6fb,#eceff6); color:#111114; padding:24px; }}
    .card {{ width:min(460px,100%); background:rgba(255,255,255,.82); border:1px solid rgba(255,255,255,.72); border-radius:30px; box-shadow:0 24px 70px rgba(27,39,64,.16); padding:30px; backdrop-filter:saturate(180%) blur(26px); -webkit-backdrop-filter:saturate(180%) blur(26px); }}
    .card::before {{ content:""; display:block; width:56px; height:56px; border-radius:17px; background:linear-gradient(145deg,#0a84ff,#0b1220 72%); box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 14px 30px rgba(0,102,204,.25); margin-bottom:18px; }}
    .eyebrow {{ font-size:11px; text-transform:uppercase; letter-spacing:.12em; color:#0066cc; font-weight:800; }}
    h1 {{ margin:6px 0 8px; font-size:36px; line-height:1; letter-spacing:-.035em; }}
    p {{ margin:0 0 18px; color:#6e6e73; line-height:1.42; }}
    label {{ display:block; font-size:12px; font-weight:760; color:#6e6e73; margin:14px 0 6px; }}
    input {{ width:100%; min-height:46px; border:1px solid rgba(60,60,67,.14); border-radius:15px; padding:12px 13px; font:inherit; background:rgba(255,255,255,.82); outline:none; }}
    input:focus {{ border-color:rgba(0,102,204,.55); box-shadow:0 0 0 4px rgba(0,102,204,.13); background:#fff; }}
    button {{ width:100%; border:0; border-radius:15px; margin-top:18px; padding:13px; background:linear-gradient(180deg,#0a84ff,#0066cc); color:white; font-weight:800; font-size:16px; cursor:pointer; box-shadow:0 12px 26px rgba(0,102,204,.24); }}
    .error,.warning {{ background:#fff7eb; border:1px solid #ffdca8; color:#7a4700; border-radius:15px; padding:11px; margin:14px 0; font-size:13px; line-height:1.35; }}
    .small {{ margin-top:16px; font-size:12px; color:#6e6e73; }}
  </style>
</head>
<body>
  <form class=\"card\" method=\"post\" action=\"/login\">
    <div class=\"eyebrow\">Team Login</div>
    <h1>Producer Calendar</h1>
    <p>Sign in to create, export, and share production calendars.</p>
    {fallback}
    {f'<div class="error">{safe_error}</div>' if error else ''}
    <label>Username</label>
    <input name=\"username\" autocomplete=\"username\" required autofocus>
    <label>Password</label>
    <input name=\"password\" type=\"password\" autocomplete=\"current-password\" required>
    <button type=\"submit\">Sign in</button>
    <div class=\"small\">On iPhone or iPad, sign in with Safari, then use Share > Add to Home Screen.</div>
  </form>
</body>
</html>""".encode("utf-8")


def _serve_static(start_response: Callable, path: str):
    rel = path[len("/static/"):].lstrip("/")
    target = (STATIC_DIR / rel).resolve()
    if not str(target).startswith(str(STATIC_DIR.resolve())):
        return _response(start_response, 403, b"Forbidden")
    if not target.exists() or not target.is_file():
        return _response(start_response, 404, b"Not found")
    ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    # Static files may be cached; app HTML/API/exports are not cached.
    cache_headers = [("Cache-Control", "public, max-age=3600")]
    return _response(start_response, 200, target.read_bytes(), ctype, cache_headers, no_store=False)


def _serve_export(start_response: Callable, path: str):
    filename = Path(path[len("/exports/"):]).name
    target = (EXPORT_DIR / filename).resolve()
    if not str(target).startswith(str(EXPORT_DIR.resolve())):
        return _response(start_response, 403, b"Forbidden")
    if not target.exists() or not target.is_file():
        return _response(start_response, 404, b"Export not found")
    if target.suffix.lower() == ".pdf":
        ctype = "application/pdf"
    elif target.suffix.lower() == ".xlsx":
        ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        ctype = "application/octet-stream"
    headers = [("Content-Disposition", f'attachment; filename="{target.name}"')]
    return _response(start_response, 200, target.read_bytes(), ctype, headers)


def _build_email_url(provider: str, subject: str, body: str) -> str:
    """Build a compose URL.

    Use percent-encoding instead of plus-space encoding so iOS/Outlook clients do
    not display literal + characters in the subject or message body. Browser
    compose links cannot attach local files; links are included in the body.
    """
    provider = (provider or "system").lower()
    params = {"subject": subject, "body": body}
    if provider == "gmail":
        return "https://mail.google.com/mail/?" + urlencode({"view": "cm", "fs": "1", "su": subject, "body": body}, quote_via=quote)
    if provider in {"outlook", "outlook_web", "office365"}:
        return "https://outlook.office.com/mail/deeplink/compose?" + urlencode(params, quote_via=quote)
    return "mailto:?" + urlencode(params, quote_via=quote)


def _api(environ: dict[str, Any], start_response: Callable, path: str):
    try:
        payload = _read_json(environ)
        if path == "/api/schedule":
            return _json_response(start_response, 200, calculate_schedule(payload))

        if path == "/api/export/excel":
            schedule = calculate_schedule(payload)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base = _safe_filename(schedule.get("projectTitle") or "Producer Calendar")
            out = EXPORT_DIR / f"{base}_{stamp}.xlsx"
            create_workbook(payload, out)
            return _json_response(start_response, 200, {"ok": True, "kind": "excel", "filename": out.name, "downloadUrl": f"/exports/{out.name}"})

        if path == "/api/export/pdf":
            schedule = calculate_schedule(payload)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base = _safe_filename(schedule.get("projectTitle") or "Producer Calendar")
            out = EXPORT_DIR / f"{base}_{stamp}.pdf"
            result = Path(create_pdf(payload, out))
            if result.suffix.lower() != ".pdf" or not result.exists() or result.read_bytes()[:5] != b"%PDF-":
                raise RuntimeError("PDF export failed because the generated file was not a valid PDF.")
            return _json_response(start_response, 200, {"ok": True, "kind": "pdf", "filename": result.name, "downloadUrl": f"/exports/{result.name}", "contentType": "application/pdf"})

        if path == "/api/email":
            schedule = calculate_schedule(payload)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base = _safe_filename(schedule.get("projectTitle") or "Producer Calendar")
            xlsx = EXPORT_DIR / f"{base}_{stamp}.xlsx"
            pdf = EXPORT_DIR / f"{base}_{stamp}.pdf"
            create_workbook(payload, xlsx)
            result_pdf = Path(create_pdf(payload, pdf))
            if result_pdf.suffix.lower() != ".pdf" or not result_pdf.exists() or result_pdf.read_bytes()[:5] != b"%PDF-":
                raise RuntimeError("PDF export failed because the generated file was not a valid PDF.")

            excel_link = _make_share_url(environ, xlsx.name)
            pdf_link = _make_share_url(environ, result_pdf.name)
            subject = f"Producer Calendar - {schedule.get('projectTitle') or 'Feature Film'}"
            period_lines = []
            for period in schedule.get("periods") or []:
                label = period.get("label") or period.get("key") or "Phase"
                start = period.get("displayStart") or ""
                end = period.get("displayEnd") or ""
                metric = period.get("metric") or {}
                metric_text = ""
                if metric.get("type") == "weeks":
                    metric_text = f" ({metric.get('value', 0)} weeks)"
                elif metric.get("type") == "workdays":
                    metric_text = f" ({metric.get('value', 0)} shoot days; {metric.get('skippedHolidays', 0)} holiday extension day(s))"
                elif metric.get("type") == "date_range":
                    metric_text = " (single date range)"
                period_lines.append(f"- {label}: {start} to {end}{metric_text}")
            coordinator_summary = str(payload.get("coordinatorSummary") or "").strip()
            if not coordinator_summary:
                coordinator_summary = "Production periods use Monday-Friday workweeks. Production excludes weekends and extends for selected-location holidays."
            body = (
                "Producer Calendar exports are ready.\n\n"
                f"Project: {schedule.get('projectTitle') or 'Feature Film'}\n"
                f"Production location: {schedule.get('productionLocationLabel')}\n"
                f"Ready for Release: {(schedule.get('ready') or {}).get('displayDate', '')}\n\n"
                "Schedule summary:\n"
                + ("\n".join(period_lines) if period_lines else "- No production periods calculated yet.")
                + "\n\nCoordinator notes:\n"
                + coordinator_summary
                + "\n\nDownload links:\n"
                f"Excel: {excel_link}\n"
                f"PDF: {pdf_link}\n\n"
                "Links expire in 7 days. Attachments are not inserted by the browser email draft; download and attach the files if you want physical attachments.\n"
            )
            email_url = _build_email_url(payload.get("emailProvider") or "system", subject, body)
            return _json_response(start_response, 200, {
                "ok": True,
                "provider": payload.get("emailProvider") or "system",
                "emailUrl": email_url,
                "excel": {"filename": xlsx.name, "downloadUrl": f"/exports/{xlsx.name}", "shareUrl": excel_link},
                "pdf": {"filename": result_pdf.name, "downloadUrl": f"/exports/{result_pdf.name}", "shareUrl": pdf_link},
                "message": "Exports created. The email draft now includes direct Excel and PDF download links.",
            })

        return _json_response(start_response, 404, {"ok": False, "error": "Not found"})
    except Exception as exc:
        return _json_response(start_response, 500, {"ok": False, "error": str(exc)})


def application(environ: dict[str, Any], start_response: Callable):
    _cleanup_sessions()
    path = environ.get("PATH_INFO") or "/"
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if path == "/healthz":
        return _json_response(start_response, 200, {"ok": True, "app": APP_NAME, "buildVersion": BUILD_VERSION})

    if path.startswith("/static/"):
        return _serve_static(start_response, path)

    if path.startswith("/share/") and method == "GET":
        filename = Path(path[len("/share/"):]).name
        qs = parse_qs(environ.get("QUERY_STRING") or "")
        token = (qs.get("token", [""])[0] or "").strip()
        if not _verify_share_token(filename, token):
            return _response(start_response, 403, b"This export link is invalid or has expired.")
        target = (EXPORT_DIR / filename).resolve()
        if not str(target).startswith(str(EXPORT_DIR.resolve())) or not target.exists() or not target.is_file():
            return _response(start_response, 404, b"Export not found")
        if target.suffix.lower() == ".pdf":
            ctype = "application/pdf"
        elif target.suffix.lower() == ".xlsx":
            ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            ctype = "application/octet-stream"
        headers = [("Content-Disposition", f'attachment; filename="{target.name}"')]
        return _response(start_response, 200, target.read_bytes(), ctype, headers)

    if path == "/login" and method == "GET":
        if _current_user(environ):
            return _redirect(start_response, "/")
        return _response(start_response, 200, _login_page(), "text/html")

    if path == "/login" and method == "POST":
        ip = _client_ip(environ)
        if _rate_limited(ip):
            return _response(start_response, 429, _login_page("Too many login attempts. Please wait and try again."), "text/html")
        form = parse_qs(_read_body(environ).decode("utf-8"), keep_blank_values=True)
        username = (form.get("username", [""])[0] or "").strip()
        password = form.get("password", [""])[0] or ""
        stored = USERS.get(username)
        if stored and _verify_password(stored, password):
            LOGIN_ATTEMPTS.pop(ip, None)
            token = _make_session(username)
            return _redirect(start_response, "/", [("Set-Cookie", _cookie_header(token, environ))])
        _record_failed_login(ip)
        return _response(start_response, 401, _login_page("Invalid username or password."), "text/html")

    if path == "/logout":
        cookies = _parse_cookies(environ)
        morsel = cookies.get(SESSION_COOKIE)
        if morsel:
            raw = _unsign(morsel.value)
            if raw:
                SESSIONS.pop(raw, None)
        return _redirect(start_response, "/login", [("Set-Cookie", _cookie_header("", environ, clear=True))])

    user = _current_user(environ)
    if not user:
        return _redirect(start_response, "/login")

    if path == "/" and method == "GET":
        html_path = STATIC_DIR / "index.html"
        return _response(start_response, 200, html_path.read_bytes(), "text/html")

    if path == "/api/info" and method == "GET":
        return _json_response(start_response, 200, {
            "mode": "hosted",
            "appName": APP_NAME,
            "username": user,
            "message": "Hosted team app. Add this URL to the iPhone/iPad Home Screen from Safari.",
            "buildVersion": BUILD_VERSION,
        })

    if path.startswith("/api/") and method == "POST":
        return _api(environ, start_response, path)

    if path.startswith("/exports/") and method == "GET":
        return _serve_export(start_response, path)

    return _response(start_response, 404, b"Not found")


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    port = int(os.environ.get("PORT", "8765"))
    print(f"Producer Calendar hosted app running at http://127.0.0.1:{port}")
    print("Dev login defaults to demo / change-me-now unless env users are set.")
    with make_server("0.0.0.0", port, application) as httpd:
        httpd.serve_forever()
