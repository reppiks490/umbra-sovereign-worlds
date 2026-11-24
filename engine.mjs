import {createSociety,advanceSociety,civicAudit,SOCIETY_VERSION} from './society.mjs';
/**
 * UMBRA Sovereign Worlds v5 — transparent, deterministic SYNTHETIC simulation.
 * Does not represent real persons, economies, ecology, scientific predictions or empirical causality.
 * CRN: exogenous draws are functions of seed/tick/site/channel and shared across forks.
 * Versioned, dependency-free ES module. All steps are pure given previous state + policy.
 */
export const ENGINE_VERSION = '5.0.0';
export const SITE_COUNT = 42;
export const CHANNELS = ['weather','shock','fecundity','migration','discovery','disease','culture','founding'];
export const DEFAULT_POLICY = Object.freeze({trade:0.72, climate:0.38, medicine:0.48, innovation:0.58, migration:0.48, conservation:0.48, conflict:0.25});
const TAU = Math.PI*2;
const CLAMP = (v,a,b) => Math.max(a,Math.min(b,v));
export const clamp = CLAMP;
function hash32(x){ x=Math.imul((x^(x>>>16)),0x7feb352d);x=Math.imul((x^(x>>>15)),0x846ca68b);return (x^(x>>>16))>>>0; }
export function noise(seed,tick=0,index=0,channel=0){return hash32((seed>>>0)^Math.imul((tick+1)>>>0,0x9e3779b1)^Math.imul((index+31)>>>0,0x85ebca6b)^Math.imul((channel+71)>>>0,0xc2b2ae35))/4294967296;}
export function policyOf(raw={}) {return Object.fromEntries(Object.entries(DEFAULT_POLICY).map(([key,val])=>[key,CLAMP(Number.isFinite(+raw[key])?+raw[key]:val,0,1)]));}
const NAMES = ['Caelum','Corven','Lumen','Nacre','Kestra','Vesper','Orison','Thal','Eidolon','Selen','Morrow','Auralis','Kairo','Ardent','Ephyra','Altair','Nivan','Solace','Tamar','Ophis','Calla','Oberon','Mir','Aether','Helion','Tethys','Sora','Aven','Illya','Orun','Valen','Rhea','Cinder','Astra','Dusk','Nera','Fjord','Iona','Umber','Keth','Lyra','Eos'];
function makeSites(seed){const list=[];for(let i=0;i<SITE_COUNT;i++){
  const y=1-(i+0.5)*2/SITE_COUNT, r=Math.sqrt(1-y*y),lon=i*2.399963229728653;
  const x=Math.cos(lon)*r,z=Math.sin(lon)*r;
  list.push({id:i,name:NAMES[i],pos:[x,y,z],lat:Math.asin(y),lon:Math.atan2(z,x),
     fertility:.62+.65*noise(seed,0,i,1),water:.48+.46*noise(seed,0,i,2),mineral:.4+.55*noise(seed,0,i,3),
     vulnerability:.18+.72*noise(seed,0,i,4),group:i%7});
}return list}
function nearest(sites){return sites.map((s,i)=>sites.map((v,j)=>({j,d:Math.acos(CLAMP(s.pos.reduce((a,x,k)=>a+x*v.pos[k],0),-1,1))})).filter(v=>v.j!==i).sort((a,b)=>a.d-b.d).slice(0,6).map(v=>v.j));}
function event(state,type,siteId,title,detail,weight=1){const e={tick:state.tick,type,siteId,title,detail,weight};state.events.unshift(e);if(state.events.length>180)state.events.length=180;}
export function createWorld(seed=49021,policy=DEFAULT_POLICY){seed=(Number(seed)>>>0)||1;const cfg=policyOf(policy), sites=makeSites(seed), near=nearest(sites);
 const towns=sites.map((s,i)=>{const founded=i%5===0||i===2;
   return {id:i,p:founded?36+Math.floor(noise(seed,0,i,5)*20):0,food:founded?65:0,water:founded?57:0,
     energy:founded?28:0,knowledge:founded?13+Math.floor(noise(seed,0,i,8)*5):0,
     health:.86,wealth:founded?35:0,infected:0,trait:.30+.42*noise(seed,0,i,9),
     generation:0,culture:s.group,emissions:0,stress:0};});
 const w={engine:ENGINE_VERSION,seed,policy:cfg,tick:0,sites,near,towns,
   climate:0,season:0,population:0,food:0,water:0,energy:0,knowledge:0,wealth:0,
   infected:0,tradeVolume:0,migrations:0,foundings:0,extinctions:0,biodiversity:1,carbon:0,inequality:0,
   trades:[],events:[],series:[],snapshots:[],historyLimit:1200};
 w.society=createSociety(w,noise);
 event(w,'genesis',2,'The first signal','Ten seed colonies arrive with limited food and no established exchange network.',5);
 recalc(w);saveSample(w);return w; }
