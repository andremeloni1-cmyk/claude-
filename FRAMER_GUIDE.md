# Framer Project Notes — Andre Meloni Photography

This site is built in Framer (via the `mcp__ccd7c9c8-9134-4b27-904c-ec6f026d1d55__*`
Framer MCP tools — no local source files). These notes capture template
documentation, project structure, and MCP tool quirks/limitations discovered
while editing, so future sessions don't have to rediscover them.

## Template info

- Template by **Templifica / bynneh** (contact: x.com/bynneh, hello@templifica.com)
- Current version: **1.21** (native filter/search for portfolio, native
  lightbox for galleries, polished hover effects, rebuilt header component)
- A "User guide" design page exists in the project (`nodeId="iO9TyOYwt"`) with
  the template author's own docs — read via `getNodeXml` if needed again.

## Template author's guide — key points

- **Global components**: Footer, Grid, and "Get Template" button are global —
  edit one instance, updates everywhere. Found in the Assets Panel.
- **Header/Footer/Photographer components**: reused across all pages — edit
  once, propagates everywhere.
- **Edit the "Primary" variant only** when changing text/images/links inside a
  component — this is what propagates to all breakpoints and hover states.
- **Cards/buttons are customizable via right-panel settings**, not by editing
  internals directly. (Likely relevant to the portfolio card `Link` prop issue
  below — may need to be set via a right-panel "Link" control in the Framer
  editor UI rather than via MCP XML attributes.)
- **FAQ section**: edit via FAQ/Questions component (double-click on homepage).
- **Testimonials**: must have exactly 3 items.
- **CMS**: Blog and Portfolio cards/pages are *intended* to be CMS-bound
  (auto-update from CMS edits). Per-field bindings ("Insert Variable") are a
  manual right-panel action — not exposed via MCP.
- **Forms**: each native Framer Form needs an email added to its recipients
  list in the right panel, individually, or submissions won't be emailed.
  **Check `/contact` for this — likely still needs to be set.**

## Project structure reference

