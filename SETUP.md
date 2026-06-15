# Connecting the Dashboard to Google Calendar & Gmail

The dashboard can sign in to your Google account directly in the browser to:

- Show everything on your **Google Calendar** alongside your jobs
- Push new/edited jobs to your calendar automatically (optional)
- Save pre-written emails as **Gmail drafts**
- Surface inquiry emails from your referral sources as potential jobs

This requires a one-time setup where you create a free Google OAuth "Client ID"
and tell Google which web address is allowed to use it. Takes about 10 minutes.

## 1. Host the dashboard somewhere with a real URL

Google sign-in does **not** work when you open `index.html` directly from your
file system (`file://...`). You need to serve it over `http://` or `https://`.

Easiest options:

- **GitHub Pages** (free): in this repo, go to **Settings → Pages**, set
  "Source" to the `main` branch (root folder), save. GitHub will give you a URL
  like `https://yourusername.github.io/claude-/`.
- **Local testing**: from the project folder, run `npx http-server -p 8080`
  and open `http://localhost:8080`.

Note the exact URL (including port, if any) — you'll need it in step 4.

## 2. Create a Google Cloud project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown at the top → **New Project**.
3. Give it any name (e.g. "Photography Dashboard") and create it.

## 3. Enable the APIs

With your new project selected, go to **APIs & Services → Library** and enable:

- **Google Calendar API**
- **Gmail API**

## 4. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Choose **External**, then fill in the app name, your email, and developer
   contact email.
3. On the **Scopes** step, add:
   - `.../auth/calendar.events`
   - `.../auth/gmail.compose`
   - `.../auth/gmail.readonly`
   - `.../auth/userinfo.email`
4. On the **Test users** step, add your own Google account email address.
5. Save. While the app is in "Testing" mode, only the test users you list can
   sign in — that's fine for personal use.

## 5. Create the OAuth Client ID

1. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Web application**.
3. Under **Authorized JavaScript origins**, add the URL from step 1, e.g.:
   - `https://yourusername.github.io`
   - or `http://localhost:8080` for local testing
4. Click **Create**. Copy the **Client ID** (looks like
   `1234567890-abc123.apps.googleusercontent.com`).

## 6. Connect the dashboard

1. Open the dashboard and click **Settings**.
2. Paste the Client ID into **Google OAuth Client ID** and click **Save**.
3. (Optional) check **"Add & update jobs in Google Calendar automatically"**
   if you want new jobs created in the dashboard to also appear on your
   Google Calendar.
4. Click **Connect Google** in the top bar and sign in with the same account
   you added as a test user.

Once connected:

- Your Google Calendar events for the next ~6 months show up on the calendar
  as blue dots and in the **"Other Calendar Events"** list for the selected
  day, with an **"Add as Job"** button to turn any of them into a job.
- The **"Save as Gmail Draft"** button in the Email Composer becomes active.
- Emails from the **Referral Sources** you've listed in Settings (under
  "Email Inquiries") show up in the **"Email Inquiries"** list, with an
  **"Add as Job"** button to turn any of them into a job.

## Adding/updating the Gmail read access scope

If you set up your OAuth Client ID before the "Email Inquiries" feature was
added, you'll need to add the `gmail.readonly` scope to your OAuth consent
screen (step 4 above) and then click **Reconnect Google** in the dashboard so
you can grant the new permission.

## Notes

- The sign-in session lasts about an hour and is stored only in the browser
  tab (not saved to disk). You may need to click **Connect Google** again
  after closing the browser.
- Nothing is sent to any third-party server — all requests go directly from
  your browser to Google's APIs using your own Client ID.
