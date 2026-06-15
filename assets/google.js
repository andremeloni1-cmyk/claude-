// Client-side Google Calendar & Gmail integration using Google Identity
// Services (GIS). No backend required — the user supplies their own OAuth
// Client ID (see SETUP.md) and signs in directly from the browser.

const GOOGLE_TOKEN_KEY = "jsd_google_token";

const GOOGLE_SCOPES = [
  "https://www.googleapis.com/auth/calendar.events",
  "https://www.googleapis.com/auth/gmail.compose",
  "https://www.googleapis.com/auth/userinfo.email",
].join(" ");

const GoogleSync = {
  clientId: null,
  tokenClient: null,
  tokenClientId: null,
  accessToken: null,
  tokenExpiry: 0,
  userEmail: null,
  events: [],

  restoreSession() {
    const saved = sessionStorage.getItem(GOOGLE_TOKEN_KEY);
    if (!saved) return;
    try {
      const data = JSON.parse(saved);
      if (data.expiry > Date.now()) {
        this.accessToken = data.token;
        this.tokenExpiry = data.expiry;
        this.userEmail = data.email;
      } else {
        sessionStorage.removeItem(GOOGLE_TOKEN_KEY);
      }
    } catch (e) {
      sessionStorage.removeItem(GOOGLE_TOKEN_KEY);
    }
  },

  persistSession() {
    sessionStorage.setItem(
      GOOGLE_TOKEN_KEY,
      JSON.stringify({ token: this.accessToken, expiry: this.tokenExpiry, email: this.userEmail })
    );
  },

  isConnected() {
    return !!this.accessToken && Date.now() < this.tokenExpiry;
  },

  // Sign in (or re-auth) with the given OAuth Client ID. Calls
  // onConnected({ email }) on success or onConnected({ error }) on failure.
  connect(clientId, onConnected) {
    const startConnect = () => {
      if (!this.tokenClient || this.tokenClientId !== clientId) {
        this.tokenClient = google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: GOOGLE_SCOPES,
          callback: async (response) => {
            if (response.error) {
              onConnected({ error: response.error });
              return;
            }
            this.accessToken = response.access_token;
            this.tokenExpiry = Date.now() + (response.expires_in || 3600) * 1000;
            try {
              await this.fetchUserEmail();
            } catch (e) {
              // not fatal — we can still use the access token
            }
            this.persistSession();
            onConnected({ email: this.userEmail });
          },
        });
        this.tokenClientId = clientId;
      }
      this.tokenClient.requestAccessToken({ prompt: "consent" });
    };

    if (window.google && window.google.accounts && window.google.accounts.oauth2) {
      startConnect();
      return;
    }

    let attempts = 0;
    const interval = setInterval(() => {
      attempts += 1;
      if (window.google && window.google.accounts && window.google.accounts.oauth2) {
        clearInterval(interval);
        startConnect();
      } else if (attempts > 40) {
        clearInterval(interval);
        onConnected({ error: "Google sign-in library failed to load. Check your connection and try again." });
      }
    }, 250);
  },

  disconnect() {
    if (this.accessToken && window.google && window.google.accounts) {
      google.accounts.oauth2.revoke(this.accessToken, () => {});
    }
    this.accessToken = null;
    this.tokenExpiry = 0;
    this.userEmail = null;
    this.events = [];
    sessionStorage.removeItem(GOOGLE_TOKEN_KEY);
  },

  async fetchUserEmail() {
    const data = await this.apiFetch("https://www.googleapis.com/oauth2/v2/userinfo");
    this.userEmail = data.email;
  },

  async apiFetch(url, options = {}) {
    if (!this.isConnected()) throw new Error("Not connected to Google");
    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: `Bearer ${this.accessToken}`,
      },
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Google API error (${res.status}): ${text}`);
    }
    if (res.status === 204) return null;
    return res.json();
  },

  // Fetches events from the user's primary calendar from one month ago to
  // six months from now.
  async fetchEvents() {
    const timeMin = new Date();
    timeMin.setMonth(timeMin.getMonth() - 1);
    const timeMax = new Date();
    timeMax.setMonth(timeMax.getMonth() + 6);

    const params = new URLSearchParams({
      timeMin: timeMin.toISOString(),
      timeMax: timeMax.toISOString(),
      singleEvents: "true",
      orderBy: "startTime",
      maxResults: "250",
    });

    const data = await this.apiFetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events?${params}`);

    this.events = (data.items || [])
      .filter((ev) => ev.start && (ev.start.date || ev.start.dateTime))
      .map((ev) => ({
        id: ev.id,
        title: ev.summary || "(No title)",
        date: (ev.start.date || ev.start.dateTime).slice(0, 10),
        time: ev.start.dateTime ? ev.start.dateTime.slice(11, 16) : "",
        allDay: !!ev.start.date,
        location: ev.location || "",
        htmlLink: ev.htmlLink,
      }));

    return this.events;
  },

  eventsOn(dateStr) {
    return this.events.filter((e) => e.date === dateStr);
  },

  jobToEventBody(job) {
    const summary = `${job.clientName} — ${job.jobType}`;
    const description = ["Status: " + STATUS_LABELS[job.status], job.price ? `Price: $${job.price}` : null, job.notes || null]
      .filter(Boolean)
      .join("\n");

    if (job.time) {
      return {
        summary,
        location: job.location || "",
        description,
        start: { dateTime: `${job.date}T${job.time}:00` },
        end: { dateTime: addHoursToDateTime(job.date, job.time, 2) },
      };
    }

    return {
      summary,
      location: job.location || "",
      description,
      start: { date: job.date },
      end: { date: addDaysToDateStr(job.date, 1) },
    };
  },

  async createEvent(job) {
    const data = await this.apiFetch("https://www.googleapis.com/calendar/v3/calendars/primary/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(this.jobToEventBody(job)),
    });
    return data.id;
  },

  async updateEvent(job) {
    await this.apiFetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events/${job.googleEventId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(this.jobToEventBody(job)),
    });
  },

  async deleteEvent(eventId) {
    try {
      await this.apiFetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events/${eventId}`, {
        method: "DELETE",
      });
    } catch (e) {
      // event may already be gone on Google's side — ignore
    }
  },

  async createDraft(to, subject, body) {
    const message = [`To: ${to}`, `Subject: ${subject}`, 'Content-Type: text/plain; charset="UTF-8"', "", body].join("\r\n");

    const encoded = btoa(unescape(encodeURIComponent(message)))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

    return this.apiFetch("https://www.googleapis.com/gmail/v1/users/me/drafts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: { raw: encoded } }),
    });
  },
};

function addDaysToDateStr(dateStr, days) {
  const d = new Date(`${dateStr}T00:00:00`);
  d.setDate(d.getDate() + days);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function addHoursToDateTime(dateStr, timeStr, hours) {
  const d = new Date(`${dateStr}T${timeStr}:00`);
  d.setHours(d.getHours() + hours);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
}
