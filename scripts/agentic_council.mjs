/** Owner-local explicit file path and bounded synthetic experiment; no scheduler. */
import {learnCouncilExperience,forecastMission} from '../mcp/agentic_learning.mjs';
import {semanticRecall} from '../mcp/agentic_nexus.mjs';
import {resolve} from 'node:path';
import {createMission,runCouncil,replayExperience} from '../mcp/agentic_swarm.mjs';
import {readExperience,appendExperience} from '../mcp/agentic_memory.mjs';
const [action,file,seed='49021',steps='12',limit='2']=process.argv.slice(2);
try{
 if(!file||!['run','replay','recall','learn'].includes(action)||process.argv.length>7)throw Error('Usage: agentic_council.mjs run|replay|recall|learn MEMORY [SEED STEPS LIMIT]');
 const path=resolve(file),records=readExperience(path);
 if(action==='replay'){console.log(JSON.stringify({records:records.length,feedback:replayExperience(records),synthetic:true}));}
 else if(action==='learn'){
  const learner=learnCouncilExperience(records.slice(-64));
  const mission=createMission({seed:Number(seed),steps:Number(steps)});
  console.log(JSON.stringify({learner,forecast:forecastMission(learner,mission)}));
 }else if(action==='recall'){
  replayExperience(records.slice(-8));
  const query=createMission({seed:Number(seed),steps:Number(steps)});
  const model='sentence-transformers/all-MiniLM-L6-v2';
  console.log(JSON.stringify({synthetic:true,model,matches:semanticRecall(model,query,records.slice(-8))}));
 }else{
  const mission=createMission({seed:Number(seed),steps:Number(steps)});
  if(records.some(x=>x.mission.seed===mission.seed))throw Error('seed already recorded; use a new seed');
  const history=replayExperience(records.slice(-32));
  const result=await runCouncil(mission,{history,limit:Number(limit)});
  const memory=appendExperience(path,result);
  console.log(JSON.stringify({result,memory}));
 }
}catch(e){console.error(e.message);process.exitCode=1;}
