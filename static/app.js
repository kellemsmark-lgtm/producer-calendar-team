const periodMeta = {
  rd: { label: 'R&D', color: '#f4b183' },
  pre: { label: 'Pre-Production', color: '#fff26b' },
  travel: { label: 'Travel/Prep', color: '#d2b48c' },
  production: { label: 'Production', color: '#5b9bd5' },
  hiatus: { label: 'Hiatus', color: '#e7a1c4' },
  post: { label: 'Post Production', color: '#e06666' },
  print_ship: { label: 'Print & Ship', color: '#70ad47' },
  ready: { label: 'Ready for Release', color: '#000000', text: '#ffffff' }
};

const stateKey = 'producerCalendarTeamHostedStateV2';
let activeYear = null;
let lastSchedule = null;
let timer = null;

const defaults = {
  projectTitle: 'Feature Film',
  asOfDate: '',
  productionLocation: 'US',
  anchorMode: 'auto',
  emailProvider: 'system',
  lastEditedAnchor: 'production',
  periods: {
    rd: { start: '', weeks: 0 },
    pre: { start: '', weeks: 8 },
    travel: { start: '', weeks: 0 },
    production: { start: '', days: 45 },
    hiatus: { start: '', end: '' },
    post: { start: '', weeks: 12 },
    print_ship: { start: '', weeks: 2 },
    ready: { date: '' }
  }
};

function $(id) { return document.getElementById(id); }

