/**
 * Push uploaded photo bundles into the Framer Portfolio CMS via the Framer Server API.
 *
 * Reads every bundle under ../published_profile/<slug>/post.json, maps its
 * fields onto the configured Framer collection (Portfolio by default), files
 * each item under the configured category (a reference into the Category
 * collection), creates any item that does not yet exist, and publishes the
 * site. Re-runs are safe: an item whose slug already exists is updated in place
 * rather than duplicated.
 *
 * Required environment:
 *   FRAMER_API_KEY       API key from Framer Site Settings -> General.
 *   FRAMER_PROJECT_URL   e.g. https://framer.com/projects/Sites--xxxxxxxx
 *   IMAGE_BASE_URL       Public base URL the committed images are served from,
 *                        e.g. https://raw.githubusercontent.com/<owner>/<repo>/<branch>
 * Optional:
 *   FRAMER_PROFILE_COLLECTION_ID   Pin an exact collection (overrides name match).
 *   MAX_PUBLISH_PER_RUN            Cap new items pushed per run (default: all pending).
 */

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";
import { connect } from "framer-api";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..");
const PUBLISHED_DIR = join(REPO_ROOT, "published_profile");

function requireEnv(name) {
  const v = (process.env[name] || "").trim();
  if (!v) throw new Error(`Missing required environment variable ${name}.`);
  return v;
}

function loadConfig() {
  const raw = readFileSync(join(REPO_ROOT, "config.yaml"), "utf8");
  const data = parseYaml(raw) || {};
  const profile = data.profile || {};
  return {
    collectionName: (profile.collection_name || "Portfolio").trim(),
    category: (profile.category || "Wedding").trim(),
    fieldMap: profile.field_map || {},
  };
}

function readBundles() {
  if (!existsSync(PUBLISHED_DIR)) return [];
  const bundles = [];
  for (const slug of readdirSync(PUBLISHED_DIR, { withFileTypes: true })) {
    if (!slug.isDirectory()) continue;
    const manifestPath = join(PUBLISHED_DIR, slug.name, "post.json");
    if (!existsSync(manifestPath)) continue;
    bundles.push(JSON.parse(readFileSync(manifestPath, "utf8")));
  }
  return bundles;
}

// Absolute, publicly hosted URL for a bundle-relative image path.
function imageUrl(base, slug, relPath) {
  return `${base.replace(/\/$/, "")}/published_profile/${slug}/${relPath}`;
}

