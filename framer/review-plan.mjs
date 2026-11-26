import {createHash} from "node:crypto";
import {readFileSync,readdirSync,realpathSync,existsSync} from "node:fs";
import {resolve,sep} from "node:path";
export const PROJECT_ID="iuFAULj0ZU07WpAzPDbI";
export const COLLECTION_ID="EEv3Nygkn";
export const FIELD_IDS=Object.freeze({title:"ua9FnvLmw",intro_1:"ivhGqPB2R",intro_2:"wIjEVkATu",meta_title:"aNQfJecqe",meta_description:"O9OI5IcMF",date:"Fi53MNOAk",body:"Jf1NQ7bt1",cover:"o4RZewo_g",image_1:"rcnbZcT2W",cover_alt:"Pp9IkO8p4"});
const hash=value=>createHash("sha256").update(value).digest("hex");
export function canonical(value){
  if(Array.isArray(value))return value.map(canonical);
  if(value&&typeof value==="object")return Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])]));
  return value;
}
export const contentHash=value=>hash(JSON.stringify(canonical(value)));
export function readBundles(directory){
  if(!existsSync(directory))throw new Error("Bundle directory does not exist: "+directory);
  return readdirSync(directory,{withFileTypes:true}).filter(e=>e.isDirectory()).sort((a,b)=>a.name.localeCompare(b.name)).map(entry=>{
    const base=realpathSync(resolve(directory,entry.name));
    const bundle=JSON.parse(readFileSync(resolve(base,"post.json"),"utf8"));
    const assetErrors=[];
    const assets=(Array.isArray(bundle.images)?bundle.images:[]).map(image=>{
      try{
        if(typeof image.path!=="string"||image.path.includes("\\")||image.path.startsWith("/")||image.path.split("/").includes(".."))throw new Error("unsafe image path");
        const path=realpathSync(resolve(base,image.path));
        if(!path.startsWith(base+sep))throw new Error("image escapes bundle directory");
        return {path:image.path,sha256:hash(readFileSync(path))};
      }catch(error){assetErrors.push("Image "+image.path+": "+error.message);return {path:image.path,sha256:null};}
    });
    return {bundle,directorySlug:entry.name,assets,assetErrors,sourceHash:contentHash({bundle,assets})};
  });
}
export function buildReviewPlan(records,baseline,now=new Date()){
  const common=[];
  if(!baseline||baseline.schemaVersion!==1||baseline.projectId!==PROJECT_ID||baseline.collectionId!==COLLECTION_ID||baseline.branchId!=="main"||!Array.isArray(baseline.items))common.push("A fresh, exact main-branch CMS baseline is required.");
  const age=now.getTime()-Date.parse(baseline?.capturedAt);
  if(!Number.isFinite(age)||age>86400000||age< -300000)common.push("CMS baseline is missing, expired (24 hours), or dated in the future.");
  const live=new Map();
  for(const item of baseline?.items||[]){
    if(!item.id||!item.slug||!/^[a-f0-9]{64}$/.test(item.contentHash||"")||live.has(item.slug))common.push("Baseline contains an invalid or duplicate CMS item.");
    live.set(item.slug,item);
  }
  const slugs=records.map(x=>x.bundle.slug);
  const items=records.map(({bundle,directorySlug,sourceHash,assets,assetErrors=[]})=>{
    const blockers=[...new Set(common),...assetErrors], fields=bundle.fields||{},slug=bundle.slug;
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug||"")||slug!==directorySlug)blockers.push("Slug must be safe and match its bundle directory.");
    if(slugs.filter(x=>x===slug).length!==1)blockers.push("Duplicate bundle slug.");
    if(!fields.title?.trim()||!fields.meta_title?.trim()||!fields.meta_description?.trim()||!bundle.body_markdown?.trim())blockers.push("Title, metadata and article body are required.");
    if((fields.meta_title||"").length>65||(fields.meta_description||"").length>165||/(?:…|\.\.\.)$/.test(fields.meta_description||""))blockers.push("Metadata is overlong or truncated; review the complete wording.");
    if(!/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(fields.date||"")||!Number.isFinite(Date.parse(fields.date))||new Date(fields.date).toISOString().slice(0,10)!==fields.date.slice(0,10))blockers.push("A verified publication date is required.");
    else if(Date.parse(fields.date)>now.getTime())blockers.push("Future-dated content must remain held until its approved publication date.");
    if(!Array.isArray(bundle.images)||!bundle.images.length||bundle.images.some(i=>!i.alt?.trim()))blockers.push("Every editorial image needs a verified alt description.");
    for(const match of (bundle.body_markdown||"").matchAll(/\{\{image_(\d+)\}\}/g))if(+match[1]<1||+match[1]>(bundle.images?.length||0))blockers.push("Unresolved image placeholder; never silently remove it.");
    const existing=live.get(slug), requestedFields=bundle.review?.fields;
    if(existing&&bundle.review?.baseContentHash!==existing.contentHash)blockers.push("Existing CMS content protected: provide its fresh baseContentHash before proposing an update.");
    if(existing&&(!Array.isArray(requestedFields)||!requestedFields.length||requestedFields.some(k=>!Object.hasOwn(FIELD_IDS,k))))blockers.push("Existing-item proposals require an explicit supported field allowlist.");
    return {slug,cmsItemId:existing?.id||null,operation:existing?"proposed-update":"proposed-new-draft",sourceHash,baselineContentHash:existing?.contentHash||null,fieldsForReview:requestedFields||Object.keys(FIELD_IDS),blockers:[...new Set(blockers)],assets,preview:{title:fields.title,meta_title:fields.meta_title,meta_description:fields.meta_description,date:fields.date,body_markdown:bundle.body_markdown},productionApproval:"not-granted"};
  });
  return {schemaVersion:1,mode:"review-only",generatedAt:now.toISOString(),projectId:PROJECT_ID,collectionId:COLLECTION_ID,baselineCapturedAt:baseline?.capturedAt||null,sourceSetHash:contentHash(items.map(x=>({slug:x.slug,sourceHash:x.sourceHash}))),cmsWritesEnabled:false,productionPublishEnabled:false,fieldIds:FIELD_IDS,items};
}
