/**
 * UMBRA v5: an explicitly synthetic, settlement-aggregate civic-economy layer.
 * No claims of real elections, individuals, cognition, policy effectiveness, or external causality.
 * All cross-settlement transfers are double-entry / quantity conserving within this layer.
 * Methods are dependency-free and deterministic given an engine world and its keyed PRNG.
 */
export const SOCIETY_VERSION = '1.0.0';
export const FACTIONS = Object.freeze([
 {id:'stewards',name:'The Stewards',color:'#a1e9d2',priority:'restoration'},
 {id:'guilds',name:'The Guilds',color:'#e8c18f',priority:'exchange'},
 {id:'scholars',name:'The Scholars',color:'#aeb6f9',priority:'learning'},
 {id:'sentinels',name:'The Sentinels',color:'#f4a0ac',priority:'security'}
]);
const civicClamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const cents=x=>{const v=Math.round((x+Number.EPSILON)*1e6)/1e6;return v===0?0:v;};
const civicTotal=(a,key)=>a.reduce((sum,x)=>sum+x[key],0);

export function createSociety(world,random){
 const councils=world.sites.map((site,i)=>({id:i,faction:FACTIONS[Math.floor(random(world.seed,0,i,16)*4)].id,
  mandate:0,support:.54,treasury:0,taxCollected:0,grantsPaid:0,services:0,turnout:.64}));
 const unique=new Set(),corridors=[];
 for(let i=0;i<world.sites.length;i++)for(const j of world.near[i].slice(0,3)){
  const a=Math.min(i,j),b=Math.max(i,j),key=a+':'+b;if(unique.has(key))continue;unique.add(key);
  corridors.push({a,b,relation:+((random(world.seed,0,a*53+b,17)-.5)*.85).toFixed(6),pact:false,aid:0,visits:0,exposure:0});
 }
 return {version:SOCIETY_VERSION,councils,corridors,ledger:[],history:[],treasury:0,taxes:0,grants:0,aid:0,exposures:0,
  elections:0,pacts:0,ruptures:0,trust:.54,turn:0,fiscalResidual:0,foodResidual:0,entrySequence:0,
  lastFlow:{taxes:0,grants:0,aid:0,exposures:0,elections:0,ledgerEntries:0}};
}
function appendLedger(s,w,kind,from,to,amount,unit){
 if(!Number.isFinite(amount)||amount<0)throw new Error('Invalid civic ledger amount');
 if(amount===0)return;
 s.entrySequence++;
 s.ledger.unshift({id:s.entrySequence,tick:w.tick,kind,from,to,amount:cents(amount),unit});
 if(s.ledger.length>240)s.ledger.length=240;
}

