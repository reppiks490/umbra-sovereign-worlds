import test from 'node:test';
import assert from 'node:assert/strict';
import {question} from '../mcp/market_academy.mjs';
import {solveMarket, compareEvidence} from '../mcp/market_symbolic.mjs';
test('independent symbolic route matches generated market tasks without the answer key',()=>{
 for(const lane of [3,11,21,22])for(const level of [1,2,5,6,10])for(let seed=1;seed<=100;seed++){
 const q=question(lane,level,seed);
 assert.equal(solveMarket({prompt:q.prompt,options:q.options}).answer,q.correct);
 }
});
test('unknown, malformed and missing options fail closed',()=>{
 assert.equal(solveMarket({prompt:'trade this asset',options:['a','b','c','d']}).status,'abstain');
 const q=question(3,2,7);
 assert.equal(solveMarket({prompt:q.prompt,options:['a','b','c','d']}).status,'abstain');
});
test('tool baseline preserves wrong raw model answers',()=>{
 const q=question(3,2,3);
 const wrong=q.options.find(x=>x!==q.correct);
 const r=compareEvidence({prompt:q.prompt,options:q.options},wrong,q.correct);
 assert.equal(r.model_correct,false);
 assert.equal(r.tool_correct,true);
 assert.equal(r.system_correct,true);
 assert.equal(r.source,'deterministic_tool');
});

import {gradeMarket} from '../mcp/market_academy.mjs';
import {verifyPair} from '../mcp/market_symbolic.mjs';
test('paired receipt evaluation never inflates model accuracy or counts duplicate tasks',()=>{
 const seed=900001,qs=[3,11,21,22].map(l=>question(l,2,seed));
 const make=name=>gradeMarket({model:name,manifest_digest:'a'.repeat(64)},qs,qs.map(q=>({id:q.id,answer:q.options.find(x=>x!==q.correct),confidence:95})));
 const a=make('qwen3:0.6b'),b=make('granite4:350m');
 const result=verifyPair([a,b]);
 assert.equal(result.model_correct,0);assert.equal(result.tool_correct,4);assert.equal(result.unique_questions,4);assert.equal(result.model_answers,8);assert.equal(result.high_confidence_errors,8);assert.equal(result.production_authority,false);
 assert.throws(()=>verifyPair([a,a]));assert.throws(()=>verifyPair([{...a,correct:4},b]));
});
