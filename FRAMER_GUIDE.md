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
| Path | nodeId | Status |
|---|---|---|
| `/` | `augiA20Il` | existing, audited for Header/Footer issues only |
| `/blog` | `JB9ZuENHj` | existing; orphan empty Desktop frame `ubwWauV3w` deleted |
| `/blog/:slug` | `QciPY2G4i` | **rebuilt** from genuinely-empty state with full real content (Greyleigh Kiama Wedding — Sarah & Archie, CMS item `dqkpr8bH1`) |
| `/404` | `AHZqS6vxL` | **rebuilt** from genuinely-empty state, verified clean |
| `/contact` | `JhEGlRZQU` | existing, not yet re-audited this session |
| `/about` | `nbiWtvW87` | existing, not yet re-audited this session |
| `/portfolio` | `Ge70M7Flj` | existing, not yet re-audited this session |
| `/portfolio/:slug` | `af3IrmIbP` | **created** (page was missing entirely) and built with Matt & Amanda content (CMS item `iiCxeDt0L`); orphan empty Desktop frame `uzvKyA9qq` deleted |

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
- Portfolio: `r4GnmA_r2` (Title `TWzcXE82P`, Category `eu9GOakWf` → Category collection `qP9bHc6_m`, Date `e_oqHADQd`, Preview `l7MvKqPuQ`, Gallery col 1 `xegTeIKOI`, Gallery col 2 `LM74JNIh4`)
- Portfolio 2: `bE1ItQMQR` (same field shape as Portfolio — purpose/usage not investigated)
- Category: `qP9bHc6_m`
- Blog: `EEv3Nygkn` (Title `ua9FnvLmw`, Date `Fi53MNOAk`, Preview `o4RZewo_g`, Intro 1 `ivhGqPB2R`, Intro 2 `wIjEVkATu`, Image 1 `rcnbZcT2W`, Content `Jf1NQ7bt1`)

## MCP tool quirks & limitations (confirmed)

- **`getNodeXml` only returns full content for the currently-focused
  page/component in the Framer app.** Any other page or component returns
  empty XML (`Node xml:` with nothing after it), or in the case of a
  component, just its bare root tag with no children (e.g.
  `<Header nodeId="tLSFnp8fu" />`). This was the real cause of earlier
  "empty"/"not found" results for `/404` and `/blog` that were initially
  mistaken for data loss — the page/component simply wasn't open/focused in
  Framer at the time. **To inspect or edit a different page/component, the
  user needs to open/select it in the Framer app first**, then `getProjectXml`
  will report it as the "currently focused" node and `getNodeXml` will return
  its full tree.
- **New-node "misplacement" in creation diffs is cosmetic, not real.** When
  `updateXmlForNode` creates new nodes inside a Stack layout, the returned
  diff often shows the new nodes with spurious
  `position="absolute" top="0px" left="-300px"` (or similar) attributes.
  Re-reading the node immediately after via `getNodeXml` shows **no
  position/top/left attributes at all** — this is just a diff-display
  artifact. **No follow-up "fix" call is needed** — just verify with
  `getNodeXml` that the structure looks correct after creation.
- **`backgroundImage` cannot be set via `updateXmlForNode`** on a Frame node —
  on create or update, with fresh or known-good URLs, with/without
  `backgroundColor` present. Always either ignored or "No changes were made!".
  Must be set manually in the Framer UI (drag image in). Used `/Gray BG`
  placeholder Frames with `borderRadius` for hero/gallery images on
  `/blog/:slug` and `/portfolio/:slug`.
- **Component instance Link props (e.g. `bqLiF7w9f` on Portfolio card) cannot
  be set via `updateXmlForNode`** — returns "No changes were made!" regardless
  of plain-path or JSON `{"type":"webPage","webPageId":"..."}` format. Must be
  set via the component's right-panel "Link" control in Framer UI.
- **`createPage` only creates a single Desktop frame** (e.g.
  `width="1200px" height="1080px"`, `/Gray BG`, no children) — no Tablet/Phone
  breakpoints. This default frame is an orphan once real content is added as a
  sibling and should be deleted via `deleteNode`. New pages built this way
  need Tablet/Phone breakpoints added manually in Framer UI.
- **Text nodes with a `font="Inter-Medium"` / `font="Inter-SemiBold"`
  attribute can fail** with `"Failed to process node X: Font with selector
  '...' not found"`. Workaround: omit the `font` attribute entirely (or use
  `inlineTextStyle` instead) when updating that node — text/link/other
  attribute changes then go through fine.
- **Reparenting trick**: referencing an existing node by `nodeId` under a new
  parent wrapper in `updateXmlForNode` moves it there without needing to
  restate all its attributes.

## Site-wide Header/Footer link & professionalism fixes (this session)

These components are shared across every page, so each fix below applies
site-wide:

1. ✅ Header (`tLSFnp8fu`) `otCxfEPeh` — mailto link fixed:
   `hello@andremeloniphotography.co` → `andre@andremeloniphotography.co`.