function recalc(w){let pop=0,food=0,water=0,energy=0,wealth=0,knowledge=0,infected=0,wealthWeighted=0;
 for(const t of w.towns){pop+=t.p;food+=t.food;water+=t.water;energy+=t.energy;wealth+=t.wealth;knowledge+=t.knowledge;infected+=t.infected;wealthWeighted+=t.wealth*t.p}
 w.population=pop;w.food=Math.round(food);w.water=Math.round(water);w.energy=Math.round(energy);w.wealth=Math.round(wealth);w.knowledge=Math.round(knowledge);w.infected=Math.round(infected);
 const active=w.towns.filter(t=>t.p).length;const mean=active?wealth/active:0;
 w.inequality=active?CLAMP(w.towns.reduce((s,t)=>s+(t.p?Math.abs(t.wealth-mean):0),0)/(active*Math.max(mean,1)*2),0,1):0;
}
function saveSample(w){const point={tick:w.tick,pop:w.population,food:w.food,water:w.water,energy:w.energy,knowledge:w.knowledge,treasury:+w.society.treasury.toFixed(2),trust:+w.society.trust.toFixed(4),pacts:w.society.corridors.filter(c=>c.pact).length,
 infected:w.infected,wealth:w.wealth,carbon:+w.carbon.toFixed(2),biodiversity:+w.biodiversity.toFixed(3),trade:w.tradeVolume,inequality:+w.inequality.toFixed(3)};
 w.series.push(point);if(w.series.length>w.historyLimit)w.series.shift();
 if(w.tick%25===0){w.snapshots.push({tick:w.tick,pop:w.population,food:w.food,health:1-w.infected/Math.max(1,w.population),carbon:point.carbon});if(w.snapshots.length>120)w.snapshots.shift();}
}
function partialTrade(w,vol=0){let remaining=vol;const p=w.policy;
 for(let i=0;i<w.towns.length&&remaining>0;i++){const a=w.towns[i];if(!a.p||a.food<32)continue;
  const candidates=w.near[i].filter(j=>{const t=w.towns[j];return t.p&&t.food<24;});if(!candidates.length)continue;
  candidates.sort((x,y)=>w.towns[x].food-w.towns[y].food||x-y);
  const j=candidates[0],b=w.towns[j];const take=Math.min(remaining,Math.floor((a.food-25)*p.trade*.43),15,Math.ceil((30-b.food)*.7));
  if(take<=0)continue;a.food-=take;b.food+=take;const payment=Math.min(b.wealth,take*.12);a.wealth+=payment;b.wealth-=payment;remaining-=take;w.tradeVolume+=take;w.trades.push({from:i,to:j,amount:take});
 }
}
export function stepWorld(w){if(!w||w.engine!==ENGINE_VERSION)throw new Error('Wrong world version');const tick=++w.tick,p=w.policy;
 const season=Math.sin(tick*.085+w.seed%43),stormCenter=Math.floor(noise(w.seed,Math.floor(tick/43),0,11)*SITE_COUNT);
 const storm=tick%43<12;w.season=season;w.climate=storm?(.4+p.climate*.6):p.climate*.48;
 w.trades=[];const exports=[];const newBorn=new Set();
 // All exogenous signals use seed/time/site/channel, independent of endogenous state and of policy.
 for(let i=0;i<SITE_COUNT;i++){
  const t=w.towns[i],s=w.sites[i];if(t.p<=0)continue;
  const nearbyStorm=storm&&(i===stormCenter||w.near[stormCenter].slice(0,2).includes(i));
  const weather=.68+.27*Math.sin(tick*.095+s.lat*3)+.3*noise(w.seed,tick,i,0);
  const climateLoss=p.climate*(.23+.55*s.vulnerability)*(nearbyStorm?1.65:.55);
  const recovery=.06+.28*p.conservation;
  const yieldFood=(3.7+Math.sqrt(t.p)*2.9)*s.fertility*weather*(1-climateLoss)*(1+t.knowledge*.0018);
  t.food=CLAMP(t.food+yieldFood-t.p*.36,0,270);
  t.water=CLAMP(t.water+2.5*s.water+weather*3-t.p*.115-climateLoss*8,0,180);
  const generatedEnergy=(1.4+s.mineral*1.7)*(1+t.knowledge*.003);
  t.energy=CLAMP(t.energy+generatedEnergy-t.p*.085,0,200);
  const shortage=CLAMP((19-t.food)/19,0,1)*.60+CLAMP((20-t.water)/20,0,1)*.36+CLAMP((9-t.energy)/9,0,1)*.18;
  const diseasePressure=(.03+.12*noise(w.seed,tick,i,6))*(1-p.medicine)*(.6+.4*t.p/90);
  const cured=Math.min(t.infected,t.infected*(.15+.29*p.medicine));
  t.infected=CLAMP(t.infected+diseasePressure*t.p+cured*(-1)+(shortage>.2?shortage*.05*t.p:0),0,t.p);
  t.stress=CLAMP(shortage+t.infected/Math.max(1,t.p)*.42+climateLoss*.2,0,1);
  const disaster=storm&&nearbyStorm?Math.min(t.p,2+Math.floor(3*noise(w.seed,tick,i,1)))*p.climate:0;
  const births=(t.food>10&&t.water>9?1+Math.floor(noise(w.seed,tick,i,2)*2):0)*(1-.2*t.stress);
  const loss=t.p*(.004*shortage+.0016*t.infected/Math.max(1,t.p)+.006*p.conflict*t.stress)+disaster*.22;
  t.p=CLAMP(Math.round((t.p+births-loss)*100)/100,0,1200);
  if(t.p<1){t.p=0;t.food=0;t.water=0;w.extinctions++;event(w,'extinction',i,s.name+' falls silent','An exhausted colony has lost its last residents.',5);continue;}
  t.health=CLAMP(1-t.stress*.6-t.infected/Math.max(1,t.p)*.4,.05,1);
  t.knowledge=CLAMP(t.knowledge+(.05+.37*p.innovation)*(1-t.stress)*(.5+noise(w.seed,tick,i,4))-.03*p.conflict,0,1000);
  t.wealth=CLAMP(t.wealth+generatedEnergy*.3+births*.27-loss*.6-t.stress*.5,0,3000);
  t.emissions=t.p*.004+.025*generatedEnergy*(1-p.conservation);
  w.carbon=CLAMP(w.carbon+t.emissions*.008-.015*p.conservation,0,1000);
  if(t.food<13&&t.p>13&&tick%5===0){const dest=w.near[i].filter(j=>w.towns[j].p&&w.towns[j].food>36).sort((j,k)=>w.towns[k].food-w.towns[j].food)[0];
     if(dest!==undefined){const qty=Math.min(8,Math.max(1,Math.floor(t.p*.08*p.migration)));if(qty>0){t.p-=qty;w.towns[dest].p+=qty;w.migrations+=qty;event(w,'migration',dest,'Passage to '+w.sites[dest].name,qty+' residents depart '+s.name+' after resource shortages.',2)}}}
  if(t.food>80&&t.p>63&&tick%7===0&&noise(w.seed,tick,i,7)<.7){const dest=w.near[i].find(j=>!w.towns[j].p&&!newBorn.has(j));
     if(dest!==undefined){const child=w.towns[dest];const count=16;t.p-=count;t.food-=42;child.p=count;child.food=42;child.water=48;child.energy=13;child.knowledge=t.knowledge*.65;child.wealth=t.wealth*.22;child.trait=CLAMP(t.trait+(noise(w.seed,tick,i,3)-.5)*.14,0,1);child.generation=t.generation+1;child.culture=t.culture;newBorn.add(dest);w.foundings++;event(w,'founding',dest,'A new light in '+w.sites[dest].name,'The colony inherits lineage '+child.generation+' and research traditions from '+s.name+'.',4);}}
 }
 if(p.trade>0)partialTrade(w,Math.ceil(p.trade*SITE_COUNT*1.2));
 // Endogenous shared discovery per neighbor represents cultural diffusion; no per-person agency claimed.
 for(let i=0;i<SITE_COUNT;i++){const t=w.towns[i];if(!t.p)continue;
  const peers=w.near[i].filter(j=>w.towns[j].p);if(peers.length){const max=Math.max(...peers.map(j=>w.towns[j].knowledge));if(max>t.knowledge)t.knowledge+=Math.min(1.4,(max-t.knowledge)*.017)*p.innovation;}}
 w.biodiversity=CLAMP(w.biodiversity+.0005*p.conservation-.000016*w.carbon-.00008*p.climate,.02,1);
 if(tick%43===1)event(w,'climate',stormCenter,'Storm at '+w.sites[stormCenter].name,'A synchronized weather disturbance crosses this region and its neighbors.',3);
 advanceSociety(w,noise,(world,type,id,title,detail,weight)=>event(world,type,id,title,detail,weight));
 if(tick%67===0){const s=Math.floor(noise(w.seed,tick,0,12)*SITE_COUNT);event(w,'discovery',s,'A new method emerges in '+w.sites[s].name,'A localized research network spreads productivity improvements through neighboring settlements.',3)}
 recalc(w);saveSample(w);return w;}
