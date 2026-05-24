# Producer Calendar v1.4 Apple-quality UX refresh

## Intent
This release is a testable design refresh of the hosted Producer Calendar PWA. It keeps the core product intact: project setup, production timeline inputs, schedule summary, day inspector, full month-grid calendar, Excel export, PDF export, and email draft workflow.

The design direction is a premium internal work tool: calm, dense, legible, and fast during live scheduling meetings. The calendar remains the primary object.

## Screen concepts included in the app

1. **Default schedule builder**
   - Left rail begins with Project Setup and Schedule Inputs.
   - Inputs remain structured and directly editable.
   - Defaults remain Pre-Production 12 weeks, Post Production 26 weeks, Print & Ship 4 weeks.

2. **AI-guided setup flow**
   - Integrated Assistant panel asks coordinator-style scheduling questions.
   - Answers populate the structured fields instead of replacing them.
   - Starter prompts support Production-start, Release-backward, and conflict review scenarios.
   - This is a guided intake layer in the test build; a true LLM provider can be attached later.

3. **Live scenario comparison**
   - Capture Scenario A, adjust inputs, then compare Ready date, Production start, shoot days, and holiday extensions.

4. **Selected-day inspector**
   - Clicking highlighted calendar days updates the Day Inspector with production phase, holiday, ready milestone, and workday status.

5. **Export/share flow**
   - Calculate, Excel, PDF, and Email remain prominent.
   - Email draft now includes a cleaner stakeholder-style schedule summary and export links.

## Design principles applied

- Reduced visual heaviness by replacing dashboard chrome with softer native-style panels.
- Preserved density: the calendar, summary, and inputs remain visible and efficient.
- Improved hierarchy: setup, schedule inputs, assistant, summary, inspector, preview, and exports each have clear roles.
- Increased consistency: one button language, one field language, one phase color system.
- Kept production-specific logic visible: workweek assumptions, holidays, hiatus, release target, and exports remain first-class.

## What did not change

- Backend schedule calculation.
- Holiday calculation assumptions.
- Excel export format.
- PDF export behavior.
- Login/authentication model.
- Render deployment model.