2. ✅ Footer (`JBX48afsO`) `FyxhKoem2` — grammar: "Lets talk" → "Let's talk".
3. ✅ Footer `uHCiRAcGo` — copyright fixed: "@ 2026 All rights reserved" →
   "© 2026 Andre Meloni Photography. All rights reserved."
4. ✅ Footer `W_LwrZl2D` — phone link fixed: `tel:555-666-7777` →
   `tel:042198936`.
5. ✅ Footer `VHVZfcB3l` — Instagram URL fixed: `x.com/bynneh` →
   `https://www.instagram.com/andremeloniphotography`.
6. ✅ Footer `VMpZx7Ne_` (active `sOLlak1N3` variant NavLink) — added missing
   `EqY7rffBl="/portfolio"` (Home/Blog/About/Contact siblings already had
   their link prop; Portfolio was missing).
7. ✅ Footer `YrNHPX5kU` (legacy `EsWWwkszM`/Primary variant) — added missing
   `link="/portfolio"` for the same reason.
8. ✅ Footer `bMCgnIlqQ` — added missing `mailto:` prefix:
   `andre@andremeloniphotography.co` → `mailto:andre@andremeloniphotography.co`
   (required omitting the `font="Inter-Medium"` attribute to avoid the font
   error above).
9. ✅ Footer `CAyo63Kqr` — deleted. Leftover template-author "x.com" SocialLink
   pointing to `x.com/bynneh`.