export function advanceWorld(w,n=1){if(!Number.isSafeInteger(n)||n<0||n>5000)throw new Error('Invalid step count');for(let i=0;i<n;i++)stepWorld(w);return w}
export function total(towns){return towns.reduce((a,t)=>a+t.p,0)}
export function simulate(seed,policy,steps=240){return advanceWorld(createWorld(seed,policy),steps)}
/** Paired replicate ensemble: identical exogenous seeds, only one policy differs. Synthetic model-internal treatment effect. */
export function pairedExperiment({seed=49021,trials=16,steps=240,baseline=DEFAULT_POLICY,treatment={...DEFAULT_POLICY,trade:0}}={}){
 if(!Number.isSafeInteger(trials)||!Number.isSafeInteger(steps))throw new RangeError('Paired experiment requires finite integer trials and steps');
 trials=CLAMP(trials,2,64);steps=CLAMP(steps,1,2000);const cfgA=policyOf(baseline),cfgB=policyOf(treatment);
 const paths=[],differences=[];
 for(let k=0;k<trials;k++){const runSeed=hash32((seed>>>0)+Math.imul(k+1,0x9e3779b1));const a=createWorld(runSeed,cfgA),b=createWorld(runSeed,cfgB);
  for(let t=0;t<steps;t++){stepWorld(a);stepWorld(b)}
  const diff=a.population-b.population;differences.push(diff);paths.push({seed:runSeed,baseline:a.population,treatment:b.population,diff,foodDiff:a.food-b.food,emissionsDiff:a.carbon-b.carbon});}
 const vals=[...differences].sort((a,b)=>a-b),mean=differences.reduce((a,b)=>a+b,0)/trials;
 const quantile=q=>{const x=q*(vals.length-1),i=Math.floor(x);return vals[i]+(vals[Math.ceil(x)]-vals[i])*(x-i)};
 const sd=Math.sqrt(differences.reduce((a,b)=>a+(b-mean)**2,0)/Math.max(1,trials-1));
 return {version:ENGINE_VERSION,seed,trials,steps,baseline:cfgA,treatment:cfgB,mean:+mean.toFixed(2),median:+quantile(.5).toFixed(2),p05:+quantile(.05).toFixed(2),p95:+quantile(.95).toFixed(2),sd:+sd.toFixed(2),positive:differences.filter(x=>x>0).length,paths};}

