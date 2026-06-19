# Etsy digital-listing field cheat sheet

Field rules for `create_draft_listing` (via `scripts/create_listing.py
create`), specific to **digital-download** listings.

## Required fields

| Field | Rule |
|---|---|
| `title` | ≤140 characters. Front-load the main search keyword — Etsy's search weighs early words more heavily. |
| `description` | No hard length limit enforced by the API, but lead with what the buyer gets and how to use/download it; avoid keyword stuffing. |
| `price` | Decimal number, in the shop's currency. No currency symbol. |
| `quantity` | For a non-made-to-order digital download, set high (e.g. `999`) — it's not a real inventory count, just how many times it can be purchased before needing a refresh. |
| `who_made` | One of `"i_did"`, `"someone_else"`, `"collective"`. Digital products you created yourself: `"i_did"`. |
| `when_made` | One of Etsy's fixed enum buckets, e.g. `"made_to_order"`, `"2020_2026"`, `"2010_2019"`, etc. — pick the bucket matching when the design/template was created. |
| `taxonomy_id` | Numeric category id. Look it up with `scripts/create_listing.py taxonomy "<keyword>"` rather than guessing — Etsy's taxonomy tree changes and ids aren't stable across categories. |

## Type field

Set `"type": "download"` for a pure digital product. This is what tells
Etsy not to require a shipping profile (`shipping_profile_id`, which is
required for `"physical"` listings but irrelevant here).

## Tags

- Up to **13** tags.
- Each tag ≤20 characters.
- Etsy matches multi-word phrases as a unit (e.g. `"wedding planner"` is one
  tag) — use natural buyer search phrases, not single generic words.
- Avoid repeating the same word across many tags; cover distinct angles
  (use case, style, occasion, format) instead.

## Materials

Optional for digital goods, but worth setting — buyers do filter by it.
Common values for downloads: `"PDF"`, `"Digital file"`, `"JPEG"`,
`"Lightroom preset"`, `"Procreate brush"`. Keep each entry short.

## Images and files

- Images: `scripts/create_listing.py` uploads them by `rank` in the order
  given in the spec's `images` array (rank 1 = primary/cover image). Etsy
  requires at least one image before a listing can be activated.
- Digital files: uploaded via the `files` array the same way. Etsy requires
  at least one digital file attached before a non-made-to-order digital
  listing can be activated.
- **Etsy's Seller Handbook sets file-count and file-size limits for digital
  downloads (these have changed over time and aren't enforced by the create
  API call itself — they're checked at upload).** If an upload fails with a
  size/format error, check the current limits in Etsy's Seller Handbook
  rather than assuming the numbers above are still current.

## Drafts vs. active

`create_draft_listing` always creates the listing in `draft` state,
regardless of what's in the spec. Moving to `active` (publicly visible and
purchasable) only happens via `scripts/create_listing.py activate
<listing_id>` — a separate, deliberate command, never automatic.
