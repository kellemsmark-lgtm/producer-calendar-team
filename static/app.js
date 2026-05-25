const periodMeta = {
  rd: { label: 'R&D', color: '#f4b183' },
  pre: { label: 'Pre-Production', color: '#fff26b' },
  travel: { label: 'Travel/Prep', color: '#d2b48c' },
  production: { label: 'Production', color: '#5b9bd5' },
  production_additional: { label: 'Production (Additional Photography)', color: '#5b9bd5' },
  hiatus: { label: 'Hiatus', color: '#e7a1c4' },
  post: { label: 'Post Production', color: '#e06666' },
  print_ship: { label: 'Print & Ship', color: '#70ad47' },
  ready: { label: 'Ready for Release', color: '#000000', text: '#ffffff' }
};

const stateKey = 'producerCalendarTeamHostedStateV2';
const defaultsVersionKey = 'producerCalendarDefaultVersion';
const currentDefaultsVersion = 'v2.3-outlook-default-stable-email';
const buildVersion = 'v2.3-outlook-default-stable-email';
const themeKey = 'producerCalendarThemePreference';
let activeYear = null;
let lastSchedule = null;
let timer = null;
let assistantStep = 0;
let selectedDayRow = null;

const defaults = {
  projectTitle: 'Feature Film',
  asOfDate: '',
  productionLocation: 'US',
  anchorMode: 'auto',
  emailProvider: 'outlook_app',
  lastEditedAnchor: 'production',
  periods: {
    rd: { start: '', weeks: 0 },
    pre: { start: '', weeks: 12 },
    travel: { start: '', weeks: 0 },
    production: { start: '', days: 45 },
    hiatus: { start: '', end: '' },
    post: { start: '', weeks: 26 },
    print_ship: { start: '', weeks: 4 },
    ready: { date: '' }
  },
  customRanges: []
};

function $(id) { return document.getElementById(id); }

function loadState() {
  try {
    const raw = localStorage.getItem(stateKey) || localStorage.getItem('producerCalendarTeamHostedStateV1');
    if (!raw) return structuredClone(defaults);
    return migrateDefaultWeeks(deepMerge(structuredClone(defaults), JSON.parse(raw)));
  } catch (e) {
    return structuredClone(defaults);
  }
}

function migrateDefaultWeeks(state) {
  // v1.7 production-planning defaults: these phases are core schedule assumptions.
  // Force prior blank/zero saved values back to defaults so old browser state cannot
  // suppress Post Production or Print & Ship during Assistant intake.
  try {
    if (localStorage.getItem(defaultsVersionKey) === currentDefaultsVersion) return state;
    state.periods = state.periods || {};
    state.periods.pre = state.periods.pre || {};
    state.periods.post = state.periods.post || {};
    state.periods.print_ship = state.periods.print_ship || {};
    if (!Array.isArray(state.customRanges)) state.customRanges = [];
    if (!state.emailProvider || state.emailProvider === 'system' || state.emailProvider === 'gmail' || state.emailProvider === 'outlook_web' || state.emailProvider === 'office365' || state.emailProvider === 'apple_mail') state.emailProvider = 'outlook_app';

    if (state.periods.pre.weeks === undefined || state.periods.pre.weeks === '' || Number(state.periods.pre.weeks) <= 0 || Number(state.periods.pre.weeks) === 8) state.periods.pre.weeks = 12;
    if (state.periods.post.weeks === undefined || state.periods.post.weeks === '' || Number(state.periods.post.weeks) <= 0 || Number(state.periods.post.weeks) === 12) state.periods.post.weeks = 26;
    if (state.periods.print_ship.weeks === undefined || state.periods.print_ship.weeks === '' || Number(state.periods.print_ship.weeks) <= 0 || Number(state.periods.print_ship.weeks) === 2) state.periods.print_ship.weeks = 4;

    localStorage.setItem(defaultsVersionKey, currentDefaultsVersion);
    localStorage.setItem(stateKey, JSON.stringify(state));
  } catch (e) {
    // If storage is unavailable, defaults still populate fresh sessions.
  }
  return state;
}

function saveState(payload) {
  localStorage.setItem(stateKey, JSON.stringify(payload));
}

function deepMerge(target, source) {
  for (const [key, value] of Object.entries(source || {})) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      target[key] = deepMerge(target[key] || {}, value);
    } else {
      target[key] = value;
    }
  }
  return target;
}

function valueOrDefault(value, fallback) {
  return value === undefined || value === null || value === '' ? fallback : value;
}

function valueOrPositiveDefault(value, fallback) {
  const n = Number(value);
  return value === undefined || value === null || value === '' || !Number.isFinite(n) || n <= 0 ? fallback : value;
}

function durationOrDefault(id, fallback) {
  const value = $(id)?.value;
  const n = Number(value);
  return !Number.isFinite(n) || n <= 0 ? fallback : n;
}

function ensureTimelineDefaultsInForm() {
  // Keep professional defaults available during Assistant intake before the
  // coordinator asks every duration question. A user can still override these
  // in Form mode, including setting 0 deliberately.
  if ($('preWeeks') && (String($('preWeeks').value).trim() === '' || Number($('preWeeks').value) <= 0)) $('preWeeks').value = '12';
  if ($('postWeeks') && (String($('postWeeks').value).trim() === '' || Number($('postWeeks').value) <= 0)) $('postWeeks').value = '26';
  if ($('printShipWeeks') && (String($('printShipWeeks').value).trim() === '' || Number($('printShipWeeks').value) <= 0)) $('printShipWeeks').value = '4';
}

function normalizeDateInput(value) {
  value = (value || '').trim();
  if (!value) return '';
  const digits = value.replace(/\D/g, '');
  if (digits.length === 6) return `${digits.slice(0,2)}/${digits.slice(2,4)}/${digits.slice(4,6)}`;
  if (digits.length === 8) return `${digits.slice(0,2)}/${digits.slice(2,4)}/${digits.slice(6,8)}`;
  return value;
}