/** Exploratory one-at-a-time sensitivity telescope; never a calibrated real-world effect. */
export function sensitivityExperiment({seed=49021,trials=8,steps=180,delta=.2,base=DEFAULT_POLICY}={}){
 if(!Number.isInteger(trials)||trials<2||trials>32||!Number.isInteger(steps)||steps<1||steps>1000||!Number.isFinite(delta)||delta<=0||delta>1)throw Error('Invalid sensitivity design');
 const basePolicy=policyOf(base),results=[];
 for(const key of Object.keys(DEFAULT_POLICY)){
  const lo={...basePolicy,[key]:Math.max(0,basePolicy[key]-delta)};
  const hi={...basePolicy,[key]:Math.min(1,basePolicy[key]+delta)};
  const paired=pairedExperiment({seed,trials,steps,baseline:hi,treatment:lo});
  const width=hi[key]-lo[key];
  results.push({policy:key,low:lo[key],high:hi[key],span:width,mean:paired.mean,median:paired.median,p05:paired.p05,p95:paired.p95,sd:paired.sd,
   positive:paired.positive,trials,meanPerUnit:width?+(paired.mean/width).toFixed(2):0});
 }
 return {version:ENGINE_VERSION,kind:'exploratory sensitivity sweep',seed,trials,steps,delta,basePolicy,results,
  caution:'Differences are internal to this uncalibrated synthetic model; this is not a real-world causal or policy estimate.'};
}

