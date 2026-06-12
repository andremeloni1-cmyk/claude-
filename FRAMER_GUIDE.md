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

1. **Portfolio card links** on `/portfolio` (`FVdsMoRWR`, `XtH21I_uu`,
   `bEgAhcHPp`) — set Link to the matching `/portfolio/:slug` CMS items
   (Matt & Amanda / Sarah & Bidia / Alana & Jacque) via right-panel Link
   control.
2. **`/about` Approach section photo** (`idkzjQrFK`) — currently a gray
   placeholder (`backgroundColor="/Gray BG"`); drag the intended portrait
   photo back in.
3. **CMS data binding** on `/blog/:slug` and `/portfolio/:slug` — static
   placeholder layouts built; need per-field "Insert Variable" binding in
   Framer UI to connect to CMS collections.
4. **Verify `/portfolio/:slug` CMS collection page setting** in Pages panel.
5. **Tablet/Phone breakpoints** missing on `/contact`, `/404`, `/blog/:slug`,
   `/portfolio/:slug` (all built via `createPage`, which only creates Desktop).
6. **Contact form recipient email** — verify/set the email recipient for the
   form on `/contact` so submissions are delivered.

## Security note

Unframer MCP credential URLs (with `id`/`secret` query params) were pasted in
chat in past sessions and should be treated as compromised — rotate them in
Unframer's settings. Never paste these URLs into chat; do not commit them to
this repo (see `README.md` for the env-var approach).