function preferredTheme() {
  const stored = localStorage.getItem(themeKey);
  if (stored === 'dark' || stored === 'light') return stored;
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  const normalized = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = normalized;
  document.documentElement.style.colorScheme = normalized;
  const meta = $('themeColorMeta');
  if (meta) meta.setAttribute('content', normalized === 'dark' ? '#101014' : '#f6f4ef');
  const toggle = $('themeToggle');
  if (toggle) {
    toggle.textContent = normalized === 'dark' ? 'Light' : 'Dark';
    toggle.setAttribute('aria-label', normalized === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  }
}

function initTheme() {
  applyTheme(preferredTheme());
  const toggle = $('themeToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem(themeKey, next);
      applyTheme(next);
    });
  }
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => {
      if (!localStorage.getItem(themeKey)) applyTheme(preferredTheme());
    });
  }
}

function syncCalculatedStartsToForm(data) {
  // Keep the form aligned with the calculated schedule. This makes the Monday
  // handoff visible after Assistant intake, even if the user never manually
  // opens the Post tab. Only blank fields are filled; explicit user-entered
  // dates are left editable and unchanged.
  const fieldFor = { rd: 'rdStart', pre: 'preStart', travel: 'travelStart', production: 'productionStart', post: 'postStart', print_ship: 'printShipStart' };
  for (const period of data.periods || []) {
    const fieldId = fieldFor[period.key];
    if (!fieldId || !$(fieldId)) continue;
    if (!String($(fieldId).value || '').trim() && period.displayStart) {
      $(fieldId).value = period.displayStart;
    }
  }
  const post = (data.periods || []).find(p => p.key === 'post');
  if (post && $('postStart')) {
    $('postStart').placeholder = post.displayStart || 'mm/dd/yy';
  }
  if (data.ready?.displayDate && $('readyDate') && !String($('readyDate').value || '').trim()) {
    $('readyDate').placeholder = data.ready.displayDate;
  }
}

function buildCoordinatorSummary() {
  if (!lastSchedule) return '';
  const production = (lastSchedule.periods || []).find(p => p.key === 'production');
  const ready = lastSchedule.ready || {};
  const parts = [];
  if (lastSchedule.anchorLabel) parts.push(`Anchor: ${lastSchedule.anchorLabel}.`);
  if (production) parts.push(`Production: ${production.displayStart} to ${production.displayEnd}, ${production.metric?.value || 0} shoot days, ${production.metric?.skippedHolidays || 0} holiday extension day(s).`);
  if (ready.displayDate) parts.push(`Ready for Release: ${ready.displayDate}.`);
  const custom = (lastSchedule.customRanges || []);
  if (custom.length) parts.push(`Manual day overrides: ${custom.map(r => `${r.label}: ${r.displayStart} to ${r.displayEnd}`).join('; ')}.`);
  for (const note of lastSchedule.notes || []) parts.push(note);
  return parts.join(' ');
}


function emailProviderControls() {
  return ['emailProvider', 'emailProviderTop', 'emailProviderOutput'].map(id => $(id)).filter(Boolean);
}

function normalizeEmailProvider(value) {
  const v = String(value || '').toLowerCase();
  if (v.includes('outlook') || v.includes('office') || v === 'outlook' || v === 'outlook_app') return 'outlook_app';
  return 'apple_mail';
}

function getEmailProviderValue() {
  return normalizeEmailProvider(($('emailProviderTop') || $('emailProvider') || {}).value || 'outlook_app');
}

function setEmailProviderValue(value) {
  const normalized = normalizeEmailProvider(value);
  for (const control of emailProviderControls()) control.value = normalized;
}

function syncEmailProviderFrom(source) {
  setEmailProviderValue(source.value);
  updateAndCalculate();
}

function payloadFromForm() {
  ensureTimelineDefaultsInForm();
  return {
    projectTitle: $('projectTitle').value || 'Feature Film',
    asOfDate: $('asOfDate').value,
    productionLocation: $('productionLocation').value || 'US',
    anchorMode: $('anchorMode').value || 'auto',
    emailProvider: getEmailProviderValue(),
    coordinatorSummary: buildCoordinatorSummary(),
    lastEditedAnchor: loadState().lastEditedAnchor || 'production',
    periods: {
      rd: { start: $('rdStart').value, weeks: Number($('rdWeeks').value || 0) },
      pre: { start: $('preStart').value, weeks: durationOrDefault('preWeeks', 12) },
      travel: { start: $('travelStart').value, weeks: Number($('travelWeeks').value || 0) },
      production: { start: $('productionStart').value, days: Number($('productionDays').value || 0) },
      hiatus: { start: $('hiatusStart').value, end: $('hiatusEnd').value },
      post: { start: $('postStart').value, weeks: durationOrDefault('postWeeks', 26) },
      print_ship: { start: $('printShipStart').value, weeks: durationOrDefault('printShipWeeks', 4) },
      ready: { date: $('readyDate').value }
    },
    customRanges: loadCustomRanges()
  };
}

function setFormFromState(s) {
  $('projectTitle').value = s.projectTitle || 'Feature Film';
  $('asOfDate').value = s.asOfDate || '';
  $('productionLocation').value = s.productionLocation || 'US';
  $('anchorMode').value = s.anchorMode || 'auto';
  setEmailProviderValue(s.emailProvider || 'outlook_app');
  $('rdStart').value = s.periods.rd.start || '';
  $('rdWeeks').value = s.periods.rd.weeks ?? 0;
  $('preStart').value = s.periods.pre.start || '';
  $('preWeeks').value = valueOrPositiveDefault(s.periods.pre.weeks, 12);
  $('travelStart').value = s.periods.travel.start || '';
  $('travelWeeks').value = s.periods.travel.weeks ?? 0;
  $('productionStart').value = s.periods.production.start || '';
  $('productionDays').value = s.periods.production.days ?? 45;
  $('hiatusStart').value = s.periods.hiatus.start || '';
  $('hiatusEnd').value = s.periods.hiatus.end || '';
  $('postStart').value = s.periods.post.start || '';
  $('postWeeks').value = valueOrPositiveDefault(s.periods.post.weeks, 26);
  $('printShipStart').value = s.periods.print_ship.start || '';
  $('printShipWeeks').value = valueOrPositiveDefault(s.periods.print_ship.weeks, 4);
  $('readyDate').value = s.periods.ready.date || '';
}

