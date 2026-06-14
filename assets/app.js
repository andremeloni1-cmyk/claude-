const JOBS_KEY = "jsd_jobs";
const SETTINGS_KEY = "jsd_settings";

const DEFAULT_SETTINGS = {
  businessName: "Andre Meloni Photography",
  yourName: "Andre",
  yourEmail: "andre@andremeloniphotography.co",
  yourPhone: "",
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
    if (dayJobs.length) {
      const dots = document.createElement("div");
      dots.className = "day-dots";
      dayJobs.forEach((j) => {
        const dot = document.createElement("span");
        dot.className = `dot dot-${j.status}`;
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

  document.getElementById("job-id").value = job ? job.id : "";
  document.getElementById("job-modal-title").textContent = job ? "Edit Job" : "Add Job";
  document.getElementById("delete-job-btn").classList.toggle("hidden", !job);

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

function handleJobFormSubmit(e) {
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
}

function handleDeleteJob() {
  const id = document.getElementById("job-id").value;
  if (!id) return;
  if (!confirm("Delete this job?")) return;

  jobs = jobs.filter((j) => j.id !== id);
  saveJobs();
  closeJobModal();
  refreshAll();
}

// ---------- Settings modal ----------

function openSettingsModal() {
  document.getElementById("settings-business-name").value = settings.businessName;
  document.getElementById("settings-your-name").value = settings.yourName;
  document.getElementById("settings-email").value = settings.yourEmail;
  document.getElementById("settings-phone").value = settings.yourPhone;
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

function handleOpenMail() {
  const jobSelect = document.getElementById("email-job-select");
  const job = jobs.find((j) => j.id === jobSelect.value);
  const subject = document.getElementById("email-subject").value;
  const body = document.getElementById("email-body").value;

  const to = job && job.email ? job.email : "";
  const url = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.location.href = url;
}

// ---------- Refresh / init ----------

function refreshAll() {
  renderCalendar();
  renderDayJobs();
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
  document.getElementById("open-mail-btn").addEventListener("click", handleOpenMail);

  [document.getElementById("job-modal"), document.getElementById("settings-modal")].forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });
  });

  refreshAll();
}

document.addEventListener("DOMContentLoaded", init);