export function buildPassport(w,extra={}){return {product:'UMBRA / Sovereign Worlds',version:ENGINE_VERSION,mode:'synthetic model experiment',createdAt:new Date().toISOString(),seed:w.seed,policy:w.policy,tick:w.tick,totals:{population:w.population,food:w.food,water:w.water,energy:w.energy,knowledge:w.knowledge,infected:w.infected,wealth:w.wealth,carbon:w.carbon,biodiversity:w.biodiversity,inequality:w.inequality,tradeVolume:w.tradeVolume,society:{version:SOCIETY_VERSION,treasury:w.society.treasury,trust:w.society.trust,elections:w.society.elections,treaties:w.society.corridors.filter(x=>x.pact).length,aid:w.society.aid,accounting:civicAudit(w),ledger:w.society.ledger}},series:w.series,events:w.events,assumptions:['Rule-based settlement aggregates and council factions, not individual intelligent agents','All environmental, civic, electoral and social dynamics are synthetic and uncalibrated','No real-world forecast, empirical causal effect or policy recommendation','A fork with common random numbers establishes only model-internal differences'],...extra};}
export function validateImport(data){if(!data||typeof data!=='object'||Array.isArray(data))throw Error('Invalid passport');if(data.product!=='UMBRA / Sovereign Worlds'||data.version!==ENGINE_VERSION)throw Error('Unsupported passport version');if(!Number.isSafeInteger(data.seed)||data.seed<1||!Number.isSafeInteger(data.tick)||data.tick<0||data.tick>5000)throw Error('Bad seed or tick');
 if(!data.policy||typeof data.policy!=='object'||Object.keys(DEFAULT_POLICY).some(key=>!Number.isFinite(data.policy[key])||data.policy[key]<0||data.policy[key]>1))throw Error('Invalid policy');return {seed:data.seed,tick:data.tick,policy:policyOf(data.policy)};}
