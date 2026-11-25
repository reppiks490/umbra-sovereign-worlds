/** Advisory resource planning, not model quality or a reservation. */
const G=1024**3;
const roles=new Set(['reasoning','research','critique','coding','triage','retrieval','classification','ranking']);
export function requiredBytes(runtime,size){
 if(!Number.isSafeInteger(size)||size<=0||size>128*G)throw Error('invalid model size');
 if(runtime==='ollama')return size+(size>=6*G?2*G:G);
 if(runtime==='onnxruntime')return size*4+G;
 throw Error('unknown runtime');
}
export function planAdmission(catalog,role,free,busy=false){
 if(!roles.has(role)||!Number.isSafeInteger(free)||free<0||typeof busy!=='boolean'||!Array.isArray(catalog?.models)||catalog.models.length>356)throw Error('invalid admission input');
 const eligible=[],blocked=[],seen=new Set();
 for(const m of catalog.models){
  if(typeof m?.model!=='string'||!m.model||!Array.isArray(m.roles)||m.roles.some(r=>!roles.has(r)))throw Error('invalid model metadata');
  const key=m.runtime+':'+m.model;if(seen.has(key))throw Error('duplicate model');seen.add(key);
  const required=requiredBytes(m.runtime,m.size_bytes);
  if(!m.roles.includes(role))continue;
  const reason=busy&&m.runtime==='ollama'?'runtime_busy':free<required?'insufficient_memory':null;
  const row={runtime:m.runtime,model:m.model,required_bytes:required,reason};
  (reason?blocked:eligible).push(row);
 }
 const sort=(a,b)=>a.required_bytes-b.required_bytes||a.model.localeCompare(b.model)||a.runtime.localeCompare(b.runtime);
 return {schema:'umbra.polymind.admission.v1',role,free_bytes:free,eligible:eligible.sort(sort),blocked:blocked.sort(sort),research_qualified:false,production_authority:false};
}
