/** Local, finite, read-only computation against UMBRA's actual repository engine. */
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,readFileSync,rmSync,statSync,existsSync,realpathSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,isAbsolute,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {simulate,pairedExperiment,DEFAULT_POLICY,ENGINE_VERSION,SITE_COUNT} from '../engine.mjs';
import {civicAudit} from '../society.mjs';
import {runCourt} from '../court.mjs';
import {createSimulationRunner} from '../scripts/umbra_independent_replay.mjs';
import {createBridge,serve} from './bridge.mjs';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const int=(minimum,maximum)=>({type:'integer',minimum,maximum});
const number=(minimum,maximum)=>({type:'number',minimum,maximum});
const object=(properties,required=Object.keys(properties))=>({type:'object',properties,required,additionalProperties:false});
const policy=object(Object.fromEntries(Object.keys(DEFAULT_POLICY).map(k=>[k,number(0,1)])),[]);
const common={seed:int(1,4294967295),steps:int(1,120),policy};
const spec=object(common,['seed','steps']);
const policyOf=p=>({...DEFAULT_POLICY,...p});
const envelope=(result,extra={})=>({schema:'umbra.mcp.computation.v1',engine:ENGINE_VERSION,synthetic:true,production_authority:false,semantic_mastery_certified:false,...extra,result});
const finiteResult=w=>{if(w.towns.length!==SITE_COUNT||!civicAudit(w).valid)throw Error('world integrity');const row={seed:w.seed,tick:w.tick,policy:w.policy};for(const k of ['population','food','water','energy','wealth','knowledge','infected','carbon','biodiversity','inequality']){if(!Number.isFinite(w[k]))throw Error('nonfinite');row[k]=w[k];}return row;};
function world(a){return simulate(a.seed,policyOf(a.policy),a.steps);}
function tool(name,description,inputSchema,invoke){return {name,description,inputSchema,invoke};}
function cleanEnv(){const env={};for(const k of ['SystemRoot','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG'])if(process.env[k]!==undefined)env[k]=process.env[k];return env;}
function fixedProcess(exe,args,options={}){const p=spawnSync(exe,args,{cwd:ROOT,timeout:25000,maxBuffer:262144,encoding:'utf8',windowsHide:true,env:cleanEnv(),...options});if(p.error||p.status!==0)throw Error('bounded subprocess failed');return p.stdout;}
function registered(a){const dir=mkdtempSync(join(tmpdir(),'umbra-mcp-'));try{fixedProcess(process.execPath,[join(ROOT,'scripts','umbra_advanced_lab.mjs'),'--id',a.id,'--out-dir',dir]);const path=join(dir,a.id+'.json');if(statSync(path).size>200000)throw Error('receipt too large');const r=JSON.parse(readFileSync(path,'utf8'));if(r.caseId!==a.id||r.engine!==ENGINE_VERSION||r.schema!=='umbra.synthetic.advanced-evidence.v1'||r.flags?.synthetic!==true||r.flags?.independentRealWorldValidity!==false||r.hash!==sha(r.results))throw Error('receipt mismatch');return envelope(r,{registered_case:true});}finally{rmSync(dir,{recursive:true,force:true});}}
function config(env){const python=env.UMBRA_MYRIAD_PYTHON,bank=env.UMBRA_MYRIAD_BANK; if(!python&&!bank)return null;if(!python||!bank||!isAbsolute(python)||!isAbsolute(bank)||!existsSync(python)||!existsSync(bank))throw Error('MYRIAD configuration invalid');return {python:realpathSync(python),bank:realpathSync(bank)};}
export function createUmbraTools(env=process.env){const c=config(env);const tools=[
 tool('umbra_simulate','Run the actual bounded UMBRA synthetic world engine; returns finite selected outcomes.',spec,a=>envelope(finiteResult(world(a)))),
 tool('umbra_paired_experiment','Common-seed paired policy experiment; synthetic effects only.',object({seed:common.seed,steps:common.steps,trials:int(2,8),baseline:policy,treatment:policy}),a=>envelope(pairedExperiment({...a,baseline:policyOf(a.baseline),treatment:policyOf(a.treatment)}),{difference_convention:'baseline_minus_treatment'})),
 tool('umbra_independent_replay','Execute two separate full worlds, check exact state digests and equality.',spec,a=>{const r=createSimulationRunner({simulate,validate:finiteResult,keyFor:(s,p,n)=>JSON.stringify([s,p,n])}).independentReplay(a.seed,policyOf(a.policy),a.steps);return envelope({firstDigest:r.firstDigest,secondDigest:r.secondDigest,executions:r.executions,summary:finiteResult(r.first)});}),
 tool('umbra_reality_court','Run model-internal engineering gates; not empirical validation.',spec,a=>envelope(runCourt(world(a),{replayLimit:120}))),
 tool('umbra_registered_case','Execute one registered case in U0301–U5300 with a finite subprocess budget and checked receipt.',object({id:{type:'string',pattern:'^U(0[3-9][0-9]{2}|[1-4][0-9]{3}|5[0-2][0-9]{2}|5300)$',maxLength:5}}),a=>{if(Number(a.id.slice(1))<301)throw Error('case out of range');return registered(a);})
 ];
 if(c)tools.push(tool('myriad_checkpoint_evaluate','Read-only replay of one configured v51 synthetic neural checkpoint; optional 32 numerical features return an 8-vector. Not an LLM or general reasoning model.',object({agent:int(1,10000),features:{type:'array',minItems:32,maxItems:32,items:number(-4,4)}},['agent']),a=>{const out=fixedProcess(c.python,[join(ROOT,'mcp','checkpoint_eval.py'),'--bank-root',c.bank],{input:JSON.stringify(a)+'\n',timeout:30000});const r=JSON.parse(out);if(r.schema!=='myriad.mcp.checkpoint_evaluation.v1'||r.agent!==a.agent||r.production_authority!==false)throw Error('checkpoint result mismatch');return r;}));
 return tools;}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{await serve(createBridge(createUmbraTools()),process.stdin,process.stdout);}catch{process.stderr.write('UMBRA MCP startup or transport failed\n');process.exitCode=1;}
}
