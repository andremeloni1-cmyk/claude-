const JOBS_KEY = "jsd_jobs";
const SETTINGS_KEY = "jsd_settings";

const DEFAULT_SETTINGS = {
  businessName: "Andre Meloni Photography",
  yourName: "Andre",
  yourEmail: "andre@andremeloniphotography.co",
  yourPhone: "",
  googleClientId: "",
  googleAutoSync: false,
};

const STATUS_LABELS = {
  inquiry: "Inquiry",
  booked: "Booked",
  completed: "Completed",
};

let jobs = [];
let settings = { ...DEFAULT_SETTINGS };
let viewDate = new Date();
let selectedDateStr = null;

// ---------- Storage ----------

function loadJobs() {
  const raw = localStorage.getItem(JOBS_KEY);
  if (raw) {
    try {
      jobs = JSON.parse(raw);
      return;
    } catch (e) {
      // fall through to seed data
    }
  }
  jobs = seedJobs();
  saveJobs();
}

function saveJobs() {
  localStorage.setItem(JOBS_KEY, JSON.stringify(jobs));
}

function loadSettings() {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (raw) {
    try {
      settings = { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
      return;
    } catch (e) {
      // fall through to defaults
    }
  }
  settings = { ...DEFAULT_SETTINGS };
}

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function seedJobs() {
  const addDays = (n) => {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return formatDateStr(d.getFullYear(), d.getMonth(), d.getDate());
  };

  return [
    {
      id: uid(),
      clientName: "Sarah & Tom",
      jobType: "Wedding",
      date: addDays(6),
      time: "14:00",
      location: "Riverside Gardens",
      status: "booked",
      email: "sarah.tom@example.com",
      price: "2500",
      notes: "Full day coverage, second shooter requested.",
    },
    {
      id: uid(),
      clientName: "Johnson Family",
      jobType: "Family",
      date: addDays(4),
      time: "10:00",
      location: "Sunset Park",
      status: "inquiry",
      email: "mjohnson@example.com",
      price: "",
      notes: "Asked about mini-session pricing.",
    },
    {
      id: uid(),
      clientName: "Emily Carter",
      jobType: "Engagement",
      date: addDays(13),
      time: "17:30",
      location: "Downtown Rooftop",
      status: "booked",
      email: "emily.carter@example.com",
      price: "450",
      notes: "",
    },
    {
      id: uid(),
      clientName: "Lopez Maternity",
      jobType: "Maternity",
      date: addDays(-4),
      time: "09:00",
      location: "Studio",
      status: "completed",
      email: "lopez@example.com",
      price: "350",
      notes: "Gallery still needs to be sent.",
    },
    {
      id: uid(),
      clientName: "Tech Co. Headshots",
      jobType: "Event",
      date: addDays(21),
      time: "11:00",
      location: "Tech Co HQ",
      status: "inquiry",
      email: "hr@techco.example.com",
      price: "",
      notes: "",
    },
  ];
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

// ---------- Date helpers ----------

function pad2(n) {
  return String(n).padStart(2, "0");
}

function formatDateStr(year, month, day) {
  return `${year}-${pad2(month + 1)}-${pad2(day)}`;
}

function todayStr() {
  const d = new Date();
  return formatDateStr(d.getFullYear(), d.getMonth(), d.getDate());
}

function parseDateStr(str) {
  const [y, m, d] = str.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function formatDisplayDate(str) {
  if (!str) return "";
  return parseDateStr(str).toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatShortDate(str) {
  if (!str) return "";
  return parseDateStr(str).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDisplayTime(timeStr) {
  if (!timeStr) return "TBD";
  const [h, m] = timeStr.split(":").map(Number);
  const period = h >= 12 ? "PM" : "AM";
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${hour12}:${pad2(m)} ${period}`;
}

function formatPrice(price) {
  const n = Number(price);
  if (!price || isNaN(n)) return "[price to be confirmed]";
  return `$${n.toFixed(2)}`;
}

// ---------- Calendar rendering ----------

function renderCalendar() {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  document.getElementById("month-label").textContent = viewDate.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  const grid = document.getElementById("calendar-grid");
  grid.innerHTML = "";

  const firstDayIndex = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();
  const totalCells = Math.ceil((firstDayIndex + daysInMonth) / 7) * 7;

  const today = todayStr();

  for (let i = 0; i < totalCells; i++) {
    const cell = document.createElement("div");
    cell.className = "day-cell";

    let cellYear = year;
    let cellMonth = month;
    let dayNum = i - firstDayIndex + 1;

    if (dayNum < 1) {
      dayNum = daysInPrevMonth + dayNum;
      cellMonth = month - 1;
      if (cellMonth < 0) {
        cellMonth = 11;
        cellYear -= 1;
      }
      cell.classList.add("other-month");
    } else if (dayNum > daysInMonth) {
      dayNum = dayNum - daysInMonth;
      cellMonth = month + 1;
      if (cellMonth > 11) {
        cellMonth = 0;
        cellYear += 1;
      }
      cell.classList.add("other-month");
    }

    const dateStr = formatDateStr(cellYear, cellMonth, dayNum);

    if (dateStr === today) cell.classList.add("today");
    if (dateStr === selectedDateStr) cell.classList.add("selected");

    const numberEl = document.createElement("div");
    numberEl.className = "day-number";
    numberEl.textContent = dayNum;
    cell.appendChild(numberEl);

    const dayJobs = jobs.filter((j) => j.date === dateStr);
    const linkedIds = new Set(jobs.map((j) => j.googleEventId).filter(Boolean));
    const otherEvents = GoogleSync.eventsOn(dateStr).filter((ev) => !linkedIds.has(ev.id));

    if (dayJobs.length || otherEvents.length) {
      const dots = document.createElement("div");
      dots.className = "day-dots";
      dayJobs.forEach((j) => {
        const dot = document.createElement("span");
        dot.className = `dot dot-${j.status}`;
        dots.appendChild(dot);
      });
      otherEvents.forEach(() => {
        const dot = document.createElement("span");
        dot.className = "dot dot-gcal";
        dots.appendChild(dot);
      });
      cell.appendChild(dots);
    }

    cell.addEventListener("click", () => selectDate(dateStr));
    grid.appendChild(cell);
  }
}

function selectDate(dateStr) {
  selectedDateStr = dateStr;
  renderCalendar();
  renderDayJobs();
  renderDayGoogleEvents();
}

// ---------- Job list rendering ----------

function createJobItem(job) {
  const li = document.createElement("li");
  li.className = "job-item";

  const top = document.createElement("div");
  top.className = "job-item-top";

  const name = document.createElement("span");
  name.className = "job-item-name";
  name.textContent = `${job.clientName} — ${job.jobType}`;

  const badge = document.createElement("span");
  badge.className = `badge badge-${job.status}`;
  badge.textContent = STATUS_LABELS[job.status] || job.status;

  top.appendChild(name);
  top.appendChild(badge);

  const meta = document.createElement("div");
  meta.className = "job-item-meta";
  meta.textContent = `${formatShortDate(job.date)} at ${formatDisplayTime(job.time)}${job.location ? " · " + job.location : ""}`;

  li.appendChild(top);
  li.appendChild(meta);

  li.addEventListener("click", () => openJobModal(job));
  return li;
}

function renderDayJobs() {
  const label = document.getElementById("selected-date-label");
  const list = document.getElementById("day-job-list");
  const emptyMsg = document.getElementById("day-empty-msg");

  list.innerHTML = "";

  if (!selectedDateStr) {
    label.textContent = "Select a date";
    emptyMsg.classList.add("hidden");
    return;
  }

  label.textContent = formatDisplayDate(selectedDateStr);

  const dayJobs = jobs
    .filter((j) => j.date === selectedDateStr)
    .sort((a, b) => (a.time || "").localeCompare(b.time || ""));

  if (!dayJobs.length) {
    emptyMsg.textContent = "No jobs on this date.";
    emptyMsg.classList.remove("hidden");
    return;
  }

  emptyMsg.classList.add("hidden");
  dayJobs.forEach((job) => list.appendChild(createJobItem(job)));
}

function createGoogleEventItem(event) {
  const li = document.createElement("li");
  li.className = "job-item gcal-item";

  const top = document.createElement("div");
  top.className = "job-item-top";

  const name = document.createElement("span");
  name.className = "job-item-name";
  name.textContent = event.title;
  top.appendChild(name);

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn-small btn-secondary";
  btn.textContent = "Add as Job";
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    openJobModal({
      id: "",
      clientName: event.title,
      jobType: "Other",
      status: "inquiry",
      date: event.date,
      time: event.time,
      location: event.location,
      email: "",
      price: "",
      notes: "Imported from Google Calendar.",
      googleEventId: event.id,
    });
  });
  top.appendChild(btn);

  const meta = document.createElement("div");
  meta.className = "job-item-meta";
  meta.textContent = event.allDay ? "All day" : formatDisplayTime(event.time);
  if (event.location) meta.textContent += ` · ${event.location}`;

  li.appendChild(top);
  li.appendChild(meta);
  return li;
}

function renderDayGoogleEvents() {
  const list = document.getElementById("day-gcal-list");
  const emptyMsg = document.getElementById("day-gcal-empty-msg");
  list.innerHTML = "";

  if (!GoogleSync.isConnected()) {
    emptyMsg.textContent = "Connect Google Calendar in Settings to see your full schedule here.";
    emptyMsg.classList.remove("hidden");
    return;
  }

  if (!selectedDateStr) {
    emptyMsg.textContent = "Select a date to see other calendar events.";
    emptyMsg.classList.remove("hidden");
    return;
  }

  const linkedIds = new Set(jobs.map((j) => j.googleEventId).filter(Boolean));
  const events = GoogleSync.eventsOn(selectedDateStr).filter((ev) => !linkedIds.has(ev.id));

  if (!events.length) {
    emptyMsg.textContent = "No other events on this date.";
    emptyMsg.classList.remove("hidden");
    return;
  }

  emptyMsg.classList.add("hidden");
  events.forEach((event) => list.appendChild(createGoogleEventItem(event)));
}

function renderUpcomingJobs() {
  const list = document.getElementById("upcoming-list");
  list.innerHTML = "";

  const today = todayStr();
  const upcoming = jobs
    .filter((j) => j.date >= today)
    .sort((a, b) => (a.date + (a.time || "")).localeCompare(b.date + (b.time || "")))
    .slice(0, 10);

  if (!upcoming.length) {
    const li = document.createElement("li");
    li.className = "empty-msg";
    li.textContent = "No upcoming jobs scheduled.";
    list.appendChild(li);
    return;
  }

  upcoming.forEach((job) => list.appendChild(createJobItem(job)));
}

// ---------- Job modal ----------

function openJobModal(job) {
  const form = document.getElementById("job-form");
  form.reset();

  const isExisting = !!(job && job.id);

  document.getElementById("job-id").value = isExisting ? job.id : "";
  document.getElementById("job-google-event-id").value = job ? job.googleEventId || "" : "";
  document.getElementById("job-modal-title").textContent = isExisting ? "Edit Job" : "Add Job";
  document.getElementById("delete-job-btn").classList.toggle("hidden", !isExisting);

  document.getElementById("job-client").value = job ? job.clientName : "";
  document.getElementById("job-type").value = job ? job.jobType : "Wedding";
  document.getElementById("job-status").value = job ? job.status : "inquiry";
  document.getElementById("job-date").value = job ? job.date : (selectedDateStr || todayStr());
  document.getElementById("job-time").value = job ? job.time : "";
  document.getElementById("job-location").value = job ? job.location : "";
  document.getElementById("job-email").value = job ? job.email : "";
  document.getElementById("job-price").value = job ? job.price : "";
  document.getElementById("job-notes").value = job ? job.notes : "";

  document.getElementById("job-modal").classList.remove("hidden");
}

function closeJobModal() {
  document.getElementById("job-modal").classList.add("hidden");
}

async function handleJobFormSubmit(e) {
  e.preventDefault();

  const id = document.getElementById("job-id").value;
  const jobData = {
    id: id || uid(),
    clientName: document.getElementById("job-client").value.trim(),
    jobType: document.getElementById("job-type").value,
    status: document.getElementById("job-status").value,
    date: document.getElementById("job-date").value,
    time: document.getElementById("job-time").value,
    location: document.getElementById("job-location").value.trim(),
    email: document.getElementById("job-email").value.trim(),
    price: document.getElementById("job-price").value,
    notes: document.getElementById("job-notes").value.trim(),
    googleEventId: document.getElementById("job-google-event-id").value || null,
  };

  if (id) {
    const idx = jobs.findIndex((j) => j.id === id);
    if (idx !== -1) jobs[idx] = jobData;
  } else {
    jobs.push(jobData);
  }

  saveJobs();
  closeJobModal();
  refreshAll();

  if (settings.googleAutoSync && GoogleSync.isConnected()) {
    try {
      if (jobData.googleEventId) {
        await GoogleSync.updateEvent(jobData);
      } else {
        jobData.googleEventId = await GoogleSync.createEvent(jobData);
      }
      saveJobs();
      await GoogleSync.fetchEvents();
      refreshAll();
    } catch (err) {
      alert("Saved locally, but could not sync with Google Calendar: " + err.message);
    }
  }
}

async function handleDeleteJob() {
  const id = document.getElementById("job-id").value;
  if (!id) return;
  if (!confirm("Delete this job?")) return;

  const job = jobs.find((j) => j.id === id);
  jobs = jobs.filter((j) => j.id !== id);
  saveJobs();
  closeJobModal();
  refreshAll();

  if (job && job.googleEventId && settings.googleAutoSync && GoogleSync.isConnected()) {
    try {
      await GoogleSync.deleteEvent(job.googleEventId);
      await GoogleSync.fetchEvents();
      refreshAll();
    } catch (err) {
      // local delete already succeeded; ignore calendar sync failure
    }
  }
}

// ---------- Settings modal ----------

function openSettingsModal() {
  document.getElementById("settings-business-name").value = settings.businessName;
  document.getElementById("settings-your-name").value = settings.yourName;
  document.getElementById("settings-email").value = settings.yourEmail;
  document.getElementById("settings-phone").value = settings.yourPhone;
  document.getElementById("settings-google-client-id").value = settings.googleClientId;
  document.getElementById("settings-google-autosync").checked = settings.googleAutoSync;
  updateGoogleStatusUI();
  document.getElementById("settings-modal").classList.remove("hidden");
}

function closeSettingsModal() {
  document.getElementById("settings-modal").classList.add("hidden");
}

function handleSettingsFormSubmit(e) {
  e.preventDefault();

  settings = {
    businessName: document.getElementById("settings-business-name").value.trim() || DEFAULT_SETTINGS.businessName,
    yourName: document.getElementById("settings-your-name").value.trim(),
    yourEmail: document.getElementById("settings-email").value.trim(),
    yourPhone: document.getElementById("settings-phone").value.trim(),
    googleClientId: document.getElementById("settings-google-client-id").value.trim(),
    googleAutoSync: document.getElementById("settings-google-autosync").checked,
  };

  saveSettings();
  document.getElementById("business-name").textContent = settings.businessName;
  closeSettingsModal();
  renderEmailPreview();
}

// ---------- Email composer ----------

function renderEmailJobSelect() {
  const select = document.getElementById("email-job-select");
  const previousValue = select.value;
  select.innerHTML = "";

  const sorted = [...jobs].sort((a, b) => (a.date + (a.time || "")).localeCompare(b.date + (b.time || "")));

  if (!sorted.length) {
    const option = document.createElement("option");
    option.textContent = "No jobs yet";
    option.value = "";
    select.appendChild(option);
    return;
  }

  sorted.forEach((job) => {
    const option = document.createElement("option");
    option.value = job.id;
    option.textContent = `${formatShortDate(job.date)} — ${job.clientName} (${STATUS_LABELS[job.status]})`;
    select.appendChild(option);
  });

  if (sorted.some((j) => j.id === previousValue)) {
    select.value = previousValue;
  } else if (selectedDateStr) {
    const match = sorted.find((j) => j.date === selectedDateStr);
    if (match) select.value = match.id;
  }
}

function renderEmailTemplateSelect() {
  const jobSelect = document.getElementById("email-job-select");
  const templateSelect = document.getElementById("email-template-select");
  templateSelect.innerHTML = "";

  const job = jobs.find((j) => j.id === jobSelect.value);
  if (!job) return;

  const templates = EMAIL_TEMPLATES[job.status] || [];
  templates.forEach((tpl) => {
    const option = document.createElement("option");
    option.value = tpl.id;
    option.textContent = tpl.name;
    templateSelect.appendChild(option);
  });
}

function fillTemplate(str, job) {
  const map = {
    clientName: job.clientName || "there",
    jobType: (job.jobType || "session").toLowerCase(),
    date: formatDisplayDate(job.date),
    time: formatDisplayTime(job.time),
    location: job.location || "[location]",
    price: formatPrice(job.price),
    businessName: settings.businessName,
    yourName: settings.yourName,
    yourEmail: settings.yourEmail,
    yourPhone: settings.yourPhone || "[phone]",
  };

  return str.replace(/{{(\w+)}}/g, (_, key) => (key in map ? map[key] : ""));
}

function renderEmailPreview() {
  const jobSelect = document.getElementById("email-job-select");
  const templateSelect = document.getElementById("email-template-select");
  const subjectInput = document.getElementById("email-subject");
  const bodyInput = document.getElementById("email-body");

  const job = jobs.find((j) => j.id === jobSelect.value);
  const templates = job ? EMAIL_TEMPLATES[job.status] || [] : [];
  const template = templates.find((t) => t.id === templateSelect.value);

  if (!job || !template) {
    subjectInput.value = "";
    bodyInput.value = "";
    return;
  }

  subjectInput.value = fillTemplate(template.subject, job);
  bodyInput.value = fillTemplate(template.body, job);
  document.getElementById("email-status").textContent = "";
}

function handleEmailJobChange() {
  renderEmailTemplateSelect();
  renderEmailPreview();
}

function handleCopyEmail() {
  const subject = document.getElementById("email-subject").value;
  const body = document.getElementById("email-body").value;
  const text = `Subject: ${subject}\n\n${body}`;
  const status = document.getElementById("email-status");

  navigator.clipboard
    .writeText(text)
    .then(() => {
      status.textContent = "Copied to clipboard!";
    })
    .catch(() => {
      status.textContent = "Could not copy automatically — please copy manually.";
    });
}

async function handleSaveDraft() {
  const status = document.getElementById("email-status");

  if (!GoogleSync.isConnected()) {
    status.textContent = "Connect your Google account in Settings first.";
    return;
  }

  const jobSelect = document.getElementById("email-job-select");
  const job = jobs.find((j) => j.id === jobSelect.value);
  const subject = document.getElementById("email-subject").value;
  const body = document.getElementById("email-body").value;

  if (!job || !job.email) {
    status.textContent = "Add a client email address to this job first.";
    return;
  }

  try {
    await GoogleSync.createDraft(job.email, subject, body);
    status.textContent = "Draft saved to your Gmail drafts folder.";
  } catch (err) {
    status.textContent = "Could not save draft: " + err.message;
  }
}

function handleOpenMail() {
  const jobSelect = document.getElementById("email-job-select");
  const job = jobs.find((j) => j.id === jobSelect.value);
  const subject = document.getElementById("email-subject").value;
  const body = document.getElementById("email-body").value;

  const to = job && job.email ? job.email : "";
  const url = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.location.href = url;
}

// ---------- Google Sync UI ----------

function updateGoogleStatusUI() {
  const connected = GoogleSync.isConnected();
  const label = connected ? `Connected${GoogleSync.userEmail ? " as " + GoogleSync.userEmail : ""}` : "Not connected";

  document.getElementById("google-status").textContent = `Google: ${label}`;
  document.getElementById("settings-google-status").textContent = label;
  document.getElementById("google-connect-btn").textContent = connected ? "Reconnect Google" : "Connect Google";
  document.getElementById("save-draft-btn").disabled = !connected;
}

function handleGoogleConnectClick() {
  const clientId = settings.googleClientId;
  if (!clientId) {
    alert("Please enter your Google OAuth Client ID in Settings first. See SETUP.md for instructions.");
    openSettingsModal();
    return;
  }

  GoogleSync.connect(clientId, onGoogleConnected);
}

async function onGoogleConnected({ email, error }) {
  if (error) {
    alert("Google sign-in failed: " + error);
    return;
  }

  updateGoogleStatusUI();

  try {
    await GoogleSync.fetchEvents();
  } catch (err) {
    // calendar fetch failure shouldn't block the rest of the UI
  }

  refreshAll();
}

function handleGoogleDisconnectClick() {
  GoogleSync.disconnect();
  updateGoogleStatusUI();
  refreshAll();
}

// ---------- Refresh / init ----------

function refreshAll() {
  renderCalendar();
  renderDayJobs();
  renderDayGoogleEvents();
  renderUpcomingJobs();
  renderEmailJobSelect();
  renderEmailTemplateSelect();
  renderEmailPreview();
}

function init() {
  loadJobs();
  loadSettings();

  document.getElementById("business-name").textContent = settings.businessName;
  selectedDateStr = todayStr();

  document.getElementById("prev-month").addEventListener("click", () => {
    viewDate.setMonth(viewDate.getMonth() - 1);
    renderCalendar();
  });

  document.getElementById("next-month").addEventListener("click", () => {
    viewDate.setMonth(viewDate.getMonth() + 1);
    renderCalendar();
  });

  document.getElementById("today-btn").addEventListener("click", () => {
    viewDate = new Date();
    selectDate(todayStr());
  });

  document.getElementById("add-job-btn").addEventListener("click", () => openJobModal(null));
  document.getElementById("cancel-job-btn").addEventListener("click", closeJobModal);
  document.getElementById("delete-job-btn").addEventListener("click", handleDeleteJob);
  document.getElementById("job-form").addEventListener("submit", handleJobFormSubmit);

  document.getElementById("settings-btn").addEventListener("click", openSettingsModal);
  document.getElementById("cancel-settings-btn").addEventListener("click", closeSettingsModal);
  document.getElementById("settings-form").addEventListener("submit", handleSettingsFormSubmit);

  document.getElementById("email-job-select").addEventListener("change", handleEmailJobChange);
  document.getElementById("email-template-select").addEventListener("change", renderEmailPreview);
  document.getElementById("copy-email-btn").addEventListener("click", handleCopyEmail);
  document.getElementById("save-draft-btn").addEventListener("click", handleSaveDraft);
  document.getElementById("open-mail-btn").addEventListener("click", handleOpenMail);

  document.getElementById("google-connect-btn").addEventListener("click", handleGoogleConnectClick);
  document.getElementById("settings-google-connect-btn").addEventListener("click", handleGoogleConnectClick);
  document.getElementById("settings-google-disconnect-btn").addEventListener("click", handleGoogleDisconnectClick);

  [document.getElementById("job-modal"), document.getElementById("settings-modal")].forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });
  });

  GoogleSync.restoreSession();
  updateGoogleStatusUI();

  refreshAll();

  if (GoogleSync.isConnected()) {
    GoogleSync.fetchEvents()
      .then(refreshAll)
      .catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", init);