10. ✅ Footer `hDs2hhoAI` (legacy `EsWWwkszM`/Primary variant) — email
    consistency: `hello@andremeloniphotography.co` →
    `andre@andremeloniphotography.co` (matches fix #1 and #8 elsewhere).

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
2. **`/about` Approach section photo** (`idkzjQrFK`) — ✅ now has a real
   `backgroundImage` set (no longer the gray placeholder). Appears resolved —
   just verify it looks right.
3. **CMS data binding** on `/blog/:slug` and `/portfolio/:slug` — static
   placeholder layouts built with real content for one sample post/gallery
   each; need per-field "Insert Variable" binding in Framer UI to connect to
   CMS collections so other posts/galleries render correctly when visited.
4. **Verify `/portfolio/:slug` (`af3IrmIbP`) CMS collection page setting** in
   Pages panel — confirm it's bound as the Portfolio collection's item page.
5. **Tablet/Phone breakpoints** missing on `/404`, `/blog/:slug`,
   `/portfolio/:slug`, and `/contact` (all built/rebuilt via `createPage`,
   which only creates a Desktop frame).
6. **Hero/gallery placeholder images** on `/blog/:slug` (`P4ZdpG142`,
   `ptWo8aPw0`) and `/portfolio/:slug` (`fyBgNpdks` + 9 gallery frames) are
   `/Gray BG` placeholders — need real images dropped in manually (MCP can't
   set `backgroundImage`).
7. ~~**Contact form recipient email**~~ — **superseded, see finding below.**
   The `/contact` form is NOT a native Framer form, so the "add recipient
   email in Framer's right panel" guidance doesn't apply. It's
   delivered/managed entirely in the Storyflow dashboard (external account,
   not MCP-doable).
8. **Delete "Portfolio 2" CMS collection** (`bE1ItQMQR`) — user confirmed
   delete (it duplicates "Portfolio" `r4GnmA_r2`). **Must be done in Framer
   UI** — the MCP has no `deleteCMSCollection` tool, only `deleteCMSItem`
   (which would just empty it and leaves an orphan collection shell). In
   Framer: CMS panel → right-click "Portfolio 2" → Delete collection (Framer
   warns if anything is bound to it). Its 3 item IDs, if ever needed:
   `rPnUez8DH`, `B4XjamlkV`, `wTdBE3z7O`.
9. ✅ **Draft Category items deleted** — "Studio Photography" (`x0gcrjku6`)
   and "Lifestyle" (`FOh0syoWy`) deleted via `deleteCMSItem` (user
   confirmed). Category collection `qP9bHc6_m` now holds only "Wedding"
   (`BUVDI0Xo2`) and "Engagement" (`NvDIxFgYB`).
10. ~~**Contact form recipient email (Storyflow)**~~ — **no action needed.**
    Storyflow is the user's own CRM for managing bookings, already set up on
    their end. The embedded form
    (`app.storyflow.com.au/contactform/1766106383436x987076636821318100`)
    feeds into it as intended.
11. **`llms.txt`** — add via Framer Site Settings custom code / DNS-hosting
    layer once a custom domain is live; not possible via MCP.

## Business info (provided by user, for SEO/checklist items)

- **Business name**: Andre Meloni Photography
- **Service area**: Sydney, Southern Highlands, and South Coast (NSW)
- **Pricing/packages**: already on the homepage (`/`) — no separate
  pricing page needed.
- **No business hours / response-time messaging** wanted on `/contact`.
- **No Privacy Policy page** needed.
- **SEO keywords** — suggested starting set (based on business name,
  service area, and the wedding/portrait/candid-style bio below). Use these
  for page titles/meta descriptions once SEO settings are accessible:
  - "Sydney wedding photographer"
  - "Southern Highlands wedding photographer"
  - "South Coast NSW wedding photographer"
  - "Engagement photographer Sydney / Southern Highlands"
  - "Candid wedding photography Sydney"
  - "Portrait photographer Southern Highlands"
  - "Andre Meloni Photography"

## Content provided by user, ready to insert

### `/about` — photographer bio/story (provided 2026-06-12)

Needs `/about` (`nbiWtvW87`) focused in Framer so its text nodes can be
located and updated. Paste/adapt into the bio/story section:

> Photography found me right after high school, and it started with people.
>
> I was drawn to portrait work because of what it asked of me to actually
> understand someone. To find the side of them that only their closest
> people get to see, and bring that into a frame.
>
> What kept me going was a simple thing. Watching someone's face when they
> saw an image of themselves — really saw it — and were taken straight back
> to that moment. Not just what it looked like, but what it felt like. That
> reaction never got old.
>
> From there, weddings made complete sense. A wedding day is one of the most
> human days a person will ever have. Everyone in the room is full of
> something — nerves, love, relief, joy. My job is to pay attention to all
> of it.
>
> My approach hasn't changed much from those early portrait days. I'm still
> trying to understand people before I photograph them. Still looking for
> the honest moments — the ones that live just outside the posed ones. The
> quiet glance. The laugh that came out of nowhere. The way someone held
> their person's hand without thinking about it.
>
> Great wedding photography isn't really about the day itself. It's about
> what you feel ten years from now when you open that album. Whether it
> still carries the weight of the room, the people, the version of yourself
> you were in that moment.
>
> That's what I'm making. Something that holds.

## Code files

- `ContactFormEmbed.tsx` (codeFileId `G7Fz0w8`) — code component used on
  `/contact`. It's an `<iframe>` embedding a **Storyflow** contact form:
  `https://app.storyflow.com.au/contactform/1766106383436x987076636821318100`.
  It forwards `fbclid` query params for ad-tracking and uses
  `iframe-resizer` for auto-height. **The "link your email to all forms"
  checklist item for `/contact` must be done in the Storyflow dashboard**,
  not Framer — Framer has no recipient-email setting for this form since
  it's just an iframe wrapper.
- **`llms.txt`**: not feasible via the Framer MCP. Framer code files
  (`createCodeFile`) only support React/TS components or overrides, not
  static text files served at a domain root path. Framer's native
  "Custom Code" / site-settings injection (if any) isn't exposed via MCP.
  This needs to be done in the Framer UI (Site Settings → General → Custom
  Code, if Framer supports a redirect/page rule) or via the hosting
  layer/DNS once a custom domain is set up — flagged as a manual/post-launch
  item, not currently actionable.

## CMS audit (this session)

Audited all 4 CMS collections for the "remove Lorem Ipsum / demo content"
and "add real content" checklist items:

- **Portfolio** (`r4GnmA_r2`, 3 items) and **Portfolio 2** (`bE1ItQMQR`,
  3 items) — near-identical duplicates, same real content (Matt & Amanda,
  Sarah & Bidia, Alana & Jacque). No Lorem Ipsum. Purpose of the duplicate
  "Portfolio 2" collection is still unclear — **needs user input**: is it
  used anywhere, or can it be deleted?
- **Blog** (`EEv3Nygkn`, 6 items) — all real, well-written posts,
  `draft: false`. No issues found.
- **Category** (`qP9bHc6_m`, 4 items) — "Wedding" (`BUVDI0Xo2`) and
  "Engagement" (`NvDIxFgYB`) are active and referenced by Portfolio items.
  "Studio Photography" (`x0gcrjku6`) and "Lifestyle" (`FOh0syoWy`) are
  **`draft: true` and not referenced by any Portfolio item** — candidates
  for deletion per "delete demo CMS items you don't need", but could be
  intentional future categories. **Needs user confirmation before
  deleting.**
- No Lorem-Ipsum/placeholder text found anywhere in CMS content — all
  content is real and site-specific already.

## Remaining site-wide audit

Header/Footer (shared across all pages) have been fully audited and fixed
(see above). Per-page content audit for spelling/links/spacing/professionalism
is still pending for `/`, `/contact`, `/about`, `/portfolio`, and `/blog` —
blocked on the focus limitation above. To continue: open each page in the
Framer app one at a time so `getNodeXml` can read it.

## Security note

Unframer MCP credential URLs (with `id`/`secret` query params) were pasted in
chat in past sessions and should be treated as compromised — rotate them in
Unframer's settings. Never paste these URLs into chat; do not commit them to
this repo (see `README.md` for the env-var approach).