function updateAndCalculate() {
  const payload = payloadFromForm();
  const current = loadState();
  payload.lastEditedAnchor = current.lastEditedAnchor || 'production';
  saveState(payload);
  clearTimeout(timer);
  timer = setTimeout(calculate, 160);
}

async function calculate() {
  const payload = payloadFromForm();
  payload.lastEditedAnchor = loadState().lastEditedAnchor || 'production';
  setBusy(true);
  try {
    const res = await fetch('/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.error || 'Schedule failed');
    lastSchedule = data;
    if (!activeYear || !(data.years || []).includes(activeYear)) activeYear = (data.years || [new Date().getFullYear()])[0];
    renderSchedule(data);
  } catch (e) {
    $('messages').innerHTML = `<div class="message warn">${escapeHtml(e.message)}</div>`;
  } finally {
    setBusy(false);
  }
}

function setBusy(busy) {
  for (const id of ['calculateBtn', 'excelBtn', 'pdfBtn', 'emailBtn']) $(id).disabled = !!busy;
}

function renderSchedule(data) {
  syncCalculatedStartsToForm(data);
  if ($('buildBadge')) $('buildBadge').textContent = data.buildVersion || buildVersion;
  const projectTitle = data.projectTitle || 'Feature Film';
  $('pageTitle').textContent = projectTitle;
  $('calendarTitle').textContent = `${projectTitle} Calendar`;
  $('calendarSubtitle').textContent = `${data.productionLocationLabel || 'United States'} holidays extend Production. Phases use Monday-Friday workweeks and hand off on the following Monday by default.`;
  renderMessages(data);
  renderYearChips(data);
  renderStats(data);
  renderPhaseLegend(data);
  renderSummary(data);
  renderCustomRangeList(data);
  renderCalendar(data, activeYear);
  renderHolidayList(data, activeYear);
  if (selectedDayRow?.date) {
    const updated = (data.dayRows || []).find(r => r.date === selectedDayRow.date);
    if (updated) renderDayDetail(updated);
  }
}

function renderMessages(data) {
  const messages = [];
  if (data.needsInput) messages.push(`<div class="message info">${escapeHtml(data.message || 'Enter a date to start.')}</div>`);
  for (const w of data.warnings || []) messages.push(`<div class="message warn">${escapeHtml(w)}</div>`);
  for (const n of data.notes || []) messages.push(`<div class="message note">${escapeHtml(n)}</div>`);
  $('messages').innerHTML = messages.join('');
}


function renderYearChips(data) {
  const years = data.years || [new Date().getFullYear()];
  $('yearChips').innerHTML = years.map(y => `<button class="${y === activeYear ? 'active' : ''}" data-year="${y}" aria-pressed="${y === activeYear ? 'true' : 'false'}">${y}</button>`).join('');
  $('yearChips').querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      activeYear = Number(btn.dataset.year);
      renderSchedule(lastSchedule);
    });
  });
}

function renderStats(data) {
  const production = (data.periods || []).find(p => p.key === 'production');
  const post = (data.periods || []).find(p => p.key === 'post');
  const ready = data.ready || {};
  const years = (data.years || []).join(' - ') || '—';
  const shootDays = production?.metric?.value ?? Number($('productionDays').value || 0);
  const holidayExt = production?.metric?.skippedHolidays ?? 0;
  const postWeeks = post?.metric?.value ?? durationOrDefault('postWeeks', 26);
  const cards = [
    ['Ready', ready.displayDate || 'Not set', 'Release milestone'],
    ['Shoot days', shootDays ? `${shootDays}` : '0', `${holidayExt} holiday extension day${holidayExt === 1 ? '' : 's'}`],
    ['Post', postWeeks ? `${postWeeks} weeks` : '0 weeks', 'Workweek basis'],
    ['Years', years, data.productionLocationLabel || 'United States']
  ];
  $('statsGrid').innerHTML = cards.map(([label, value, sub]) => `<div class="stat-card"><div class="stat-label">${escapeHtml(label)}</div><div class="stat-value">${escapeHtml(value)}</div><div class="stat-sub">${escapeHtml(sub)}</div></div>`).join('');
}

function renderPhaseLegend(data) {
  const activeKeys = new Set((data.periods || []).map(p => p.key));
  if (data.ready?.displayDate) activeKeys.add('ready');
  const order = ['rd', 'pre', 'travel', 'production', 'hiatus', 'post', 'print_ship', 'ready'];
  const chips = order.filter(key => activeKeys.has(key)).map(key => {
    const meta = periodMeta[key];
    return `<span class="legend-chip"><span class="legend-dot" style="background:${meta.color}"></span>${escapeHtml(meta.label)}</span>`;
  });
  $('phaseLegend').innerHTML = chips.join('');
}

function renderSummary(data) {
  const metaRows = [
    ['Location', data.productionLocationLabel || ''],
    ['Anchor', data.anchorLabel || ''],
  ];
  if (data.ready && data.ready.displayDate) metaRows.push(['Ready', data.ready.displayDate]);
  const metaHtml = `<div class="summary-meta">${metaRows.map(([label, value]) => `<div class="summary-meta-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('')}</div>`;
  const periodHtml = (data.periods || []).map(p => {
    const metric = p.metric || {};
    let metricText = '';
    if (metric.type === 'weeks') metricText = `${metric.value} weeks`;
    if (metric.type === 'workdays') metricText = `${metric.value} shoot days; ${metric.skippedHolidays || 0} holiday extension day(s)`;
    if (metric.type === 'date_range') metricText = 'single date range';
    const meta = periodMeta[p.key] || { color: `#${p.color}`, label: p.label };
    const textColor = meta.text ? `color:${meta.text};` : '';
    return `<div class="summary-item">
      <span class="summary-swatch" style="background:${meta.color};${textColor}"></span>
      <div>
        <div class="summary-title">${escapeHtml(p.label)}</div>
        <div class="summary-dates">${escapeHtml(p.displayStart)} - ${escapeHtml(p.displayEnd)}</div>
        <div class="summary-metric">${escapeHtml(metricText)}</div>
      </div>
    </div>`;
  }).join('');
  $('summary').innerHTML = `${metaHtml}<div class="summary-list">${periodHtml || '<div class="summary-meta-row"><span>No phases yet</span><strong>Enter an anchor date</strong></div>'}</div>`;
}