function slugify(text) {
  return String(text)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Build a Framer { type, value } entry appropriate to the target field's type.
function buildFieldValue(field, rawValue, alt) {
  if (rawValue === undefined || rawValue === null || rawValue === "") return null;
  switch (field.type) {
    case "string":
      return { type: "string", value: String(rawValue) };
    case "formattedText":
      return { type: "formattedText", value: String(rawValue), contentType: "markdown" };
    case "image":
      return alt ? { type: "image", value: String(rawValue), alt } : { type: "image", value: String(rawValue) };
    case "date":
      return { type: "date", value: String(rawValue) };
    case "link":
      return { type: "link", value: String(rawValue) };
    case "number":
      return { type: "number", value: Number(rawValue) };
    case "collectionReference":
      return { type: "collectionReference", value: String(rawValue) };
    default:
      console.warn(`  ! field "${field.name}" has unsupported type "${field.type}" — skipping`);
      return null;
  }
}

// Resolve the configured category name to an item id in the referenced
// Category collection. Matches the item's slug, falling back to its title field.
async function buildCategoryResolver(framer, collections, categoryField, categoryName) {
  if (!categoryField) return null;

  let refCollection = categoryField.collectionId
    ? collections.find((c) => c.id === categoryField.collectionId)
    : null;
  if (!refCollection) {
    refCollection = collections.find((c) => (c.name || "").trim().toLowerCase() === "category");
  }
  if (!refCollection) {
    console.warn("  ! could not locate the referenced Category collection");
    return null;
  }

  const items = await refCollection.getItems();
  const wanted = slugify(categoryName);

  // Match on slug first (robust, no field-shape assumptions), then on any
  // string field whose value matches the configured category name.
  let match = items.find((it) => it.slug && slugify(it.slug) === wanted);
  if (!match) {
    match = items.find((it) => {
      const data = it.fieldData || {};
      return Object.values(data).some(
        (f) => f && typeof f.value === "string" && slugify(f.value) === wanted
      );
    });
  }

  if (!match) {
    const available = items.map((it) => `"${it.slug}"`).join(", ");
    throw new Error(
      `Category "${categoryName}" not found in the "${refCollection.name}" collection. ` +
        `Available: ${available || "(none)"}. Create it in Framer or set profile.category in config.yaml.`
    );
  }
  console.log(`Filing items under category "${categoryName}" (item ${match.id}).`);
  return match.id;
}

async function main() {
  const apiKey = requireEnv("FRAMER_API_KEY");
  const projectUrl = requireEnv("FRAMER_PROJECT_URL");
  const imageBase = requireEnv("IMAGE_BASE_URL");
  const maxPerRun = parseInt(process.env.MAX_PUBLISH_PER_RUN || "0", 10); // 0 = no cap
  const { collectionName, category, fieldMap } = loadConfig();

  const bundles = readBundles();
  if (bundles.length === 0) {
    console.log("No bundles under published_profile/. Nothing to publish.");
    return;
  }

  const framer = await connect(projectUrl, apiKey);
  try {
    const collections = await framer.getCollections();
    const wantedId = (process.env.FRAMER_PROFILE_COLLECTION_ID || "").trim();
    const collection = wantedId
      ? collections.find((c) => c.id === wantedId)
      : collections.find((c) => (c.name || "").trim().toLowerCase() === collectionName.toLowerCase());

    if (!collection) {
      const names = collections.map((c) => `"${c.name}"`).join(", ");
      throw new Error(
        `Could not find collection ${wantedId || `named "${collectionName}"`}. ` +
          `Available collections: ${names || "(none)"}.`
      );
    }
    console.log(`Using collection "${collection.name}" (${collection.id}).`);

    const fields = await collection.getFields();
    console.log("Collection fields:");
    for (const f of fields) console.log(`  - "${f.name}" [${f.type}] (id=${f.id})`);

    const fieldByName = new Map(fields.map((f) => [(f.name || "").trim().toLowerCase(), f]));
    const firstOfType = (type) => fields.find((f) => f.type === type) || null;

    // Resolve each logical field to a real collection field: prefer the
    // configured name, then fall back to the only field of an unambiguous type.
    const resolve = (logical, fallbackType) => {
      const name = fieldMap[logical];
      let field = name ? fieldByName.get(String(name).trim().toLowerCase()) : null;
      if (!field && name) console.warn(`  ! mapped field "${name}" (${logical}) not found`);
      if (!field && fallbackType) {
        field = firstOfType(fallbackType);
        if (field) console.log(`  ~ ${logical}: falling back to "${field.name}" [${field.type}]`);
      }
      return field || null;
    };

    const FALLBACK_TYPE = {
      title: null,
      alt_text: null,
      preview: "image",
      date: "date",
      category: "collectionReference",
    };
    const resolved = Object.fromEntries(
      Object.entries(FALLBACK_TYPE).map(([logical, type]) => [logical, resolve(logical, type)])
    );

    const categoryItemId = await buildCategoryResolver(
      framer,
      collections,
      resolved.category,
      category
    );

    const existingItems = await collection.getItems();
    const itemBySlug = new Map(existingItems.filter((it) => it.slug).map((it) => [it.slug, it]));

    let added = 0;
    let updated = 0;
    for (const b of bundles) {
      const existing = itemBySlug.get(b.slug);
      if (!existing && maxPerRun > 0 && added >= maxPerRun) {
        console.log(`Reached MAX_PUBLISH_PER_RUN=${maxPerRun}; stopping new items.`);
        break;
      }

      const imgUrl = b.image ? imageUrl(imageBase, b.slug, b.image.path) : null;
      const alt = b.image?.alt || b.fields.alt_text;

      // logical field -> raw value
      const values = {
        title: b.fields.title,
        alt_text: b.fields.alt_text,
        preview: imgUrl,
        date: b.fields.date,
        category: categoryItemId,
      };

      const fieldData = {};
      for (const [logical, raw] of Object.entries(values)) {
        const field = resolved[logical];
        if (!field) continue;
        const entry = buildFieldValue(field, raw, logical === "preview" ? alt : undefined);
        if (entry) fieldData[field.id] = entry;
      }

      if (existing) {
        await collection.addItems([{ id: existing.id, slug: b.slug, fieldData }]);
        console.log(`* Updated "${b.fields.title}" (${b.slug}).`);
        updated++;
      } else {
        await collection.addItems([{ slug: b.slug, fieldData }]);
        console.log(`+ Added "${b.fields.title}" (${b.slug}).`);
        added++;
      }
    }

    if (added + updated > 0) {
      console.log("Publishing site…");
      await framer.publish();
      console.log(`Published. ${added} new, ${updated} updated.`);
    } else {
      console.log("Nothing to publish.");
    }
  } finally {
    await framer.disconnect();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