export function advanceSociety(w,random,publish=()=>{}){
 const s=w.society;if(!s||s.version!==SOCIETY_VERSION)throw Error('Unsupported society model');
 const tick=w.tick,policy=w.policy,flow={taxes:0,grants:0,aid:0,exposures:0,elections:0,ledgerEntries:0};
 const moneyBefore=civicTotal(w.towns,'wealth')+civicTotal(s.councils,'treasury');
 const foodBefore=civicTotal(w.towns,'food');
 const announced=[];
 // Four competing synthetic social institutions: their winners affect local rates and investment priorities.
 for(const c of s.councils){const t=w.towns[c.id];if(t.p<=0)continue;
  if(tick%36===0){
   const choices=FACTIONS.map((f,k)=>{
    const hunger=civicClamp((42-t.food)/42,0,1),sickness=t.infected/Math.max(1,t.p),literacy=civicClamp(t.knowledge/270,0,1);
    const scores=[.45+.38*hunger+.28*policy.conservation,
                  .45+.3*policy.trade+.16*(1-hunger),
                  .45+.33*policy.innovation+.24*literacy,
                  .45+.32*policy.conflict+.15*sickness];
    return {f,score:scores[k]+.23*random(w.seed,tick,c.id,k+40)+.11*(f.id===c.faction)};
   });
   choices.sort((a,b)=>b.score-a.score || a.f.id.localeCompare(b.f.id));
   const previous=c.faction;c.faction=choices[0].f.id;c.mandate++;c.turnout=civicClamp(.46+.27*c.support+.18*random(w.seed,tick,c.id,48),0,1);
   s.elections++;flow.elections++;if(previous!==c.faction&&announced.length<3)announced.push({type:'election',site:c.id,title:w.sites[c.id].name+' chooses '+choices[0].f.name,detail:'A rule-based synthetic council election produces a new local administration.'});
  }
  const civicTaxRate=(c.faction==='stewards'?.028:c.faction==='guilds'?.016:c.faction==='scholars'?.034:.042)*(1-.24*policy.conflict);
  const due=Math.min(t.wealth,Math.max(0,t.wealth*civicTaxRate));
  t.wealth-=due;c.treasury+=due;c.taxCollected+=due;s.taxes+=due;flow.taxes+=due;
  appendLedger(s,w,'tax','town:'+c.id,'council:'+c.id,due,'credit');flow.ledgerEntries++;
  const need=civicClamp((37-t.food)/37,0,1)*.65+civicClamp((25-t.water)/25,0,1)*.35;
  const fraction=c.faction==='stewards'?.56:c.faction==='scholars'?.39:c.faction==='sentinels'?.27:.30;
  const grant=Math.min(c.treasury,(.25+.6*need+.25*policy.medicine)*fraction+c.treasury*.055);
  c.treasury-=grant;t.wealth+=grant;c.grantsPaid+=grant;s.grants+=grant;flow.grants+=grant;
  appendLedger(s,w,'grant','council:'+c.id,'town:'+c.id,grant,'credit');flow.ledgerEntries++;
  const effectiveness=(c.faction==='scholars'?1.5:1)*policy.innovation;
  t.knowledge+=grant*.014*effectiveness;
  t.infected=Math.max(0,t.infected-grant*.008*policy.medicine);
  c.services+=grant;
  const satisfaction=civicClamp(.62-.42*t.stress-.16*(t.infected/Math.max(1,t.p))+.16*policy.medicine-.13*civicTaxRate,0,1);
  c.support=civicClamp(c.support*.93+.07*satisfaction,0,1);
 }
 const tradeRoutes=new Set(w.trades.map(x=>Math.min(x.from,x.to)+':'+Math.max(x.from,x.to)));
 for(const road of s.corridors){const a=w.towns[road.a],b=w.towns[road.b];if(!a.p||!b.p){if(road.pact){road.pact=false;s.ruptures++;}continue;}
  const pairKey=road.a+':'+road.b;
  const trade=tradeRoutes.has(pairKey)?1:0;
  const stress=.5*(a.stress+b.stress),conflict=policy.conflict;
  const change=.0032*trade+.0015*policy.migration-.004*conflict*stress+(.5-random(w.seed,tick,road.a*97+road.b,50))*.005;
  road.relation=civicClamp(road.relation+change,-1,1);
  if(tick%23===0){if(!road.pact&&road.relation>.23){road.pact=true;s.pacts++;if(announced.length<3)announced.push({type:'treaty',site:road.a,title:'The '+w.sites[road.a].name+'–'+w.sites[road.b].name+' compact',detail:'Two settlements enter a synthetic mutual-aid pact.'});}
   else if(road.pact&&road.relation<-.15){road.pact=false;s.ruptures++;if(announced.length<3)announced.push({type:'rupture',site:road.a,title:'Treaty dissolved',detail:w.sites[road.a].name+' and '+w.sites[road.b].name+' suspend their aid corridor.'});}}
  if(!road.pact)continue;
  road.visits++;
  // Food aid transfers conserve the modeled food amount exactly; no new food is created by transfer.
  if(tick%3===0){const donor=a.food>b.food?a:b,receiver=donor===a?b:a;
   if(donor.food>67&&receiver.food<34){const qty=Math.min(4.5,(donor.food-62)*.17,(38-receiver.food)*.3);
    if(qty>0){donor.food-=qty;receiver.food+=qty;road.aid+=qty;s.aid+=qty;flow.aid+=qty;
     appendLedger(s,w,'aid','town:'+(donor===a?road.a:road.b),'town:'+(receiver===a?road.a:road.b),qty,'food');flow.ledgerEntries++;}}
  }
  // Exposure is directional and modeled, not a scientifically calibrated disease mechanism.
  if(tick%4===0){const source=a.infected/a.p>b.infected/b.p?a:b,dest=source===a?b:a;
   const exposure=civicClamp(source.infected/Math.max(1,source.p)*dest.p*.014*(1-policy.medicine),0,2.5);
   dest.infected=civicClamp(dest.infected+exposure,0,dest.p);road.exposure+=exposure;s.exposures+=exposure;flow.exposures+=exposure;
  }
 }
 // Double entry auditing is scoped to this module, excluding production/consumption in the base engine.
 s.fiscalResidual=cents(civicTotal(w.towns,'wealth')+civicTotal(s.councils,'treasury')-moneyBefore);
 s.foodResidual=cents(civicTotal(w.towns,'food')-foodBefore);
 s.treasury=civicTotal(s.councils,'treasury');s.trust=w.towns.reduce((a,t)=>a+(t.p? s.councils[t.id].support:0),0)/Math.max(1,w.towns.filter(t=>t.p).length);
 s.lastFlow=flow;s.turn=tick;
 if(tick%5===0){s.history.push({tick,treasury:+s.treasury.toFixed(2),trust:+s.trust.toFixed(4),pacts:s.corridors.filter(c=>c.pact).length,aid:+s.aid.toFixed(2)});if(s.history.length>240)s.history.shift();}
 for(const item of announced)publish(w,item.type,item.site,item.title,item.detail,4);
 if(!Number.isFinite(s.treasury)||Math.abs(s.fiscalResidual)>1e-5||Math.abs(s.foodResidual)>1e-5)throw new Error('Civic transfer accounting violation');
 return flow;
}