function renderCalendar(data, year) {
  const rowsByDate = new Map((data.dayRows || []).map(r => [r.date, r]));
  const months = [];
  for (let m = 0; m < 12; m++) months.push(renderMonth(year, m, rowsByDate));
  $('calendarGrid').innerHTML = months.join('');
  $('calendarGrid').querySelectorAll('.day.has-data').forEach(el => {
    el.addEventListener('click', () => renderDayDetail(rowsByDate.get(el.dataset.date)));
    el.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        renderDayDetail(rowsByDate.get(el.dataset.date));
      }
    });
  });
}

function displayKeyForDay(keys, holidays) {
  // Priority is visual, not chronological: Ready > Hiatus/Holiday override > phase color.
  // Hiatus remains visible as an interruption even when it overlays Post, and
  // selected-location holidays override Production color.
  if (keys.includes('hiatus')) return 'hiatus';
  if (keys.includes('production') && (holidays || []).length) return 'hiatus';
  const priority = ['production_additional', 'print_ship', 'post', 'production', 'travel', 'pre', 'rd'];
  return priority.find(key => keys.includes(key)) || keys[keys.length - 1];
}

function renderMonth(year, monthIndex, rowsByDate) {
  const monthName = new Date(year, monthIndex, 1).toLocaleString(undefined, { month: 'long' });
  const first = new Date(year, monthIndex, 1);
  const startOffset = first.getDay();
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  let cells = '';
  for (let i = 0; i < startOffset; i++) cells += `<div class="day empty" aria-hidden="true"></div>`;
  for (let d = 1; d <= daysInMonth; d++) {
    const iso = toIso(year, monthIndex + 1, d);
    const row = rowsByDate.get(iso) || {};
    const keys = row.periodKeys || [];
    const ready = !!row.ready;
    const holidays = row.holidayNames || [];
    const weekend = row.isWeekend;
    const hasData = ready || keys.length || holidays.length;
    const productionNonWork = keys.includes('production') && !row.isProductionWorkday;
    let bg = '';
    let mini = '';
    let displayKey = '';
    if (ready) {
      bg = '#000000';
      mini = 'READY';
    } else if (keys.length) {
      displayKey = displayKeyForDay(keys, holidays);
      bg = periodMeta[displayKey]?.color || '#fff';
      mini = keys.map(k => periodMeta[k]?.label || k).join(' / ');
    } else if (holidays.length) {
      bg = '#d9ead3';
      mini = holidays[0];
    }
    const textColor = ready ? 'white' : (displayKey ? periodMeta[displayKey]?.text : '');
    const style = bg ? ` style="background:${bg};${textColor ? `color:${textColor};` : ''}"` : '';
    const aria = hasData ? `${row.displayDate || iso}: ${(row.periodLabels || []).concat(holidays).concat(ready ? ['Ready for Release'] : []).join(', ')}` : `${monthName} ${d}, ${year}`;
    cells += `<div class="day ${weekend ? 'weekend' : ''} ${hasData ? 'has-data' : ''} ${ready ? 'ready' : ''} ${productionNonWork ? 'production-nonwork' : ''}" data-date="${iso}" ${hasData ? 'role="button" tabindex="0"' : ''} aria-label="${escapeHtml(aria)}"${style}>
      <div class="num">${d}</div>
      ${holidays.length ? '<div class="holiday-dot" title="Holiday"></div>' : ''}
      ${mini ? `<div class="mini">${escapeHtml(mini)}</div>` : ''}
    </div>`;
  }
  const totalCells = startOffset + daysInMonth;
  for (let i = totalCells; i < 42; i++) cells += `<div class="day empty" aria-hidden="true"></div>`;
  return `<section class="month" aria-label="${escapeHtml(monthName)} ${year}">
    <div class="month-title"><span>${escapeHtml(monthName)}</span><span>${year}</span></div>
    <div class="weekdays"><div>Su</div><div>M</div><div>Tu</div><div>W</div><div>Th</div><div>F</div><div>Sa</div></div>
    <div class="days">${cells}</div>
  </section>`;
}

