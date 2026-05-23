# Recommended Next Steps

## Phase 2A - Hosted pilot

Deploy the Docker app privately and give access to a small internal group.

Pilot checklist:

- Confirm login works for every tester.
- Confirm iPhone and iPad Home Screen installation.
- Confirm Excel export format.
- Confirm PDF export format.
- Confirm email draft workflow.
- Confirm export performance during a live meeting.

## Phase 2B - Team hardening

Recommended enhancements after pilot:

- Microsoft 365 / Entra ID single sign-on.
- Microsoft Graph email send with generated files attached.
- Saved calendar scenarios.
- Audit log of exports.
- Admin screen for team users.
- Custom domain.

## Phase 3 - Native wrapper if needed

If a true App Store/TestFlight app is still desired, wrap the hosted PWA in a native iOS/iPadOS shell after the hosted workflow is locked.

## v1.1 Email draft behavior

The Email Draft button now creates both exports and places direct, signed download links for the Excel and PDF files into the email body. These links expire after 7 days. Browser compose links cannot attach files directly; true attachment sending should be implemented later through Microsoft Graph, Gmail API, or SMTP.
