# Producer Calendar - Apple-Quality Redesign Proposal

## 1. Product Strategy

The redesign treats Producer Calendar as a serious production planning instrument, not a consumer calendar and not a generic dashboard. The calendar remains the primary object. The interface is redesigned around three persistent modes: structured form entry, AI-guided intake, and live preview. These modes do not replace one another; they share the same schedule state so users can start with a guided conversation, inspect/edit the fields directly, then export immediately.

Preserved: project setup, production inputs, phase color logic, holiday/workday calculations, schedule summary, selected-day inspection, full month-grid calendar, Excel/PDF/email export workflows, authentication, and Render deployment. Improved: hierarchy, typography, calmness, density management, left-rail grouping, action priority, schedule reasoning, scenario comparison, and integrated assistant behavior.

## 2. UI Concept

### Visual system
- Calm professional surface: warm off-white background, graphite text, thin borders, subtle depth.
- Native-feeling panels: translucent, light, restrained cards rather than heavy boxes.
- Calendar-first layout: the year grid dominates the canvas; controls support it rather than competing with it.
- Dense but quiet: compact input controls, section labels, and muted dividers preserve efficiency.

### Typography
- Use the Apple system font stack: `-apple-system, BlinkMacSystemFont, SF Pro Text, SF Pro Display, Segoe UI, sans-serif`.
- Project title uses display weight; section labels use small caps/kicker treatment.
- Numeric schedule facts use monospaced/tabular numerals for scanability.

### Color
- Base palette: warm paper, graphite, soft blue system accent.
- Phase colors stay semantic and production-specific:
  - R&D: light orange
  - Pre-Production: yellow
  - Travel/Prep: tan
  - Production: blue
  - Holidays/Hiatus: pink
  - Post Production: red
  - Print & Ship: green
  - Ready for Release: black with white text
- AI/reasoning callouts use restrained amber/blue, never neon.

### Surface and buttons
- Primary action: Calculate.
- Secondary actions: Excel, PDF, Email.
- Destructive or reset actions are visually quieter and not near export actions.
- Buttons use subtle native-like shadows and consistent rounded rectangles, not large marketing-style pills.

### Calendar styling
- Month-grid calendar remains central.
- Month modules use clear titles, thin grid lines, high-contrast day numbers, and phase fills.
- Selected day uses an outline, not a disruptive glow.
- Holidays override production color, matching the production rule.

## 3. Information Architecture

### Top bar
- App icon and product identity.
- Current project title and hosted/PWA status.
- Mode switch: Form, Assistant, Preview.
- Primary actions: Calculate, Excel, PDF, Email, Sign Out.

### Left rail
1. Project Setup
   - project title
   - as-of date
   - production location
   - scheduling anchor
   - email provider
2. Schedule Inputs
   - phase tabs with editable date/duration fields
   - production uses shoot days
   - non-production phases use workweeks
3. AI Assistant
   - optional guided intake and reasoning
   - does not replace the form
4. Summary
   - high-density scenario facts
5. Day Inspector
   - selected date, phase, holiday, workday status

### Main canvas
- Calendar header with project summary.
- Year chips for schedules spanning multiple years.
- Full month-grid calendar.
- Reasoning card explaining assumptions and shifts.
- Scenario comparison panel.
- Export/share panel.

### Flow
User can begin from any mode:
- Form mode: direct entry, fastest for known schedules.
- Assistant mode: guided intake for incomplete assumptions.
- Preview mode: live schedule validation and export.
All modes use the same structured schedule data.

## 4. AI Assistant UX

The AI assistant appears as a coordinator panel in the left rail. It is not a full-screen chat product. It asks short production-specific questions and writes answers into the same fields the user can edit manually.

Example prompts:
- What is the project title?
- What is the as-of date for this version?
- Where is production based?
- Should we anchor from production start or ready-for-release?
- How many shoot days are planned?
- Is there a hiatus window?
- How many post-production workweeks should we assume?
- Should Print & Ship remain 4 weeks?
- Which email provider should the draft use?

Mapping examples:
| User answer | Structured field update |
|---|---|
| "Feature Film" | Project title |
| "as of 5/22/26" | As-of date |
| "shooting in the UK" | Production location = United Kingdom |
| "40 shoot days" | Production days = 40 |
| "release target August 16, 2027" | Ready for Release = 08/16/27 |
| "hiatus Dec 20 to Jan 2" | Hiatus start/end |

AI reasoning callouts:
- "Production uses Monday-Friday workdays. Three selected-location holidays extend the run."
- "The release anchor pushed Print & Ship back four workweeks, then Post, Hiatus, Production, and Pre-Production were calculated upstream."
- "Hiatus overlaps the year boundary; the export will include 2026 and 2027 tabs."
- "Pre-Production is using the default 12 workweeks."

