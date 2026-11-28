/** Explicit operator-local checkpoint path, no scheduled jobs or network. */
import {resolve} from 'node:path';
import {existsSync} from 'node:fs';
import {runEvolution,loadCheckpoint,saveCheckpoint} from '../mcp/autogenesis.mjs';
const [file,seed='49021',rounds='16',steps='12']=process.argv.slice(2);
if(!file||process.argv.length>6){console.error('Usage: node scripts/autogenesis_train.mjs CHECKPOINT SEED ROUNDS STEPS');process.exit(1);}
const path=resolve(file);
try{
 const previous=existsSync(path)?loadCheckpoint(path):undefined;
 const state=runEvolution({seed:Number(seed),rounds:Number(rounds),steps:Number(steps),previous});
 saveCheckpoint(path,state);
 console.log(JSON.stringify({schema:state.schema,synthetic:true,production_authority:false,metrics:state.metrics,neural:state.neural?{selected:state.neural.selected,linear_mse:state.neural.linear_mse,validation_mse:state.neural.validation_mse,student_teacher_mse:state.neural.student_teacher_mse}:null,holdout:state.holdout,champion:state.champion}));
}catch(e){console.error(e.message);process.exitCode=1;}