### Pages
| Path | nodeId |
|---|---|
| `/` | `augiA20Il` |
| `/blog` | `JB9ZuENHj` |
| `/blog/:slug` | `QciPY2G4i` |
| `/404` | `AHZqS6vxL` |
| `/contact` | `JhEGlRZQU` |
| `/about` | `nbiWtvW87` |
| `/portfolio` | `Ge70M7Flj` |
| `/portfolio/:slug` | `ZXqVV5X0H` (created manually — verify it's set as the CMS collection page for Portfolio in Pages panel) |

### Design pages
| Name | nodeId |
|---|---|
| User guide | `iO9TyOYwt` |

### Key components
| Name | nodeId |
|---|---|
| Header | `tLSFnp8fu` |
| Footer | `JBX48afsO` |
| Portfolio card | `Th722ys5j` |
| Blog card | `q8sExslWw` |
| Blog card small | `P5Uk_jJ8N` |
| Contact card | `lJuGp8FE7` |
| Go back button | `RiTFBoiLP` |

### CMS collections
- Portfolio: `r4GnmA_r2`
- Category: `qP9bHc6_m`
- Blog: `EEv3Nygkn`

## MCP tool quirks & limitations (confirmed)

- **`backgroundImage` cannot be set via `updateXmlForNode`** on a Frame node —
  on create or update, with fresh or known-good URLs, with/without
  `backgroundColor` present. Always either ignored or "No changes were made!".
  Must be set manually in the Framer UI (drag image in).
- **Component instance Link props (e.g. `bqLiF7w9f` on Portfolio card) cannot
  be set via `updateXmlForNode`** — returns "No changes were made!" regardless
  of plain-path or JSON `{"type":"webPage","webPageId":"..."}` format. Must be
  set via the component's right-panel "Link" control in Framer UI.
- **`createPage` only creates a single Desktop frame** (e.g.
  `width="1200px" height="1080px"`) — no Tablet/Phone breakpoints. New pages
  built this way need breakpoints added manually in Framer UI.
- **New-node misplacement**: when `updateXmlForNode` creates multiple new
  nodes (especially Text) in one call alongside existing-node references, the
  new nodes often land as siblings of the wrapper root with
  `position="absolute"` and arbitrary `top`/`left` offsets instead of inside
  the intended nested parent.
  - **Fix**: issue a second `updateXmlForNode` targeting the correct immediate
    parent `nodeId`, listing existing children by `nodeId` plus the misplaced
    new ones (with corrected `inlineTextStyle`/`width`, no `position`/`top`/
    `left`) in the desired order. This reparents, reorders, and strips bad
    positioning in one shot.
- **Reparenting trick**: referencing an existing node by `nodeId` under a new
  parent wrapper in `updateXmlForNode` moves it there without needing to
  restate all its attributes.

## Outstanding manual-action items (Framer UI)

1. **Portfolio card slugs** (`bqLiF7w9f` prop) on `/portfolio` — this is a
   plain slug **string** field (not a Link control), confirmed by
   `bqLiF7w9f="matt-and-amanda-engagement-kiama-lookout"` on `FVdsMoRWR`. Still
   cannot be set via MCP `updateXmlForNode` (no error, but value doesn't
   change) even as a plain string. Set these manually in the right panel:
   - `XtH21I_uu` (Sarah & Bidia card) → `bqLiF7w9f` should be
     `sarah-and-bidia-wedding-kangaroo-valley` (currently wrongly has the Matt
     & Amanda slug, copy-paste bug).
   - `bEgAhcHPp` (Alana & Jacque card) → `bqLiF7w9f` should be
     `alana-and-jacque-wedding-wollongong-botanical-gardens` (currently empty).
   - `FVdsMoRWR` (Matt & Amanda card) → already correct
     (`matt-and-amanda-engagement-kiama-lookout`).
   - ✅ `FVdsMoRWR`'s empty title (`hJ5j8DWR6`) was fixed via MCP → now
     "Matt & Amanda — Kiama Lookout".
2. **`/about` Approach section photo** (`idkzjQrFK`) — ✅ now has a real
   `backgroundImage` set (no longer the gray placeholder). Appears resolved
   (possibly fixed manually since the last check) — just verify it looks right.
3. **CMS data binding** on `/blog/:slug` and `/portfolio/:slug` — static
   placeholder layouts built; need per-field "Insert Variable" binding in
   Framer UI to connect to CMS collections.
4. **Verify `/portfolio/:slug` CMS collection page setting** in Pages panel.
5. **Tablet/Phone breakpoints** missing on `/contact`, `/404`, `/blog/:slug`,
   `/portfolio/:slug` (all built via `createPage`, which only creates Desktop).
6. **Contact form recipient email** — verify/set the email recipient for the
   form on `/contact` so submissions are delivered.

## ⚠️ Potential issue found: `/blog` page may have lost its content

- `getNodeXml("JB9ZuENHj")` (the `/blog` page) now returns **completely
  empty** XML (no Desktop/Tablet/Phone frames at all).
- The previously-noted content root `cVTJ9yF1b` (Header + 6 BlogCards +
  Footer) returns **"Node with ID cVTJ9yF1b not found."**
- The "Blog card" (`q8sExslWw`) and "Blog card small" (`P5Uk_jJ8N`) components
  *also* both return empty XML (`<BlogCard nodeId="q8sExslWw" />` with no
  children) — yet a live `BlogCard` instance on the homepage
  (`nodeId="xrmHDl5t1"`) references `componentId="q8sExslWw"
  variant="kYHa_x55W"` with real props (`rvBKN8hHg="/blog:slug"`,
  `FG8rd1EUA="2026-06-11T00:00:00.000Z"`,
  `TFO4LYmNP="A Greyleigh Kiama Wedding — Sarah & Archie"`), so the component
  can't actually be empty.
- This pattern (multiple Blog-related nodes returning empty XML while still
  being referenced live) suggests an **MCP tool query issue for these specific
  nodes**, not necessarily real data loss — but this could not be confirmed
  (project has no published staging/production URL to check against).
- **Action needed**: before any rebuild of `/blog`, open the page in the
  Framer editor and confirm whether it visually still has its content. If it's
  genuinely empty, it needs to be rebuilt with 6 Blog cards (data for all 6
  posts is available via `getCMSItems("EEv3Nygkn")`). If it still has content,
  this is just an MCP read limitation to note and move on from.
- Also note: the homepage's `rvBKN8hHg="/blog:slug"` looks like an unresolved
  placeholder link (literally `/blog:slug` instead of a real post path) — same
  family of issue as the portfolio card slug/link props above.

## Security note

Unframer MCP credential URLs (with `id`/`secret` query params) were pasted in
chat in past sessions and should be treated as compromised — rotate them in
Unframer's settings. Never paste these URLs into chat; do not commit them to
this repo (see `README.md` for the env-var approach).