export function civicAudit(w){
 const s=w?.society;
 if(!s||typeof s!=='object')return {valid:false,issues:['Society module absent']};
 const issues=[];
 const denseEvery=(items,predicate)=>{
  for(let i=0;i<items.length;i++)if(!Object.hasOwn(items,i)||!predicate(items[i]))return false;
  return true;
 };
 if(s.version!==SOCIETY_VERSION)issues.push('Unsupported civic model version');
 const councils=Array.isArray(s.councils)?s.councils:null;
 const corridors=Array.isArray(s.corridors)?s.corridors:null;
 const ledger=Array.isArray(s.ledger)?s.ledger:null;
 if(!councils||!Array.isArray(w?.sites)||councils.length!==w.sites.length)issues.push('Council count mismatch');
 if(!corridors)issues.push('Invalid corridor collection');
 if(!ledger)issues.push('Invalid ledger collection');
 if(!Number.isFinite(s.fiscalResidual)||Math.abs(s.fiscalResidual)>1e-5)issues.push('Unbalanced fiscal transfers');
 if(!Number.isFinite(s.foodResidual)||Math.abs(s.foodResidual)>1e-5)issues.push('Unbalanced aid transfers');
 if(councils&&!denseEvery(councils,x=>x&&Number.isFinite(x.treasury)&&Number.isFinite(x.support)&&x.treasury>=0&&x.support>=0&&x.support<=1))issues.push('Invalid council state');
 if(corridors&&!denseEvery(corridors,x=>x&&Number.isFinite(x.relation)&&Math.abs(x.relation)<=1&&Number.isInteger(x.a)&&Number.isInteger(x.b)&&x.a<x.b))issues.push('Invalid corridor');
 if(ledger&&!denseEvery(ledger,x=>x&&Number.isFinite(x.amount)&&x.amount>=0))issues.push('Invalid ledger entry');
 return {valid:issues.length===0,issues,fiscalResidual:s.fiscalResidual,foodResidual:s.foodResidual,
   balancedEntries:s.entrySequence,activePacts:corridors?corridors.filter(x=>x?.pact).length:0};
}
