import {pairedExperiment,sensitivityExperiment,ENGINE_VERSION} from './engine.mjs';
self.onmessage = (event) => { try { const payload=event.data;
 if (!payload || payload.version!==ENGINE_VERSION) throw Error('Worker protocol mismatch');
 const result=payload.kind==='sensitivity'?sensitivityExperiment(payload.args):pairedExperiment(payload.args);self.postMessage({ok:true,id:payload.id,result});
} catch(error) {self.postMessage({ok:false,id:event.data?.id,error:String(error?.message||error)});}}
