# v2.8 Login Environment Fix

This build prevents malformed multi-user environment variables from crashing Render.

Recommended Render setup:

```text
CALENDAR_USERS=mark.kellems=StrongPassword1;andy.davis=StrongPassword2
```

`CALENDAR_USERS` is preferred over `CALENDAR_USERS_JSON` because it avoids curly quote and JSON punctuation issues in Render.

The app still supports `CALENDAR_USERS_JSON`, but malformed JSON is logged and ignored instead of crashing the worker.