function renderHolidayList(data, year) {
  const holidays = (data.holidays || []).filter(h => Number(h.date.slice(0, 4)) === year);
  if (!holidays.length) {
    $('holidayList').innerHTML = '';
    return;
  }
  const rows = holidays.map(h => `<tr><td>${escapeHtml(h.displayDate)}</td><td>${escapeHtml(h.name)}</td><td>${escapeHtml(h.regionLabel)}</td><td>${h.observed ? 'Yes' : ''}</td></tr>`).join('');
  $('holidayList').innerHTML = `<h3>${year} selected-location holidays</h3><table class="holiday-table"><thead><tr><th>Date</th><th>Holiday</th><th>Region</th><th>Observed</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderDayDetail(row) {
  if (!row) return;
  selectedDayRow = row;
  setMode('form', false);
  const tags = [];
  for (const key of row.periodKeys || []) {
    const meta = periodMeta[key] || { color: '#eee', label: key };
    const textColor = meta.text ? `;color:${meta.text}` : '';
    tags.push(`<span class="tag" style="background:${meta.color}${textColor}">${escapeHtml(meta.label)}</span>`);
  }
  for (const h of row.holidayNames || []) tags.push(`<span class="tag" style="background:#d9ead3">${escapeHtml(h)}</span>`);
  if (row.ready) tags.push(`<span class="tag" style="background:#000;color:#fff">Ready for Release</span>`);
  const customForDay = (lastSchedule?.customRanges || []).filter(r => r.start <= row.date && row.date <= r.end);
  const selectedDisplay = row.displayDate || isoToDisplay(row.date);
  $('dayDetail').innerHTML = `<div class="detail-date">${escapeHtml(selectedDisplay)}</div>
    <div>${escapeHtml(row.weekday || '')}</div>
    <div class="detail-tags">${tags.join('') || '<span class="tag">No period/holiday</span>'}</div>
    ${row.periodKeys?.includes('production') || row.periodKeys?.includes('production_additional') ? `<p><b>Production workday:</b> ${row.isProductionWorkday ? 'Yes' : 'No'}</p>` : ''}
    <form id="dayOverrideForm" class="day-override-form">
      <div class="day-override-title">Change this day or range</div>
      <p class="hint">Use this for reshoots, additional photography, special travel/prep windows, or temporary phase changes. These are overlays; downstream Post continues unless you edit the main phase dates.</p>
      <div class="field-row">
        <label class="field">Start date <input id="overrideStart" type="text" inputmode="numeric" value="${escapeHtml(selectedDisplay)}"></label>
        <label class="field">End date <input id="overrideEnd" type="text" inputmode="numeric" value="${escapeHtml(selectedDisplay)}"></label>
      </div>
      <label class="field full">Change to period
        <select id="overridePeriod">
          <option value="production_additional">Production (Additional Photography)</option>
          <option value="production">Production</option>
          <option value="pre">Pre-Production</option>
          <option value="travel">Travel/Prep</option>
          <option value="post">Post Production</option>
          <option value="print_ship">Print & Ship</option>
          <option value="hiatus">Hiatus</option>
          <option value="rd">R&D</option>
        </select>
      </label>
      <label class="field full">Note <input id="overrideNote" type="text" placeholder="Additional photography / reshoot / special unit" autocomplete="off"></label>
      <div class="override-actions">
        <button id="applyOverrideBtn" type="button" class="button primary compact-button">Apply Range</button>
        <button id="clearOverridesForDayBtn" type="button" class="button soft compact-button">Clear Overrides for Day</button>
      </div>
    </form>
    ${customForDay.length ? `<div class="override-current"><strong>Manual override on this date</strong>${customForDay.map(r => `<div>${escapeHtml(r.label)}: ${escapeHtml(r.displayStart)} - ${escapeHtml(r.displayEnd)}${r.note ? ` · ${escapeHtml(r.note)}` : ''}</div>`).join('')}</div>` : ''}`;
  $('applyOverrideBtn')?.addEventListener('click', applyDayOverrideFromInspector);
  $('clearOverridesForDayBtn')?.addEventListener('click', () => clearOverridesForDate(row.date));
}

function isoToDisplay(isoDate) {
  if (!isoDate) return '';
  const [y, m, d] = String(isoDate).split('-');
  if (!y || !m || !d) return isoDate;
  return `${m}/${d}/${String(y).slice(2)}`;
}

function displayToIso(value) {
  const normalized = normalizeDateInput(value);
  const parts = normalized.split('/');
  if (parts.length !== 3) return '';
  const mm = parts[0].padStart(2, '0');
  const dd = parts[1].padStart(2, '0');
  const yy = parts[2].length === 2 ? `20${parts[2]}` : parts[2];
  if (!/^\d{4}$/.test(yy) || !/^\d{2}$/.test(mm) || !/^\d{2}$/.test(dd)) return '';
  return `${yy}-${mm}-${dd}`;
}

function loadCustomRanges() {
  const state = loadState();
  return Array.isArray(state.customRanges) ? state.customRanges : [];
}

function saveCustomRanges(customRanges) {
  const state = loadState();
  state.customRanges = customRanges;
  saveState(state);
}

function applyDayOverrideFromInspector() {
  const startDisplay = normalizeDateInput($('overrideStart')?.value || '');
  const endDisplay = normalizeDateInput($('overrideEnd')?.value || startDisplay);
  const startIso = displayToIso(startDisplay);
  const endIso = displayToIso(endDisplay || startDisplay);
  if (!startIso || !endIso) return showTransient('Enter a valid override start and end date.', true);
  const periodKey = $('overridePeriod')?.value || 'production_additional';
  const meta = periodMeta[periodKey] || periodMeta.production_additional;
  const note = ($('overrideNote')?.value || '').trim();
  const customRanges = loadCustomRanges();
  const item = {
    id: `manual-${Date.now()}`,
    start: startIso <= endIso ? startIso : endIso,
    end: endIso >= startIso ? endIso : startIso,
    displayStart: isoToDisplay(startIso <= endIso ? startIso : endIso),
    displayEnd: isoToDisplay(endIso >= startIso ? endIso : startIso),
    periodKey,
    label: meta.label,
    color: meta.color,
    note,
    source: 'day-inspector'
  };
  customRanges.push(item);
  saveCustomRanges(customRanges);
  showTransient(`Applied ${item.label} from ${item.displayStart} to ${item.displayEnd}.`);
  updateAndCalculate();
}

function clearOverridesForDate(isoDate) {
  if (!isoDate) return;
  const before = loadCustomRanges();
  const after = before.filter(r => !(r.start <= isoDate && isoDate <= r.end));
  saveCustomRanges(after);
  showTransient(before.length === after.length ? 'No manual overrides were found for that date.' : 'Cleared manual override(s) for the selected day.');
  updateAndCalculate();
}

function removeCustomRange(id) {
  saveCustomRanges(loadCustomRanges().filter(r => r.id !== id));
  updateAndCalculate();
}

function renderCustomRangeList(data) {
  const target = $('customRangeList');
  if (!target) return;
  const ranges = data?.customRanges || [];
  if (!ranges.length) {
    target.innerHTML = '<p class="hint">No manual day overrides yet. Select a calendar day to add additional photography, reshoots, or special phase ranges.</p>';
    return;
  }
  target.innerHTML = ranges.map(r => `<div class="custom-range-row">
    <span class="summary-swatch" style="background:${escapeHtml(r.color || '#5b9bd5')}"></span>
    <div><strong>${escapeHtml(r.label)}</strong><span>${escapeHtml(r.displayStart)} - ${escapeHtml(r.displayEnd)}${r.note ? ` · ${escapeHtml(r.note)}` : ''}</span></div>
    <button type="button" class="text-button" data-remove-custom-range="${escapeHtml(r.id || '')}">Remove</button>
  </div>`).join('');
  target.querySelectorAll('[data-remove-custom-range]').forEach(btn => {
    btn.addEventListener('click', () => removeCustomRange(btn.dataset.removeCustomRange));
  });
}

function toIso(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

async function exportFile(endpoint, expectedExt) {
  const payload = payloadFromForm();
  payload.lastEditedAnchor = loadState().lastEditedAnchor || 'production';
  setBusy(true);
  try {
    const res = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.error || 'Export failed');
    if (expectedExt && !String(data.filename || '').toLowerCase().endsWith(expectedExt)) {
      throw new Error(`Export returned ${data.filename || 'a file'}, but ${expectedExt} was expected.`);
    }
    const fileRes = await fetch(data.downloadUrl, { cache: 'no-store' });
    if (!fileRes.ok) throw new Error('The export was created but could not be downloaded.');
    const blob = await fileRes.blob();
    if (expectedExt === '.pdf') {
      const isPdfType = !blob.type || blob.type.includes('pdf');
      if (!isPdfType) throw new Error('The PDF button did not receive a PDF file.');
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = data.filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    showTransient(`Created ${data.filename}`);
  } catch (e) {
    showTransient(e.message, true);
  } finally {
    setBusy(false);
  }
}

function isLikelyMobileAppleDevice() {
  const ua = navigator.userAgent || '';
  return /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}

function launchEmailClient(data) {
  const provider = getEmailProviderValue();
  const mailto = data.mailto || data.fallbackEmailUrl || data.emailUrl;
  const outlookMobile = data.outlookMobileUrl || data.emailUrl;
  if (!mailto && !outlookMobile) return;

  // Reliable rule:
  // - Mac/desktop: use mailto. That opens Outlook when Outlook is set as the
  //   device's default email reader, and avoids the failed temp/web Outlook flow.
  // - iPhone/iPad: try Outlook's app scheme only when Outlook App is selected;
  //   fall back to the system mailto handler so the user still gets a draft.
  // The app's own default is Outlook App, but the operating system still owns
  // which native client handles mailto links.
  if (provider === 'outlook_app' && isLikelyMobileAppleDevice() && outlookMobile && outlookMobile.startsWith('ms-outlook://')) {
    let didHide = false;
    const onVisibility = () => { if (document.hidden) didHide = true; };
    document.addEventListener('visibilitychange', onVisibility, { once: true });
    window.location.href = outlookMobile;
    window.setTimeout(() => {
      document.removeEventListener('visibilitychange', onVisibility);
      if (!didHide && mailto) {
        showTransient('Outlook did not open directly. Opening the device email handler instead. Set Outlook as your default email app to keep this in Outlook.');
        window.location.href = mailto;
      }
    }, 900);
    return;
  }

  if (provider === 'outlook_app') {
    showTransient('Opening Outlook through the system email handler. Make Outlook your default email app on this device for this option to open Outlook.');
  }
  window.location.href = mailto || outlookMobile;
}

async function emailDraft() {
  const payload = payloadFromForm();
  payload.lastEditedAnchor = loadState().lastEditedAnchor || 'production';
  payload.openMailtoOnServer = false;
  setBusy(true);
  try {
    const res = await fetch('/api/email', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.error || 'Email draft failed');
    const links = [];
    if (data.excel?.shareUrl || data.excel?.downloadUrl) links.push(`<a href="${data.excel.shareUrl || data.excel.downloadUrl}" target="_blank" rel="noopener">Excel link</a>`);
    if (data.pdf?.shareUrl || data.pdf?.downloadUrl) links.push(`<a href="${data.pdf.shareUrl || data.pdf.downloadUrl}" target="_blank" rel="noopener">PDF link</a>`);
    const clientLabel = getEmailProviderValue() === 'outlook_app' ? 'Outlook app' : 'Apple Mail / default mail app';
    showTransient((data.message || 'Email draft created.') + ` Opening ${clientLabel}.` + (links.length ? ' ' + links.join(' | ') : ''));
    launchEmailClient(data);
  } catch (e) {
    showTransient(e.message, true);
  } finally {
    setBusy(false);
  }
}

function showTransient(message, warn = false) {
  const div = document.createElement('div');
  div.className = `message ${warn ? 'warn' : 'note'}`;
  if (String(message).includes('<a ')) div.innerHTML = message;
  else div.textContent = message;
  $('messages').prepend(div);
  setTimeout(() => div.remove(), 10000);
}

function initTabs() {
  document.querySelectorAll('#toolbarTabs button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#toolbarTabs button').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.period-form').forEach(f => f.classList.remove('active'));
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      document.querySelector(`.period-form[data-form="${btn.dataset.tab}"]`).classList.add('active');
    });
  });
}

function bindInputs() {
  const ids = ['projectTitle', 'productionLocation', 'anchorMode', 'rdWeeks', 'preWeeks', 'travelWeeks', 'productionDays', 'postWeeks', 'printShipWeeks'];
  for (const id of ids) $(id).addEventListener('input', updateAndCalculate);
  emailProviderControls().forEach(control => control.addEventListener('change', () => syncEmailProviderFrom(control)));
  emailProviderControls().forEach(control => control.addEventListener('input', () => syncEmailProviderFrom(control)));
  $('asOfDate').addEventListener('change', () => { $('asOfDate').value = normalizeDateInput($('asOfDate').value); updateAndCalculate(); });
  $('asOfDate').addEventListener('blur', () => { $('asOfDate').value = normalizeDateInput($('asOfDate').value); updateAndCalculate(); });
  for (const el of document.querySelectorAll('[data-date-period]')) {
    el.addEventListener('focus', () => {
      const s = loadState();
      s.lastEditedAnchor = el.dataset.datePeriod;
      saveState(s);
    });
    el.addEventListener('change', () => {
      el.value = normalizeDateInput(el.value);
      const s = loadState();
      s.lastEditedAnchor = el.dataset.datePeriod;
      saveState(s);
      updateAndCalculate();
    });
    el.addEventListener('blur', () => {
      el.value = normalizeDateInput(el.value);
      updateAndCalculate();
    });
  }
  $('calculateBtn').addEventListener('click', calculate);
  $('excelBtn').addEventListener('click', () => exportFile('/api/export/excel', '.xlsx'));
  $('pdfBtn').addEventListener('click', () => exportFile('/api/export/pdf', '.pdf'));
  $('emailBtn').addEventListener('click', emailDraft);
  $('saveBtn').addEventListener('click', () => { saveState(payloadFromForm()); showTransient('Saved locally in this browser.'); });
  document.querySelectorAll('[data-mirror-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.mirrorAction;
      if (action === 'excel') $('excelBtn').click();
      if (action === 'pdf') $('pdfBtn').click();
      if (action === 'email') $('emailBtn').click();
    });
  });
  initModes();
  initAssistant();
  $('resetBtn').addEventListener('click', () => {
    if (!confirm('Reset this calendar?')) return;
    localStorage.removeItem(stateKey);
    localStorage.removeItem('producerCalendarTeamHostedStateV1');
    localStorage.removeItem(defaultsVersionKey);
    setFormFromState(structuredClone(defaults));
    activeYear = null;
    updateAndCalculate();
  });
}


function setMode(mode, scrollToPanel = true) {
  document.body.classList.remove('mode-form', 'mode-assistant', 'mode-preview');
  document.body.classList.add(`mode-${mode}`);
  document.querySelectorAll('.mode-button').forEach(button => {
    const active = button.dataset.mode === mode;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', active ? 'true' : 'false');
  });
  if (scrollToPanel) {
    const target = mode === 'assistant' ? $('aiAssistantSection') : mode === 'preview' ? document.querySelector('.calendar-panel') : $('projectSetupSection');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function initModes() {
  document.querySelectorAll('.mode-button').forEach(button => {
    button.addEventListener('click', () => setMode(button.dataset.mode || 'form'));
  });
  setMode('form', false);
}


const assistantQuestions = [
  { key: 'projectTitle', prompt: 'What is the project title?', field: 'projectTitle' },
  { key: 'asOfDate', prompt: 'What as-of date should appear on the calendar? Use mm/dd/yy.', field: 'asOfDate', normalize: true },
  { key: 'productionLocation', prompt: 'Where are we shooting for holiday rules: United States, New York, Canada, United Kingdom, or Mexico?', field: 'productionLocation', map: mapLocationAnswer },
  { key: 'anchorMode', prompt: 'What is the scheduling anchor? I can work from Production start or Ready for Release.', field: 'anchorMode', map: mapAnchorAnswer },
  { key: 'productionStart', prompt: 'What is the Production start date? Use mm/dd/yy. Type skip if you are anchoring by release.', field: 'productionStart', normalize: true, allowSkip: true },
  { key: 'productionDays', prompt: 'How many Production shoot days? Default is 45. Weekends are excluded.', field: 'productionDays', number: true },
  { key: 'preWeeks', prompt: 'How many weeks of Pre-Production? Default is 12.', field: 'preWeeks', number: true },
  { key: 'hiatus', prompt: 'Any single hiatus range? Say none, or enter start and end dates like 12/20/26 to 01/02/27. The next phase still begins the Monday after the previous period; hiatus is shown as an overlay and does not suppress Post.', field: 'hiatus', hiatus: true },
  { key: 'postWeeks', prompt: 'How many weeks of Post Production? Default is 26.', field: 'postWeeks', number: true },
  { key: 'printShipWeeks', prompt: 'How many weeks for Print & Ship? Default is 4.', field: 'printShipWeeks', number: true },
  { key: 'readyDate', prompt: 'Ready for Release defaults to the last Friday inside Print & Ship. Enter a release date only if you want to override it, or type skip.', field: 'readyDate', normalize: true, allowSkip: true },
  { key: 'emailProvider', prompt: 'Which email client should the draft use? Outlook App is the default, or say Apple Mail if needed.', field: 'emailProvider', map: mapEmailAnswer }
];

function initAssistant() {
  const send = $('assistantSend');
  const input = $('assistantInput');
  if (!send || !input) return;
  assistantStep = 0;
  assistantAdd('coordinator', 'I can guide intake without replacing the form. Answer in short phrases; I will populate the structured fields and keep everything editable. Phase handoffs default to the following Monday; Hiatus is an overlay, not a gate.');
  assistantAdd('coordinator', assistantQuestions[assistantStep].prompt);
  send.addEventListener('click', handleAssistantSend);
  input.addEventListener('keydown', event => { if (event.key === 'Enter') handleAssistantSend(); });
  document.querySelectorAll('[data-assistant-preset]').forEach(button => {
    button.addEventListener('click', () => assistantPreset(button.dataset.assistantPreset));
  });
}

function assistantAdd(type, text) {
  const log = $('assistantLog');
  if (!log) return;
  const div = document.createElement('div');
  div.className = `assistant-message ${type}`;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function assistantPreset(kind) {
  setMode('assistant', false);
  if (kind === 'production') {
    $('anchorMode').value = 'production';
    assistantStep = 4;
    assistantAdd('callout', 'Production-start scenario selected. I will prioritize production start, shoot days, and downstream delivery.');
  } else if (kind === 'release') {
    $('anchorMode').value = 'ready';
    assistantStep = 10;
    assistantAdd('callout', 'Release-backward scenario selected. I will use the release date as the anchor.');
  } else {
    explainCurrentSchedule();
    return;
  }
  updateAndCalculate();
  assistantAdd('coordinator', assistantQuestions[assistantStep].prompt);
}

function handleAssistantSend() {
  const input = $('assistantInput');
  const answer = (input.value || '').trim();
  if (!answer) return;
  input.value = '';
  assistantAdd('user', answer);
  const lower = answer.toLowerCase();
  if (lower.includes('explain') || lower.includes('conflict') || lower.includes('why') || lower.includes('review')) {
    explainCurrentSchedule();
    return;
  }
  const q = assistantQuestions[assistantStep] || assistantQuestions[assistantQuestions.length - 1];
  applyAssistantAnswer(q, answer);
  assistantStep = Math.min(assistantStep + 1, assistantQuestions.length - 1);
  updateAndCalculate();
  const next = assistantQuestions[assistantStep];
  if (assistantStep >= assistantQuestions.length - 1) {
    assistantAdd('coordinator', 'I have the core scenario. Review the form fields, then Calculate, Export Excel, Export PDF, or Draft Email.');
  } else {
    assistantAdd('coordinator', next.prompt);
  }
}

function applyAssistantAnswer(q, answer) {
  if (!q || !q.field) return;
  const lower = answer.toLowerCase();
  if (q.allowSkip && /^(skip|none|no|n\/a)$/i.test(answer.trim())) {
    assistantAdd('callout', 'Skipped. The field remains editable if you need to add it later.');
    return;
  }
  if (q.hiatus) {
    if (/^(none|no|skip|n\/a)$/i.test(answer.trim())) {
      $('hiatusStart').value = '';
      $('hiatusEnd').value = '';
      assistantAdd('callout', 'No hiatus captured.');
      return;
    }
    const dates = extractDates(answer);
    if (dates[0]) $('hiatusStart').value = dates[0];
    if (dates[1]) $('hiatusEnd').value = dates[1];
    assistantAdd('callout', dates.length >= 2 ? `Captured hiatus ${dates[0]} to ${dates[1]}. Post will still begin on the Monday after Production by default; the hiatus will overlay that downstream schedule.` : 'I need two dates for hiatus; you can edit them in the form.');
    return;
  }
  let value = answer;
  if (q.number) {
    const match = answer.match(/\d+/);
    value = match ? match[0] : '';
  }
  if (q.normalize) value = normalizeDateInput(extractDates(answer)[0] || answer);
  if (q.map) value = q.map(answer);
  if (value !== undefined && value !== null && value !== '') {
    if (q.field === 'emailProvider') setEmailProviderValue(value);
    else $(q.field).value = value;
    if (q.field === 'productionStart') markAnchor('production');
    if (q.field === 'readyDate') markAnchor('ready');
    assistantAdd('callout', `Captured ${fieldLabel(q.field)}: ${$(q.field).tagName === 'SELECT' ? $(q.field).selectedOptions[0].textContent : value}`);
  } else {
    assistantAdd('callout', 'I could not confidently capture that. The field remains editable in the form.');
  }
}

function markAnchor(anchor) {
  const s = loadState();
  s.lastEditedAnchor = anchor;
  saveState(s);
}

function extractDates(text) {
  const matches = String(text).match(/\b\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}\b/g) || [];
  return matches.map(normalizeDateInput);
}

function mapLocationAnswer(answer) {
  const a = answer.toLowerCase();
  if (a.includes('new york') || a === 'ny') return 'NY';
  if (a.includes('canada') || a === 'ca') return 'CA';
  if (a.includes('kingdom') || a.includes('uk') || a.includes('london')) return 'UK';
  if (a.includes('mexico') || a === 'mx') return 'MX';
  return 'US';
}

function mapAnchorAnswer(answer) {
  const a = answer.toLowerCase();
  if (a.includes('release') || a.includes('ready')) return 'ready';
  if (a.includes('pre')) return 'pre';
  if (a.includes('post')) return 'post';
  if (a.includes('print')) return 'print_ship';
  if (a.includes('travel')) return 'travel';
  if (a.includes('hiatus')) return 'hiatus';
  if (a.includes('r&d') || a.includes('research')) return 'rd';
  return 'production';
}

function mapEmailAnswer(answer) {
  const a = answer.toLowerCase();
  if (a.includes('outlook') || a.includes('office') || a.includes('365')) return 'outlook_app';
  return 'apple_mail';
}

function fieldLabel(field) {
  const labels = {
    projectTitle: 'project title', asOfDate: 'as-of date', productionLocation: 'location', anchorMode: 'anchor', productionStart: 'production start', productionDays: 'shoot days', preWeeks: 'pre-production weeks', postWeeks: 'post weeks', printShipWeeks: 'print & ship weeks', readyDate: 'ready date', emailProvider: 'email provider'
  };
  return labels[field] || field;
}

function explainCurrentSchedule() {
  if (!lastSchedule) {
    assistantAdd('coordinator', 'Calculate a schedule first, and I will explain the assumptions and conflicts.');
    return;
  }
  const production = (lastSchedule.periods || []).find(p => p.key === 'production');
  const holidayExt = production?.metric?.skippedHolidays || 0;
  const pieces = [];
  pieces.push(`Anchor: ${lastSchedule.anchorLabel || 'not set'}.`);
  if (production) pieces.push(`Production runs ${production.displayStart} to ${production.displayEnd}; ${production.metric?.value || 0} shoot days, extended by ${holidayExt} holiday day${holidayExt === 1 ? '' : 's'}.`);
  if (lastSchedule.ready?.displayDate) pieces.push(`Ready for Release: ${lastSchedule.ready.displayDate}.`);
  if ((lastSchedule.warnings || []).length) pieces.push(`Needs review: ${lastSchedule.warnings.join(' ')}`);
  assistantAdd('coordinator', pieces.join(' '));
}

async function loadServerInfo() {
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    $('serverInfo').textContent = data.message || 'Secure hosted team app. Add this URL to the iPhone/iPad Home Screen from Safari.'; if ($('buildBadge')) $('buildBadge').textContent = data.buildVersion || buildVersion;
  } catch (e) {
    $('serverInfo').textContent = 'Secure hosted app is running.';
  }
}

function boot() {
  initTheme();
  setFormFromState(loadState());
  ensureTimelineDefaultsInForm();
  initTabs();
  bindInputs();
  loadServerInfo();
  calculate();
}

document.addEventListener('DOMContentLoaded', boot);
