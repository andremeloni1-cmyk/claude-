/** Review only: no CMS client, network call or publishing capability. */
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {dirname,resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {buildReviewPlan,readBundles} from "./review-plan.mjs";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const args=process.argv.slice(2);
const options={baseline:null,out:resolve(root,"review-output/plan.json"),check:false};
try {
  for(let i=0;i<args.length;i++){
    const arg=args[i];
    if(arg==="--check")options.check=true;
    else if(["--baseline","--out"].includes(arg)&&args[i+1]&&!args[i+1].startsWith("--"))options[arg.slice(2)]=resolve(args[++i]);
    else throw new Error("Unsupported argument: "+arg+". Publishing and CMS writes are disabled.");
  }
  const baseline=options.baseline?JSON.parse(readFileSync(options.baseline,"utf8")):null;
  const plan=buildReviewPlan(readBundles(resolve(root,"published")),baseline);
  mkdirSync(dirname(options.out),{recursive:true});
  writeFileSync(options.out,JSON.stringify(plan,null,2)+"\n");
  console.log("Review only: "+plan.items.length+" bundles; "+plan.items.filter(x=>x.blockers.length).length+" blocked. "+options.out);
  console.log("No CMS content changed. No site published. Production approval remains required.");
  if(options.check&&plan.items.some(x=>x.blockers.length))process.exitCode=1;
}catch(error){console.error(error.message);process.exitCode=1;}
