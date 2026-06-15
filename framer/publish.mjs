/**
 * Push generated blog post bundles into the Framer CMS via the Framer Server API.
 *
 * Reads every bundle under ../published/<slug>/post.json, maps its fields onto
 * the configured Framer collection, embeds the photos (hosted at IMAGE_BASE_URL),
 * creates any post that does not yet exist in the collection, and publishes the
 * site. Re-runs are safe: posts whose slug already exists are skipped.
 *
 * Required environment:
 *   FRAMER_API_KEY       API key from Framer Site Settings -> General.
 *   FRAMER_PROJECT_URL   e.g. https://framer.com/projects/Sites--xxxxxxxx
 *   IMAGE_BASE_URL       Public base URL the committed images are served from,
 *                        e.g. https://raw.githubusercontent.com/<owner>/<repo>/<branch>
 * Optional:
 *   FRAMER_COLLECTION_ID   Pin an exact collection (overrides name match).
 *   MAX_PUBLISH_PER_RUN    Cap new posts pushed per run (default: all pending).
 */

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";
import { connect } from "framer-api";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..");
const PUBLISHED_DIR = join(REPO_ROOT, "published");

function requireEnv(name) {
  const v = (process.env[name] || "").trim();
  if (!v) throw new Error(`Missing required environment variable ${name}.`);
  return v;
}

function loadConfig() {
  const raw = readFileSync(join(REPO_ROOT, "config.yaml"), "utf8");
  const data = parseYaml(raw) || {};
  const blog = data.blog || {};
  return {
    collectionName: (blog.collection_name || "Blog").trim(),
    fieldMap: blog.field_map || {},
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
  return `${base.replace(/\/$/, "")}/published/${slug}/${relPath}`;
}

// Replace {{image_N}} placeholders in the body with hosted inline images.
function embedImages(markdown, slug, images, base) {
  let out = markdown;
  images.forEach((img, i) => {
    const url = imageUrl(base, slug, img.path);
    const alt = (img.alt || "").replace(/[[\]]/g, "");
    out = out.split(`{{image_${i + 1}}}`).join(`\n\n![${alt}](${url})\n\n`);
  });
  // Strip any placeholders the writer left unused.
  return out.replace(/\{\{image_\d+\}\}/g, "").trim();
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
    default:
      console.warn(`  ! field "${field.name}" has unsupported type "${field.type}" — skipping`);
      return null;
  }
}

async function main() {
  const apiKey = requireEnv("FRAMER_API_KEY");
  const projectUrl = requireEnv("FRAMER_PROJECT_URL");
  const imageBase = requireEnv("IMAGE_BASE_URL");
  const maxPerRun = parseInt(process.env.MAX_PUBLISH_PER_RUN || "0", 10); // 0 = no cap
  const { collectionName, fieldMap } = loadConfig();

  const bundles = readBundles();
  if (bundles.length === 0) {
    console.log("No bundles under published/. Nothing to publish.");
    return;
  }

  const framer = await connect(projectUrl, apiKey);
  try {
    const collections = await framer.getCollections();
    const wantedId = (process.env.FRAMER_COLLECTION_ID || "").trim();
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
    const fieldByName = new Map(fields.map((f) => [(f.name || "").trim().toLowerCase(), f]));
    const resolve = (logical) => {
      const name = fieldMap[logical];
      if (!name) return null;
      const field = fieldByName.get(String(name).trim().toLowerCase());
      if (!field) console.warn(`  ! mapped field "${name}" (${logical}) not found in collection — skipping`);
      return field || null;
    };

    const existingItems = await collection.getItems();
    const existingSlugs = new Set(existingItems.map((it) => it.slug).filter(Boolean));

    let added = 0;
    for (const b of bundles) {
      if (existingSlugs.has(b.slug)) {
        console.log(`= "${b.slug}" already in CMS — skipping.`);
        continue;
      }
      if (maxPerRun > 0 && added >= maxPerRun) {
        console.log(`Reached MAX_PUBLISH_PER_RUN=${maxPerRun}; stopping.`);
        break;
      }

      const cover = b.images.find((i) => i.is_cover) || b.images[0];
      const body = embedImages(b.body_markdown, b.slug, b.images, imageBase);

      // logical field -> raw value
      const values = {
        title: b.fields.title,
        excerpt: b.fields.excerpt,
        body,
        cover: cover ? imageUrl(imageBase, b.slug, cover.path) : null,
        date: b.fields.date,
        category: b.fields.category,
        meta_title: b.fields.meta_title,
        meta_description: b.fields.meta_description,
        author: b.fields.author,
        keywords: b.fields.keywords,
      };

      const fieldData = {};
      for (const [logical, raw] of Object.entries(values)) {
        const field = resolve(logical);
        if (!field) continue;
        const alt = logical === "cover" ? cover?.alt : undefined;
        const entry = buildFieldValue(field, raw, alt);
        if (entry) fieldData[field.id] = entry;
      }

      await collection.addItems([{ slug: b.slug, fieldData }]);
      console.log(`+ Added "${b.fields.title}" (${b.slug}).`);
      added++;
    }

    if (added > 0) {
      console.log("Publishing site…");
      await framer.publish();
      console.log(`Published. ${added} new post(s) live.`);
    } else {
      console.log("No new posts to add; skipping publish.");
    }
  } finally {
    await framer.disconnect();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