The first test build includes a guided/rule-based coordinator layer. A true LLM provider can be added later behind the same assistant UI without changing the user-facing workflow.

## 5. Screen-by-Screen Redesign

### A. Default schedule builder
Purpose: fastest path for experienced users.
Layout: left rail shows Project Setup and Schedule Inputs; main canvas shows the calendar. Calculate and export buttons are always visible in the top bar.
Hierarchy: project identity first, inputs second, calendar output dominant.
Key interactions: edit fields, select phase tab, calculate, click a day, export.
Visual notes: compact controls, clear field labels, low-chrome containers.
Why better: less visual bulk while preserving the density that makes the app useful in meetings.

### B. AI-guided setup screen
Purpose: collect incomplete assumptions during live discussion.
Layout: Assistant card becomes visually emphasized; other left-rail sections remain visible but de-emphasized.
Hierarchy: coordinator prompt, answer field, quick scenario chips, structured fields still visible.
Key interactions: answer prompt, use starter prompt, skip optional data, review populated fields.
Visual notes: small message cards and callouts, no oversized bubbles.
Why better: AI augments the existing production workflow instead of replacing it.

### C. Live scenario comparison
Purpose: compare changes without losing the baseline.
Layout: main canvas includes Scenario A/B summary panel under the calendar.
Hierarchy: Ready date, Production start, shoot days, holiday extension days.
Key interactions: capture Scenario A, adjust fields, compare current scenario.
Visual notes: compact metric tiles, not a separate analytics dashboard.
Why better: supports meeting-room decision making and clear tradeoffs.

### D. Selected-day inspector
Purpose: explain what is happening on a specific date.
Layout: Day Inspector card in the left rail; calendar selection stays visible.
Hierarchy: selected date, phase, holiday, workday status, relevant notes.
Key interactions: click calendar cell; inspector updates instantly.
Visual notes: high contrast labels, phase chip, concise explanation.
Why better: reduces ambiguity about holidays, hiatus, and phase overlaps.

### E. Export/share flow
Purpose: produce stakeholder-ready outputs immediately.
Layout: top actions remain prominent; export/share panel in main canvas explains what will be generated.
Hierarchy: Excel, PDF, Draft Email.
Key interactions: export file, create PDF, generate email with links and summary.
Visual notes: confirmation is inline and calm; no modal unless blocking error occurs.
Why better: maintains the production value of the tool: calendar in, deliverables out.

## 6. Component System

| Component | Role | Visual behavior | States | Hierarchy contribution |
|---|---|---|---|---|
| Top navigation/project header | Persistent identity and actions | translucent warm surface, compact | default, calculating, export-ready | anchors the product and actions |
| Mode switch | Form/Assistant/Preview | segmented native control | active, hover, focus | keeps hybrid model explicit |
| Phase selector | Navigate inputs | compact chips with phase hints | active, inactive | reduces form length without hiding phases |
| Schedule input card | Editable schedule source | light panel, clear fields | filled, missing, invalid | source of truth |
| AI assistant panel | Guided intake/reasoning | integrated sidecar | idle, asking, captured, conflict | augments input without dominating |
| Calendar month module | Primary output | refined grid, phase fills | normal, selected, holiday, out-of-range | central visual object |
| Day inspector | Explain date | small structured facts | no selection, date selected | context and trust |
| Summary cards | Scenario facts | compact metric tiles | neutral, warning | quick scan of schedule health |
| Reasoning banners | Explain changes | quiet blue/amber cards | info, assumption, warning | makes logic visible |
| Export action row | Deliverables | button group with primary/secondary | ready, busy, success, error | meeting workflow completion |
| Scenario comparison controls | Compare options | metric grid | empty, captured, changed | supports planning decisions |

## 7. Apple-Quality Interaction Details

- Transitions: 120-180 ms ease for mode changes, section focus, and calendar updates.
- Hover/focus: subtle surface lift and blue focus ring, never heavy shadows.
- Tap targets: at least 44px where possible on iPhone/iPad.
- Assistant open/close: segmented mode switch scrolls the assistant into view while keeping form fields available.
- Recalculation feedback: Calculate button shows disabled/busy state; updated dates briefly highlight.
- Schedule changes: changed scenario facts are emphasized in the comparison panel.
- Export confirmation: inline message includes filename and link state; errors are plain-language.
- Microcopy: production coordinator tone: direct, factual, no hype.

## 8. Sample AI Conversation