function loadState() {
  try {
    const raw = localStorage.getItem(stateKey) || localStorage.getItem('producerCalendarTeamHostedStateV1');
    if (!raw) return structuredClone(defaults);
    return deepMerge(structuredClone(defaults), JSON.parse(raw));
  } catch (e) {
    return structuredClone(defaults);
  }
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

function normalizeDateInput(value) {
  value = (value || '').trim();
  if (!value) return '';
  const digits = value.replace(/\D/g, '');
  if (digits.length === 6) return `${digits.slice(0,2)}/${digits.slice(2,4)}/${digits.slice(4,6)}`;
  if (digits.length === 8) return `${digits.slice(0,2)}/${digits.slice(2,4)}/${digits.slice(6,8)}`;
  return value;
}

function payloadFromForm() {
  return {
    projectTitle: $('projectTitle').value || 'Feature Film',
    asOfDate: $('asOfDate').value,
    productionLocation: $('productionLocation').value || 'US',
    anchorMode: $('anchorMode').value || 'auto',
    emailProvider: $('emailProvider').value || 'system',
    lastEditedAnchor: loadState().lastEditedAnchor || 'production',
    periods: {
      rd: { start: $('rdStart').value, weeks: Number($('rdWeeks').value || 0) },
      pre: { start: $('preStart').value, weeks: Number($('preWeeks').value || 0) },
      travel: { start: $('travelStart').value, weeks: Number($('travelWeeks').value || 0) },
      production: { start: $('productionStart').value, days: Number($('productionDays').value || 0) },
      hiatus: { start: $('hiatusStart').value, end: $('hiatusEnd').value },
      post: { start: $('postStart').value, weeks: Number($('postWeeks').value || 0) },
      print_ship: { start: $('printShipStart').value, weeks: Number($('printShipWeeks').value || 0) },
      ready: { date: $('readyDate').value }
    }
  };
}

function setFormFromState(s) {
  $('projectTitle').value = s.projectTitle || 'Feature Film';
  $('asOfDate').value = s.asOfDate || '';
  $('productionLocation').value = s.productionLocation || 'US';
  $('anchorMode').value = s.anchorMode || 'auto';
  $('emailProvider').value = s.emailProvider || 'system';
  $('rdStart').value = s.periods.rd.start || '';
  $('rdWeeks').value = s.periods.rd.weeks ?? 0;
  $('preStart').value = s.periods.pre.start || '';
  $('preWeeks').value = s.periods.pre.weeks ?? 8;
  $('travelStart').value = s.periods.travel.start || '';
  $('travelWeeks').value = s.periods.travel.weeks ?? 0;
  $('productionStart').value = s.periods.production.start || '';
  $('productionDays').value = s.periods.production.days ?? 45;
  $('hiatusStart').value = s.periods.hiatus.start || '';
  $('hiatusEnd').value = s.periods.hiatus.end || '';
  $('postStart').value = s.periods.post.start || '';
  $('postWeeks').value = s.periods.post.weeks ?? 12;
  $('printShipStart').value = s.periods.print_ship.start || '';
  $('printShipWeeks').value = s.periods.print_ship.weeks ?? 2;
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
  const projectTitle = data.projectTitle || 'Feature Film';
  $('pageTitle').textContent = projectTitle;
  $('calendarTitle').textContent = `${projectTitle} Calendar`;
  $('calendarSubtitle').textContent = `${data.productionLocationLabel || 'United States'} holidays extend Production. All phases use Monday-Friday workweeks.`;
  renderMessages(data);
  renderYearChips(data);
  renderStats(data);
  renderPhaseLegend(data);
  renderSummary(data);
  renderCalendar(data, activeYear);
  renderHolidayList(data, activeYear);
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
  const postWeeks = post?.metric?.value ?? Number($('postWeeks').value || 0);
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
    if (ready) {
      bg = '#000000';
      mini = 'READY';
    } else if (keys.length) {
      const key = keys[keys.length - 1];
      bg = periodMeta[key]?.color || '#fff';
      mini = keys.map(k => periodMeta[k]?.label || k).join(' / ');
    } else if (holidays.length) {
      bg = '#d9ead3';
      mini = holidays[0];
    }
    const textColor = ready ? 'white' : (keys.length ? periodMeta[keys[keys.length - 1]]?.text : '');
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
  const tags = [];
  for (const key of row.periodKeys || []) {
    const meta = periodMeta[key] || { color: '#eee', label: key };
    const textColor = meta.text ? `;color:${meta.text}` : '';
    tags.push(`<span class="tag" style="background:${meta.color}${textColor}">${escapeHtml(meta.label)}</span>`);
  }
  for (const h of row.holidayNames || []) tags.push(`<span class="tag" style="background:#d9ead3">${escapeHtml(h)}</span>`);
  if (row.ready) tags.push(`<span class="tag" style="background:#000;color:#fff">Ready for Release</span>`);
  $('dayDetail').innerHTML = `<div class="detail-date">${escapeHtml(row.displayDate)}</div>
    <div>${escapeHtml(row.weekday || '')}</div>
    <div class="detail-tags">${tags.join('') || '<span class="tag">No period/holiday</span>'}</div>
    ${row.periodKeys?.includes('production') ? `<p><b>Production workday:</b> ${row.isProductionWorkday ? 'Yes' : 'No'}</p>` : ''}`;
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
    showTransient((data.message || 'Email draft created.') + (links.length ? ' ' + links.join(' | ') : ''));
    if (data.emailUrl || data.mailto) window.location.href = data.emailUrl || data.mailto;
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
  const ids = ['projectTitle', 'productionLocation', 'anchorMode', 'emailProvider', 'rdWeeks', 'preWeeks', 'travelWeeks', 'productionDays', 'postWeeks', 'printShipWeeks'];
  for (const id of ids) $(id).addEventListener('input', updateAndCalculate);
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
  $('resetBtn').addEventListener('click', () => {
    if (!confirm('Reset this calendar?')) return;
    localStorage.removeItem(stateKey);
    localStorage.removeItem('producerCalendarTeamHostedStateV1');
    setFormFromState(structuredClone(defaults));
    activeYear = null;
    updateAndCalculate();
  });
}

async function loadServerInfo() {
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    $('serverInfo').textContent = data.message || 'Secure hosted team app. Add this URL to the iPhone/iPad Home Screen from Safari.';
  } catch (e) {
    $('serverInfo').textContent = 'Secure hosted app is running.';
  }
}

function boot() {
  setFormFromState(loadState());
  initTabs();
  bindInputs();
  loadServerInfo();
  calculate();
}

document.addEventListener('DOMContentLoaded', boot);