Assistant: What is the project title?
User: Feature Film.
Assistant: Captured project title: Feature Film. What is the as-of date for this version?
User: 5/22/26.
Assistant: Captured as-of date: 05/22/26. Where is production based?
User: United States.
Assistant: Captured production location: United States. Should we anchor from production start or ready for release?
User: Work backwards from release, August 16, 2027.
Assistant: Captured Ready for Release: 08/16/27. I will calculate backward from that milestone. How many shoot days?
User: 40 shoot days.
Assistant: Captured 40 shoot days. Production uses Monday-Friday workdays. Do you have a hiatus?
User: Yes, December 20, 2026 to January 2, 2027.
Assistant: Captured hiatus 12/20/26 to 01/02/27. I found that the scenario crosses calendar years, so the export will include 2026 and 2027.
User: Use 26 weeks of post and four weeks for print and ship.
Assistant: Captured Post Production: 26 weeks. Print & Ship: 4 weeks. I will preserve Pre-Production at the default 12 weeks.
Assistant: Production shifts because U.S. holidays inside the production window extend the schedule. Ready for Release remains 08/16/27; upstream phases have been recalculated backward.
Assistant: Stakeholder note prepared: Feature Film is scheduled from Pre-Production through Ready for Release, using U.S. holiday logic, 40 shoot days, 26 workweeks of Post, and 4 workweeks for Print & Ship.

## 9. Export Outputs

### Excel export structure
- One tab per year touched by the schedule.
- Calendar grid in the established SPE-style format.
- Top summary: project title, ready-for-release, as-of date, shoot days, post weeks.
- Bottom Dates box: phase start lines, durations, hiatus if used, Print & Ship, Ready for Release.
- Formula-backed workbook remains editable after export.
- Optional AI/coordinator summary can be included in notes/summary area.

### PDF summary structure
- PDF mirrors the Excel calendar tabs.
- Uses the same phase color logic and bottom box structure.
- Includes AI/coordinator assumptions when available.

### Email draft output
Subject: Producer Calendar - Feature Film
Body:
- Project title
- Production location
- Ready for Release
- Schedule assumptions
- Holiday/workday explanation
- Download links for Excel and PDF
- Notes that links expire if hosted link signing is active

## 10. Build Brief for UI Generator

Design principles:
- Calendar-first.
- Structured fields remain visible and editable.
- AI assists, never replaces.
- Dense, practical, calm.
- No startup dashboard styling.

Layout rules:
- Top bar contains project identity, mode switch, and export actions.
- Left rail contains setup, inputs, assistant, summary, inspector.
- Main canvas contains calendar, reasoning, comparison, export status.
- On iPhone, left rail becomes stacked sections above the calendar or a drawer; calendar remains accessible.

Components:
- ProjectHeader
- ModeSwitch
- ProjectSetupCard
- PhaseInputTabs
- AssistantPanel
- ScheduleSummary
- DayInspector
- CalendarCanvas
- ReasoningPanel
- ScenarioCompare
- ExportPanel

States:
- Empty schedule
- Partial schedule
- Calculated schedule
- Missing input
- Conflict/warning
- Scenario A captured
- Scenario comparison active
- Export busy
- Export success
- Export failure

AI behavior rules:
- Ask one clear question at a time unless a grouped intake is more efficient.
- Write answers into structured fields.
- Explain every automatic shift.
- Preserve user editability.
- Never hide schedule inputs behind chat.
- Keep tone concise and coordinator-like.

Visual constraints:
- Use Apple system fonts.
- Use restrained color and subtle depth.
- No gradient blobs, neon, novelty AI chrome, or chat-first layout.
- Maintain semantic phase colors.
- Keep export actions visible.

Interaction constraints:
- No context loss when switching modes.
- Keep Calculate available at all times once any anchor exists.
- Exports use current structured schedule plus coordinator summary.
- Calendar cell click updates inspector instantly.

## Design North Star

A calm, calendar-first production scheduling cockpit that lets a producer capture assumptions, reason through shifts, compare scenarios, and export stakeholder-ready calendars during a meeting.

## 10-Point Evaluation Checklist

1. The month-grid calendar remains the primary object.
2. Structured schedule fields are always accessible.
3. AI guidance populates editable fields rather than replacing them.
4. Export actions remain prominent.
5. Phase colors remain semantic and production-specific.
6. Holiday/workday logic is visible and explainable.
7. The UI feels calm enough for long work sessions.
8. The interface is dense without feeling heavy.
9. Scenario comparison supports real planning decisions.
10. The app still produces the same Excel/PDF/email outputs.

## UI Generation Prompt

Design a premium Apple-native web/PWA interface for a professional film production scheduling tool. Preserve a calendar-first workflow with project setup, structured timeline inputs, AI-guided intake, schedule summary, selected-day inspector, full month-grid calendar, and Excel/PDF/email exports. Use a calm warm-neutral palette, Apple system typography, subtle native-like depth, compact dense controls, semantic phase colors, and an integrated coordinator-style assistant panel. Do not make it a generic SaaS dashboard or chat-first app. The AI must populate editable structured fields, explain schedule logic, identify conflicts, and prepare export summaries while leaving all core fields visible.
