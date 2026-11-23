import {runCourt} from './court.mjs';
import {FACTIONS,civicAudit} from './society.mjs';
import {createWorld,stepWorld,advanceWorld,pairedExperiment,sensitivityExperiment,buildPassport,validateImport,DEFAULT_POLICY,policyOf,noise,clamp,ENGINE_VERSION} from './engine.mjs';
const $ = id => document.getElementById(id);
const fmt=n=>Math.round(n).toLocaleString('en-US');
const signed=n=>(n>0?'+':'')+fmt(n);
const PKEYS=Object.keys(DEFAULT_POLICY);
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const isMobile=()=>innerWidth<=660;
const state={world:createWorld(49021),twin:createWorld(49021,{...DEFAULT_POLICY,trade:0}),selected:2,
 playing:true,speed:1,lens:'population',lastStep:performance.now(),lastDraw:0,lastTelemetry:0,maxObservedTick:0,stepMs:0,renderMs:0,frameTimes:[],renderSamples:[],fps:0,quality:1,drag:false,lon:0,lat:0,zoom:1,offsetX:0,offsetY:0,hover:-1,exp:null,sweep:null,sweepId:0,sweepWorker:null,worker:null,expId:0,visible:!document.hidden};
const w=()=>state.world;
const civicCanvas=$('civic-network');
let civicHits=[];
const clampLabel=(x,max=30)=>String(x).slice(0,max);
const c=$('universe'),ctx=c.getContext('2d',{alpha:false});
const starSeed=85712,stars=Array.from({length:410},(_,i)=>({x:noise(starSeed,0,i,1),y:noise(starSeed,0,i,2),r:.38+1.2*noise(starSeed,0,i,3),alpha:.09+.53*noise(starSeed,0,i,4),phase:noise(starSeed,0,i,5)*6.283}));
const orbitDust=Array.from({length:350},(_,i)=>({t:noise(starSeed,1,i,4)*Math.PI*2,r:1.12+.55*noise(starSeed,1,i,3),alpha:.12+.7*noise(starSeed,1,i,2),size:.3+.9*noise(starSeed,1,i,1)}));
const terrain=Array.from({length:1800},(_,i)=>{const lat=Math.asin(noise(13989,0,i,1)*2-1),lon=noise(13989,0,i,2)*Math.PI*2,coast=Math.sin(lon*2.2+Math.sin(lat*4))*Math.cos(lat*5.2)+Math.cos(lon*4.2-lat*3.3)*.37+Math.sin(lon*9.1+lat*14.8)*.12;
 return{v:[Math.cos(lat)*Math.cos(lon),Math.sin(lat),Math.cos(lat)*Math.sin(lon)],land:coast>.18,bright:noise(13989,0,i,4)};});
let hitPoints=[];
const PLANET_LENSES=Object.freeze({
 population:{rgb:'141,246,205',text:'Population halo · brighter means more simulated residents.'},
 resources:{rgb:'255,168,119',text:'Resource stress · brighter means greater food and water shortage.'},
 infection:{rgb:'255,116,153',text:'Disease burden · brighter means a higher simulated infected share.'},
 climate:{rgb:'255,215,131',text:'Climate exposure · brighter means more vulnerability under current stress.'},
 civic:{rgb:'179,145,255',text:'Civic unrest · brighter means lower synthetic council support.'},
 off:{rgb:'',text:'Overlay disabled · ordinary globe and live settlement markers remain.'}
});
function lensSignal(world,site,town,lens){
 if(lens==='population')return town.p?clamp(Math.sqrt(town.p/300),0,1):0;
 if(lens==='resources')return town.p?clamp(.62*(1-town.food/Math.max(25,town.p*.36))+.38*(1-town.water/Math.max(22,town.p*.12)),0,1):0;
 if(lens==='infection')return town.p?clamp(town.infected/Math.max(1,town.p)*3.6,0,1):0;
 if(lens==='climate')return clamp((site.vulnerability*.58+world.climate*.42)*(town.p?1:.32),0,1);
 if(lens==='civic')return town.p?clamp((1-world.society.councils[site.id].support)*1.65,0,1):0;
 return 0;
}
function resizeCanvas(canvas,ratio=1.5){const box=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,ratio*state.quality);
 const nw=Math.max(1,Math.round(box.width*d)),nh=Math.max(1,Math.round(box.height*d));if(canvas.width!==nw||canvas.height!==nh){canvas.width=nw;canvas.height=nh;}return{W:box.width,H:box.height,d};}
function orient(v,longitude,latitude){const ca=Math.cos(longitude),sa=Math.sin(longitude),cb=Math.cos(latitude),sb=Math.sin(latitude);
 const a=v[0]*ca+v[2]*sa,z=-v[0]*sa+v[2]*ca;return [a,v[1]*cb-z*sb,v[1]*sb+z*cb];}
function drawUniverse(t){const start=performance.now(),{W,H,d}=resizeCanvas(c);ctx.setTransform(d,0,0,d,0,0);ctx.clearRect(0,0,W,H);
 ctx.fillStyle='#05090d';ctx.fillRect(0,0,W,H);
 const mobile=isMobile(),cx=W*(mobile?.52:.677)+state.offsetX,cy=H*(mobile?.63:.52)+state.offsetY,
 R=Math.min(W*(mobile?.39:.275),H*(mobile?.245:.41))*state.zoom;
 // Cinematic light scattering, sparse star lens field.
 const bg=ctx.createRadialGradient(cx-R*.19,cy-R*.15,R*.02,cx,cy,R*2.65);
 bg.addColorStop(0,'#23434a');bg.addColorStop(.21,'#0d2830');bg.addColorStop(.48,'#07151b');bg.addColorStop(1,'#05090d');ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
 for(const s of stars){const flick=reduceMotion?0:.14*Math.sin(t*.0015+s.phase);ctx.fillStyle=`rgba(197,234,217,${clamp(s.alpha+flick,0,1)})`;ctx.fillRect(s.x*W,s.y*H,s.r,s.r)}
 // Orbit rings are physically separated from the rotating planet surface.
 ctx.save();ctx.translate(cx,cy);ctx.rotate(-.26);const rings=[1.28,1.41,1.59,1.75];
 for(let i=0;i<rings.length;i++){ctx.beginPath();ctx.ellipse(0,0,R*rings[i],R*(.25+i*.018),0,0,Math.PI*2);ctx.strokeStyle=i===1?'rgba(157,246,211,.24)':'rgba(169,216,208,.08)';ctx.lineWidth=i===1?1:.7;ctx.stroke();}
 for(const mote of orbitDust){const a=mote.t+(reduceMotion?0:t*.000055*(1.7-mote.r));const r=R*mote.r,dx=Math.cos(a)*r,dy=Math.sin(a)*r*.27;ctx.fillStyle=`rgba(209,236,213,${mote.alpha*.45})`;ctx.fillRect(dx,dy,mote.size,mote.size)}ctx.restore();
 const outer=ctx.createRadialGradient(cx,cy,R*.85,cx,cy,R*1.28);outer.addColorStop(0,'#7feacf00');outer.addColorStop(.4,'#8aefcf18');outer.addColorStop(.66,'#78daba20');outer.addColorStop(1,'#78daba00');ctx.fillStyle=outer;ctx.fillRect(cx-R*1.3,cy-R*1.3,2.6*R,2.6*R);
 const lon=state.lon+(reduceMotion?0:t*.000016),lat=state.lat;
 const pos=(v,r=R)=>{const [x,y,z]=orient(v,lon,lat);return{x:cx+x*r,y:cy-y*r,z};};
 // Planet sphere, terminator and luminous atmospheric limb.
 ctx.save();ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.clip();
 const sphere=ctx.createRadialGradient(cx-R*.38,cy-R*.40,R*.06,cx+R*.26,cy+R*.22,R*1.37);
 sphere.addColorStop(0,'#387c76');sphere.addColorStop(.30,'#1d5258');sphere.addColorStop(.59,'#10323c');sphere.addColorStop(.81,'#071c25');sphere.addColorStop(1,'#020910');ctx.fillStyle=sphere;ctx.fillRect(cx-R,cy-R,2*R,2*R);
 const continents=reduceMotion?terrain.filter((_,i)=>i%2===0):terrain;
 for(const e of continents){const q=pos(e.v);if(q.z<=0)continue;
 const intensity=q.z*(.2+.8*e.bright);ctx.fillStyle=e.land?`rgba(150,206,146,${(.06+.26*intensity).toFixed(3)})`:`rgba(65,181,198,${(.03+.12*intensity).toFixed(3)})`;
 const rad=(e.land?2.9:1.4)*(R/320)*(.65+q.z);ctx.beginPath();ctx.ellipse(q.x,q.y,rad*1.4,rad,0,0,Math.PI*2);ctx.fill();}
 // A projected, state-driven field: every halo reflects one actual synthetic region.
 // Per-frame gradients are limited to visible sites; adaptive quality reduces draw count.
 if(state.lens!=='off'){
  const model=w(),lens=PLANET_LENSES[state.lens];
  ctx.save();ctx.globalCompositeOperation='screen';
  for(let i=0;i<model.sites.length;i++){
   if(state.quality<1&&i%2!==0)continue;
   const site=model.sites[i],town=model.towns[i],value=lensSignal(model,site,town,state.lens);
   if(value<.035)continue;
   const q=pos(site.pos,R*1.005);if(q.z<=.055)continue;
   const pulse=reduceMotion?1:(.94+.06*Math.sin(t*.0018+i*.57));
   const rad=R*(.04+.105*value)*(.65+.35*q.z)*pulse;
   const a=clamp((.10+.60*value)*q.z,0,.65);
   const glow=ctx.createRadialGradient(q.x,q.y,0,q.x,q.y,rad);
   glow.addColorStop(0,`rgba(${lens.rgb},${a.toFixed(3)})`);
   glow.addColorStop(.40,`rgba(${lens.rgb},${(a*.55).toFixed(3)})`);
   glow.addColorStop(1,`rgba(${lens.rgb},0)`);
   ctx.fillStyle=glow;ctx.fillRect(q.x-rad,q.y-rad,rad*2,rad*2);
  }
  ctx.restore();
 }
 // Latitude arcs visually establish that the world is rotating in three dimensions.
 for(let j=-5;j<=5;j++){const y=j/6,rc=Math.sqrt(1-y*y),pts=72;ctx.beginPath();let pen=false;for(let k=0;k<=pts;k++){
 const a=k/pts*2*Math.PI,q=pos([rc*Math.cos(a),y,rc*Math.sin(a)]);if(q.z<0){pen=false;continue;}if(!pen)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);pen=true;}
 ctx.strokeStyle='rgba(110,233,224,.13)';ctx.lineWidth=.6;ctx.stroke();}
 // Climate storm traces over the surface.
 for(let j=0;j<7;j++){const i=(Math.floor(w().tick/43)*7+j*5)%w().sites.length,site=w().sites[i];const pr=pos(site.pos);if(pr.z<=0)continue;
 ctx.beginPath();ctx.arc(pr.x,pr.y,3.5+7*Math.abs(Math.sin((t*.001+j)*.7)),0,Math.PI*2);ctx.strokeStyle=`rgba(186,221,182,${.10+.10*state.world.climate})`;ctx.stroke();}
 ctx.restore();
 // Atmosphere rim.
 ctx.beginPath();ctx.arc(cx,cy,R+.6,0,Math.PI*2);ctx.strokeStyle='#a3ffdc60';ctx.lineWidth=1.3;ctx.stroke();
 ctx.beginPath();ctx.arc(cx,cy,R*1.012,-.9,2.6);ctx.strokeStyle='#a0ffe96c';ctx.lineWidth=2.4;ctx.stroke();
 const arc=(i,j,amount)=>{const a=w().sites[i]?.pos,b=w().sites[j]?.pos;if(!a||!b)return;
 ctx.beginPath();let pen=false;for(let k=0;k<=25;k++){const z=k/25,p=a.map((q,h)=>q*(1-z)+b[h]*z),l=Math.hypot(...p),q=pos(p.map(v=>v/l),R+Math.sin(z*Math.PI)*R*.09);
 if(q.z<.02){pen=false;continue}if(!pen)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);pen=true;}
 ctx.strokeStyle=`rgba(244,199,132,${clamp(.23+amount*.025,.25,.7)})`;ctx.lineWidth=1.1;ctx.stroke();
 const phase=reduceMotion?.48:(t*.00015+(i+j)*.07)%1,p=a.map((q,h)=>q*(1-phase)+b[h]*phase),l=Math.hypot(...p),v=pos(p.map(q=>q/l),R+Math.sin(phase*Math.PI)*R*.09);
 if(v.z>0){ctx.fillStyle='#ffe5ab';ctx.shadowBlur=13;ctx.shadowColor='#edca83';ctx.beginPath();ctx.arc(v.x,v.y,2.4,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;}
 };
 w().trades.slice(0,22).forEach(r=>arc(r.from,r.to,r.amount));
 hitPoints=[];
 for(const site of w().sites){const town=w().towns[site.id],q=pos(site.pos);if(q.z<.01)continue;
 if(town.p>0){const r=2+Math.sqrt(town.p)*.3;ctx.fillStyle=site.group===2?'#ecc8ff':site.group%2?'#f9c18e':'#a9f7d2';ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=15;ctx.beginPath();ctx.arc(q.x,q.y,r,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
 if(!reduceMotion){ctx.strokeStyle='rgba(170,252,205,.12)';ctx.beginPath();ctx.arc(q.x,q.y,r+4+2*Math.sin(t*.002+site.id),0,Math.PI*2);ctx.stroke();}}
 if(site.id===state.selected){const pulse=reduceMotion?0:Math.sin(t*.003)*3;ctx.beginPath();ctx.arc(q.x,q.y,13+pulse,0,Math.PI*2);ctx.strokeStyle='#f7da9f';ctx.lineWidth=1.1;ctx.stroke();
 const labelX=clamp(q.x+22,4,W-114),labelY=clamp(q.y-21,18,H-8);ctx.font='12px monospace';ctx.fillStyle='#f9dfac';ctx.fillText(site.name,labelX,labelY);ctx.beginPath();ctx.moveTo(q.x+8,q.y-8);ctx.lineTo(labelX-6,labelY+3);ctx.lineTo(labelX,labelY+3);ctx.strokeStyle='#f9dfac6e';ctx.stroke();}
 hitPoints.push({...q,id:site.id,r:Math.max(12,4+Math.sqrt(town.p)*.3)});
 }
 // Reticle layers and telemetry overlay in rendered scene.
 ctx.strokeStyle='#c9e8d017';ctx.lineWidth=.65;ctx.setLineDash([2,8]);ctx.beginPath();ctx.arc(cx,cy,R*1.95,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
 const frameDt=performance.now()-start;state.renderMs=state.renderMs*.9+frameDt*.1;
 return{cx,cy,R};}
function chartPlot(canvas,seriesA,seriesB,metric='pop'){
 const cx=canvas.getContext('2d');const {W,H,d}=resizeCanvas(canvas,1.7);cx.setTransform(d,0,0,d,0,0);cx.clearRect(0,0,W,H);
 if(!seriesA.length)return;const N=Math.max(seriesA.length,seriesB.length),dataA=seriesA.map(p=>p[metric]??0),dataB=seriesB.map(p=>p[metric]??0);
 const vals=[...dataA,...dataB],mi=Math.min(...vals),ma=Math.max(...vals),pad=Math.max(1,(ma-mi)*.15),lo=mi-pad,hi=ma+pad;
 const left=39,right=9,top=15,bottom=28,ww=W-left-right,hh=H-top-bottom;
 cx.font='10px monospace';for(let k=0;k<5;k++){const y=top+k*hh/4;cx.strokeStyle='rgba(255,255,255,.08)';cx.beginPath();cx.moveTo(left,y);cx.lineTo(W-right,y);cx.stroke();cx.fillStyle='#8fa7a1';const val=hi-(hi-lo)*k/4;cx.fillText(Math.abs(val)>=10000?(val/1000).toFixed(0)+'k':Math.round(val).toLocaleString(),3,y+3);}
 const trace=(data,color)=>{if(data.length<2)return;cx.strokeStyle=color;cx.lineWidth=1.7;cx.beginPath();data.forEach((v,i)=>{const x=left+i/Math.max(1,N-1)*ww,y=top+(hi-v)/(hi-lo)*hh;if(!i)cx.moveTo(x,y);else cx.lineTo(x,y)});cx.stroke();};trace(dataB,'#bba6eb');trace(dataA,'#9ef0c3');
 cx.fillStyle='#9eb5ae';cx.fillText('0',left,H-7);cx.textAlign='right';cx.fillText('Turn '+state.world.tick,W-right,H-7);cx.textAlign='left';
}
function chartExperiment(canvas,data){const {W,H,d}=resizeCanvas(canvas);const cx=canvas.getContext('2d');cx.setTransform(d,0,0,d,0,0);cx.clearRect(0,0,W,H);if(!data)return;
 const a=data.paths.map(p=>p.diff),mi=Math.min(0,...a),ma=Math.max(0,...a);const scale=Math.max(1,ma-mi),n=a.length,gap=3,bw=(W-10)/n;
 a.forEach((v,i)=>{const h=Math.abs(v)/scale*(H-15),y=v>=0?H-8-h:8;cx.fillStyle=v>=0?'#a1f3ca':'#d6abbb';cx.fillRect(5+i*bw,y,Math.max(2,bw-gap),Math.max(2,h));});
 cx.strokeStyle='#ffffff50';cx.beginPath();cx.moveTo(0,H-8);cx.lineTo(W,H-8);cx.stroke();}

function drawCivicNetwork(now){
 const canvas=civicCanvas,cx=canvas.getContext('2d'),{W,H,d}=resizeCanvas(canvas,1.6);
 cx.setTransform(d,0,0,d,0,0);cx.clearRect(0,0,W,H);
 const world=w(),soc=world.society,layer=$('civic-layer').value;
 const radius=Math.min(W*.435,H*.42),centerX=W*.50,centerY=H*.52;
 // Equal-angle radial layout keeps the same settlement graph spatially stable across turns.
 const pts=world.sites.map((site,i)=>{
  const theta=i*2.399963229728653-Math.PI/2,ri=radius*(.63+.31*noise(world.seed,0,i,12));
  return {id:i,x:centerX+Math.cos(theta)*ri,y:centerY+Math.sin(theta)*ri};
 });
 const rings=[.25,.5,.75,1];for(const r of rings){cx.beginPath();cx.ellipse(centerX,centerY,radius*r,radius*r,0,0,Math.PI*2);cx.strokeStyle='rgba(120,232,207,.07)';cx.stroke();}
 cx.lineWidth=1;const active=world.towns;
 for(const link of soc.corridors){const a=pts[link.a],b=pts[link.b];if(!active[link.a].p||!active[link.b].p)continue;
  const isSelected=link.a===state.selected||link.b===state.selected;
  if(layer==='pacts'&&!link.pact&&!isSelected)continue;
  if(layer==='exposure'&&!link.pact)continue;
  const connection=link.relation;
  let alpha=layer==='relations'?Math.max(.09,Math.min(.85,Math.abs(connection)*.88)):.12;
  if(link.pact)alpha=Math.max(alpha,.43);if(isSelected)alpha=Math.max(alpha,.68);
  const col=layer==='exposure'?'255,164,171':connection<-.18?'247,143,157':'162,247,206';
  cx.strokeStyle=`rgba(${col},${alpha})`;cx.lineWidth=isSelected?1.55:link.pact?1.2:.6;
  cx.beginPath();cx.moveTo(a.x,a.y);const controlX=(a.x+b.x)/2+(centerX-(a.x+b.x)/2)*.34,controlY=(a.y+b.y)/2+(centerY-(a.y+b.y)/2)*.34;
  cx.quadraticCurveTo(controlX,controlY,b.x,b.y);cx.stroke();
  if(link.pact&&!reduceMotion){const phase=(now*.00023+(link.a+link.b)*.072)%1,u=1-phase;
   const x=u*u*a.x+2*u*phase*controlX+phase*phase*b.x,y=u*u*a.y+2*u*phase*controlY+phase*phase*b.y;
   cx.fillStyle=layer==='exposure'?'#f6c2ba':'#c0fae6';cx.beginPath();cx.arc(x,y,2,0,Math.PI*2);cx.fill();}
 }
 civicHits=[];
 for(const pt of pts){const t=world.towns[pt.id];const chief=soc.councils[pt.id],isSel=pt.id===state.selected;
  cx.globalAlpha=t.p?1:.29;cx.fillStyle=FACTIONS.find(f=>f.id===chief.faction)?.color||'#b7f2d8';
  cx.beginPath();cx.arc(pt.x,pt.y,(t.p?3.1:2.2)+(isSel?2:0),0,Math.PI*2);cx.fill();cx.globalAlpha=1;
  if(isSel){cx.strokeStyle='#ffe2a1';cx.lineWidth=1;cx.beginPath();cx.arc(pt.x,pt.y,10+(reduceMotion?0:1.8*Math.sin(now*.003)),0,Math.PI*2);cx.stroke();
   cx.font='11px monospace';cx.fillStyle='#fff4ce';cx.fillText(world.sites[pt.id].name,Math.min(W-100,pt.x+12),Math.max(12,pt.y-11));}
  civicHits.push({...pt,r:13});
 }
}
function drawCivicHistory(){const canvas=$('civic-history'),cx=canvas.getContext('2d'),{W,H,d}=resizeCanvas(canvas,1.7),s=w().society;
 cx.setTransform(d,0,0,d,0,0);cx.clearRect(0,0,W,H);
 const data=s.history;if(!data.length)return;
 const traces=[['trust','#b4f5dd'],['pacts','#eccc98'],['treasury','#a6b5f6']];
 traces.forEach(([key,color])=>{const vals=data.map(e=>e[key]),min=Math.min(0,...vals),max=Math.max(1,...vals),span=max-min;
  cx.strokeStyle=color;cx.lineWidth=1.6;cx.beginPath();vals.forEach((value,i)=>{const x=9+i/Math.max(1,vals.length-1)*(W-18),y=H-10-(value-min)/span*(H-22);if(i===0)cx.moveTo(x,y);else cx.lineTo(x,y)});cx.stroke();});
 cx.font='9px monospace';cx.fillStyle='#99b0a7';cx.fillText('TRUST',12,13);cx.fillStyle='#eccc98';cx.fillText('PACT',66,13);cx.fillStyle='#a6b5f6';cx.fillText('TREASURY',114,13);
}
function refreshCivic(){const world=w(),s=world.society,audit=civicAudit(world),count=s.corridors.filter(c=>c.pact).length;
 $('civic-pacts').textContent=fmt(count);$('civic-treasury').textContent=fmt(s.treasury);
 $('civic-trust').textContent=Math.round(s.trust*100)+'%';$('civic-elections').textContent=fmt(s.elections);$('civic-aid').textContent=fmt(s.aid);
 $('civic-map-label').textContent=$('civic-layer').selectedOptions[0].textContent.toUpperCase();
 const c=s.councils[state.selected],site=world.sites[state.selected];$('civic-selected-title').textContent=site.name;
 const faction=FACTIONS.find(f=>f.id===c.faction);$('civic-selected-faction').textContent=faction.name.toUpperCase()+' / '+faction.priority.toUpperCase();
 $('civic-selected-support').textContent=Math.round(c.support*100)+'%';$('civic-selected-treasury').textContent=fmt(c.treasury);
 $('civic-selected-treaties').textContent=fmt(s.corridors.filter(r=>r.pact&&(r.a===state.selected||r.b===state.selected)).length);
 $('civic-selected-turnout').textContent=Math.round(c.turnout*100)+'%';$('civic-cycle').textContent='TERM '+c.mandate;
 const root=$('civic-factions'),active=s.councils.filter(c=>world.towns[c.id].p).length,frag=document.createDocumentFragment();
 for(const f of FACTIONS){const count=s.councils.filter(c=>world.towns[c.id].p&&c.faction===f.id).length;
  const item=document.createElement('div'),name=document.createElement('span'),bar=document.createElement('i'),num=document.createElement('b');item.className='civic-faction';item.style.setProperty('--percent',(count/Math.max(1,active)*100).toFixed(1)+'%');item.style.setProperty('--faction-color',f.color);name.textContent=f.name.replace('The ','');num.textContent=count;item.append(name,bar,num);frag.append(item);}
 root.replaceChildren(frag);
 $('civic-audit').textContent=audit.valid?'BALANCED':'AUDIT FAILURE';$('civic-audit').style.color=audit.valid?'#bcf3d2':'#ff9da1';
 $('civic-fiscal-residual').textContent=s.fiscalResidual.toFixed(6);$('civic-food-residual').textContent=s.foodResidual.toFixed(6);
 const feed=$('civic-ledger'),rows=document.createDocumentFragment();for(const item of s.ledger.slice(0,8)){
  const li=document.createElement('li'),time=document.createElement('span'),body=document.createElement('span'),value=document.createElement('b');time.textContent='T '+item.tick;body.textContent=item.kind.toUpperCase()+' · '+item.from+' → '+item.to;value.textContent=item.amount.toFixed(2)+' '+item.unit;li.append(time,body,value);rows.append(li);}
 feed.replaceChildren(rows);drawCivicHistory();
}

const update={
 hero(){const world=w(),town=world.towns[state.selected],site=world.sites[state.selected];$('hero-turn').textContent=fmt(world.tick);$('hero-era').textContent='01';$('universe-id').textContent='UMBRA / '+world.seed;
 $('hero-pop').textContent=fmt(world.population);$('hero-sites').textContent=world.towns.filter(t=>t.p>0).length;$('hero-site').textContent=site.name;
 $('site-coords').textContent=Math.round(site.lat*180/Math.PI)+'° / '+Math.round(site.lon*180/Math.PI)+'°';$('elapsed').textContent='Turn '+fmt(world.tick);$('status').textContent=state.playing?'RUNNING':'PAUSED';
 $('stat-pop').textContent=fmt(world.population);$('stat-food').textContent=fmt(world.food);$('stat-knowledge').textContent=fmt(world.knowledge);
 $('stat-trade').textContent=fmt(world.tradeVolume);$('stat-bio').textContent=Math.round(world.biodiversity*100)+'%';$('stat-carbon').textContent=world.carbon.toFixed(1);
 $('stat-pop-delta').textContent=world.towns.filter(t=>t.p).length+' active settlements';$('active-count').textContent=world.towns.filter(t=>t.p).length+' ACTIVE';
 $('inv-foundings').textContent=fmt(world.foundings);$('inv-extinctions').textContent=fmt(world.extinctions);$('inv-migrations').textContent=fmt(world.migrations);$('inv-infected').textContent=fmt(world.infected);
 $('pause').textContent=state.playing?'Ⅱ PAUSE':'▷ RESUME';$('pause').setAttribute('aria-pressed',String(!state.playing));$('turn-range').max=String(Math.max(state.maxObservedTick,world.tick));$('turn-range').value=String(world.tick);$('turn-value').textContent=String(world.tick);
 },
 chart(){const metric=$('metric-pick').value;chartPlot($('worldline-chart'),w().series,state.twin.series,metric);
 const mapped={pop:'population',food:'food',knowledge:'knowledge',water:'water',carbon:'carbon',biodiversity:'biodiversity'};
 const a=mapped[metric]?w()[mapped[metric]]:w().series.at(-1)?.[metric]??0,b=mapped[metric]?state.twin[mapped[metric]]:state.twin.series.at(-1)?.[metric]??0;
 const diff=a-b;$('delta').textContent=(diff>=0?'+':'')+(Math.abs(diff)<10?diff.toFixed(2):fmt(diff));$('delta-caption').textContent=diff===0?'equal values in both worlds':diff>0?'your world is higher':'no-trade world is higher';},
 sites(){const world=w(),filter=$('site-search').value.toLowerCase().trim(),sort=$('site-sort').value;
 const eligible=world.sites.filter(s=>s.name.toLowerCase().includes(filter));eligible.sort((a,b)=>world.towns[b.id][sort]-world.towns[a.id][sort]||a.id-b.id);
 const root=$('sites-list'),frag=document.createDocumentFragment();for(const s of eligible){const town=world.towns[s.id],button=document.createElement('button');button.type='button';button.className='site-entry';button.role='listitem';button.setAttribute('aria-selected',String(s.id===state.selected));button.dataset.siteId=s.id;
 const dot=document.createElement('span');dot.className='s-dot'+(town.p?'':' dark');dot.setAttribute('aria-hidden','true');const name=document.createElement('span');name.className='s-name';name.textContent=s.name;
 const pop=document.createElement('span');pop.className='s-pop';pop.textContent=fmt(town.p);button.append(dot,name,pop);frag.append(button)}root.replaceChildren(frag);},
 selected(){const world=w(),t=world.towns[state.selected],s=world.sites[state.selected];$('selected-name').textContent=s.name;
 $('selected-status').textContent=t.p?'ACTIVE COLONY':'UNINHABITED';$('site-generation').textContent='GEN '+t.generation;
 $('site-description').textContent='Regional terrain fertility '+(s.fertility*100).toFixed(0)+'% · water potential '+(s.water*100).toFixed(0)+'% · vulnerability '+(s.vulnerability*100).toFixed(0)+'%. All values are synthetic.';
 const values=[['Residents',fmt(t.p)],['Food',fmt(t.food)],['Water',fmt(t.water)],['Health',Math.round(t.health*100)+'%'],['Knowledge',fmt(t.knowledge)],['Infected',fmt(t.infected)],['Energy',fmt(t.energy)],['Drought trait',Math.round(t.trait*100)+'%']];
 const root=$('site-measurements');const frag=document.createDocumentFragment();for(const [label,value] of values){const div=document.createElement('div'),a=document.createElement('span'),b=document.createElement('b');a.textContent=label;b.textContent=value;div.append(a,b);frag.append(div);}root.replaceChildren(frag);},
 chronicle(){const list=$('chronicle-events'),frag=document.createDocumentFragment();for(const e of w().events.slice(0,28)){
 const li=document.createElement('li'),a=document.createElement('span'),panel=document.createElement('div'),type=document.createElement('span'),title=document.createElement('div'),body=document.createElement('div');a.className='ev-turn';a.textContent='T '+e.tick;type.className='ev-type';type.textContent=e.type;title.className='ev-name';title.textContent=e.title;body.className='ev-body';body.textContent=e.detail;panel.append(type,title,body);li.append(a,panel);frag.append(li);}list.replaceChildren(frag);},
 all(){this.hero();this.chart();this.sites();this.selected();this.chronicle();refreshCivic();}
};
function selectSite(id){if(!Number.isInteger(id)||id<0||id>=w().sites.length)return;state.selected=id;const site=w().sites[id];state.lon=Math.atan2(site.pos[2],site.pos[0])-.3;state.lat=clamp(site.lat*.4,-.65,.65);update.selected();update.sites();update.hero();refreshCivic()}
function timelineStep(){const start=performance.now(),prev=w().tick;stepWorld(w());stepWorld(state.twin);state.maxObservedTick=Math.max(state.maxObservedTick,w().tick);state.stepMs=state.stepMs*.8+(performance.now()-start)*.2;
 if(w().tick%3===0||prev===0)update.all();else{update.hero();update.selected();update.chart();refreshCivic();} }
function replayTo(turn){turn=Math.round(clamp(turn,0,5000));const world=createWorld(w().seed,w().policy),twin=createWorld(world.seed,{...world.policy,trade:0});advanceWorld(world,turn);advanceWorld(twin,turn);state.world=world;state.twin=twin;state.maxObservedTick=Math.max(state.maxObservedTick,turn);state.lastStep=performance.now();update.all();}
function reset(newSeed=null,newPolicy=null){const seed=newSeed===null?w().seed:(Number(newSeed)>>>0)||1,cfg=policyOf(newPolicy||w().policy);state.world=createWorld(seed,cfg);state.twin=createWorld(seed,{...cfg,trade:0});state.lastStep=performance.now();state.maxObservedTick=0;state.exp=null;state.sweep=null;state.sweepId++;state.sweepWorker?.terminate();state.sweepWorker=null;state.expId++;state.worker?.terminate();state.worker=null;
 $('exp-mean').textContent=$('exp-range').textContent=$('exp-positive').textContent=$('exp-sd').textContent='—';$('exp-status').textContent='READY · NEW UNIVERSE';$('sweep-status').textContent='READY · NEW UNIVERSE';$('sweep-results').textContent='Run a new sensitivity experiment for this world.';update.all();}
for(const k of PKEYS){$('policy-'+k).addEventListener('input',()=>{$('out-'+k).textContent=$('policy-'+k).value+'%';});}
function readPolicy(){return Object.fromEntries(PKEYS.map(k=>[k,Number($('policy-'+k).value)/100]));}
$('forge-world').addEventListener('click',()=>{const raw=Number($('world-seed').value);if(!Number.isSafeInteger(raw)||raw<1||raw>4294967295){$('file-status').textContent='INVALID SEED · SELECT 1–4,294,967,295';return}reset(raw,readPolicy());state.playing=true;update.hero();$('file-status').textContent='NEW SYNTHETIC UNIVERSE STARTED · SEED '+raw;document.getElementById('observatory').scrollIntoView({behavior:reduceMotion?'auto':'smooth'});});
$('restore-policy').addEventListener('click',()=>{for(const k of PKEYS){$('policy-'+k).value=Math.round(DEFAULT_POLICY[k]*100);$('out-'+k).textContent=Math.round(DEFAULT_POLICY[k]*100)+'%'};});
$('pause').addEventListener('click',()=>{state.playing=!state.playing;state.lastStep=performance.now();update.hero();});
$('step').addEventListener('click',()=>{state.playing=false;timelineStep();update.hero();});
$('speed').addEventListener('change',()=>{state.speed=Number($('speed').value);});
$('reset').addEventListener('click',()=>{reset();state.playing=false;update.hero();});
$('turn-range').addEventListener('input',e=>{state.playing=false;replayTo(Number(e.target.value));update.hero();});
$('metric-pick').addEventListener('change',()=>update.chart());$('civic-layer').addEventListener('change',refreshCivic);
$('planet-lens').addEventListener('change',e=>{
 const next=e.target.value;
 if(!Object.hasOwn(PLANET_LENSES,next))return;
 state.lens=next;
 $('planet-lens-legend').textContent=PLANET_LENSES[next].text;
 $('planet-lens').closest('.planet-lens-panel').dataset.lens=next;
});
$('site-search').addEventListener('input',()=>update.sites());$('site-sort').addEventListener('change',()=>update.sites());
$('sites-list').addEventListener('click',e=>{const b=e.target.closest('[data-site-id]');if(b)selectSite(Number(b.dataset.siteId))});
civicCanvas.addEventListener('click',e=>{const r=civicCanvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;const near=civicHits.map(p=>({...p,d:Math.hypot(p.x-x,p.y-y)})).sort((a,b)=>a.d-b.d)[0];if(near&&near.d<near.r)selectSite(near.id);});
function runExperiment(){const id=++state.expId,button=$('experiment');button.disabled=true;const args={seed:w().seed,trials:Number($('trials').value),steps:Number($('horizon').value),baseline:{...DEFAULT_POLICY},treatment:readPolicy()};
 $('exp-status').textContent='COMPUTING · '+args.trials+' PAIRED SEEDS × '+args.steps+' TURNS';
 const finish=msg=>{if(id!==state.expId)return;button.disabled=false;if(!msg.ok){$('exp-status').textContent='FAILED · '+String(msg.error||'unknown').slice(0,120);return;}
 const result=msg.result;state.exp=result;$('exp-status').textContent='COMPLETE · DETERMINISTIC · NO REAL-WORLD VALIDATION';$('exp-mean').textContent=signed(result.mean);$('exp-range').textContent=signed(result.p05)+' to '+signed(result.p95);
 $('exp-positive').textContent=result.positive+' / '+result.trials;$('exp-sd').textContent=result.sd.toFixed(1);chartExperiment($('exp-chart'),result);};
 if(typeof Worker!=='undefined'){try{const worker=new Worker('./lab.worker.mjs',{type:'module'});state.worker?.terminate();state.worker=worker;
  worker.onmessage=e=>{worker.terminate();finish(e.data)};worker.onerror=e=>{worker.terminate();if(id!==state.expId)return;console.warn('Module worker failed; attempting bounded main-thread fallback',e.message);setTimeout(()=>{try{finish({ok:true,result:pairedExperiment(args)})}catch(error){finish({ok:false,error:String(error.message)})}},20)};worker.postMessage({version:ENGINE_VERSION,id,args});return;}catch(err){console.warn('Worker unavailable; using sliced main-thread fallback',err);}}
 // Fallback for file:// browsers: async yield before running, so controls can paint.
 setTimeout(()=>{try{finish({ok:true,result:pairedExperiment(args)})}catch(error){finish({ok:false,error:String(error.message)})}},20);
}
$('experiment').addEventListener('click',runExperiment);
function renderSensitivity(result){const wrap=$('sweep-results'),max=Math.max(1,...result.results.map(row=>Math.abs(row.mean))),frag=document.createDocumentFragment();
 for(const row of result.results){const box=document.createElement('div'),label=document.createElement('span'),rail=document.createElement('i'),value=document.createElement('b');box.className='sweep-row';rail.className='sweep-line';
  const relative=row.mean/max*50;box.style.setProperty('--start',(row.mean<0?50+relative:50)+'%');box.style.setProperty('--width',Math.abs(relative)+'%');box.style.setProperty('--bar-color',row.mean>=0?'#b4f5cf':'#f6acb0');
  label.textContent=row.policy.toUpperCase();value.textContent=(row.mean>0?'+':'')+row.mean.toFixed(1);box.title=row.policy+': seed-matched mean '+row.mean+', 5–95th percentiles '+row.p05+' to '+row.p95;
  box.append(label,rail,value);frag.append(box);}
 wrap.replaceChildren(frag);
}
function runSensitivity(){const id=++state.sweepId,button=$('run-sweep');button.disabled=true;const args={seed:w().seed,trials:Number($('sweep-trials').value),steps:Number($('sweep-horizon').value),delta:.2,base:readPolicy()};
 $('sweep-status').textContent='COMPUTING · SEVEN POLICY AXES × '+args.trials+' SEEDS';
 const finish=msg=>{if(id!==state.sweepId)return;button.disabled=false;if(!msg.ok){$('sweep-status').textContent='FAILED · '+String(msg.error||'unknown').slice(0,100);return;}
  state.sweep=msg.result;renderSensitivity(msg.result);$('sweep-status').textContent='COMPLETE · SEVEN CONTROLLED RULE COMPARISONS · SYNTHETIC ONLY';};
 if(typeof Worker!=='undefined')try{const worker=new Worker('./lab.worker.mjs',{type:'module'});state.sweepWorker?.terminate();state.sweepWorker=worker;
  worker.onmessage=e=>{worker.terminate();finish(e.data)};worker.onerror=e=>{worker.terminate();setTimeout(()=>{try{finish({ok:true,result:sensitivityExperiment(args)})}catch(error){finish({ok:false,error:String(error.message)})}},30)};
  worker.postMessage({version:ENGINE_VERSION,id,kind:'sensitivity',args});return;}catch(error){console.warn('Sensitivity worker unavailable; falling back',error);}
 setTimeout(()=>{try{finish({ok:true,result:sensitivityExperiment(args)})}catch(error){finish({ok:false,error:String(error.message)})}},30);
}
$('run-sweep').addEventListener('click',runSensitivity);
$('court-run').addEventListener('click',()=>{const button=$('court-run');button.disabled=true;$('court-counts').textContent='REPLAYING WORLD · CHECKING ENGINEERING INVARIANTS';
 setTimeout(()=>{try{const finding=runCourt(w());const parent=$('court-results'),frag=document.createDocumentFragment();
  for(const findingRow of finding.rows){const box=document.createElement('div'),index=document.createElement('small'),text=document.createElement('div'),name=document.createElement('strong'),desc=document.createElement('em'),badge=document.createElement('b');
   box.className='court-row';box.dataset.status=findingRow.status;index.textContent=findingRow.id;name.textContent=findingRow.label;desc.textContent=findingRow.evidence;badge.textContent=findingRow.status.toUpperCase();text.append(name,desc);box.append(index,text,badge);frag.append(box);}
  parent.replaceChildren(frag);$('court-counts').textContent=`${finding.counts.pass} PASSED / ${finding.counts.fail} FAILED / ${finding.counts.blocked} BLOCKED · SYNTHETIC ONLY`;
 }catch(error){$('court-counts').textContent='VERIFICATION FAILED · '+String(error.message).slice(0,125);}finally{button.disabled=false;}},15);});


$('download').addEventListener('click',async()=>{const data=buildPassport(w(),{...(state.exp?{experiment:state.exp}:{}),...(state.sweep?{sensitivity:state.sweep}:{})});const plain=JSON.stringify(data,null,2);
 if(globalThis.crypto?.subtle){const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(plain));data.checksum={algorithm:'SHA-256',scope:'unsigned payload before checksum insertion',hex:[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('')};}
 const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`umbra-world-${w().seed}-turn-${w().tick}.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
 $('file-status').textContent='EXPORT COMPLETE · LOCAL FILE · UNSIGNED CHECKSUM';});
$('import').addEventListener('change',async e=>{const file=e.target.files?.[0];if(!file)return;try{if(file.size>2_500_000)throw Error('Passport exceeds 2.5 MB');const raw=JSON.parse(await file.text()),valid=validateImport(raw);
 if(raw.checksum){if(raw.checksum.algorithm!=='SHA-256'||!/^[a-f0-9]{64}$/.test(raw.checksum.hex))throw Error('Unsupported checksum');if(!globalThis.crypto?.subtle)throw Error('Secure context required for checksum verification');
 const payload={...raw};delete payload.checksum;const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(payload,null,2)));const hex=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');if(hex!==raw.checksum.hex)throw Error('Passport checksum mismatch');}
 state.playing=false;reset(valid.seed,valid.policy);replayTo(valid.tick);
 for(const k of PKEYS){$('policy-'+k).value=Math.round(valid.policy[k]*100);$('out-'+k).textContent=Math.round(valid.policy[k]*100)+'%';}$('world-seed').value=valid.seed;
 $('file-status').textContent=`IMPORTED · SEED ${valid.seed} · TURN ${valid.tick} · RECOMPUTED FROM MODEL RULES`;}
 catch(error){$('file-status').textContent='IMPORT REJECTED · '+String(error.message).slice(0,120);}finally{e.target.value='';}});
const canvasPoint=e=>{const r=c.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};};
let dragStart=null;
c.addEventListener('pointerdown',e=>{dragStart={...canvasPoint(e),lon:state.lon,lat:state.lat};state.drag=false;c.setPointerCapture(e.pointerId);});
c.addEventListener('pointermove',e=>{if(!dragStart)return;const p=canvasPoint(e),dx=p.x-dragStart.x,dy=p.y-dragStart.y;
 if(Math.abs(dx)+Math.abs(dy)>6)state.drag=true;state.lon=dragStart.lon+dx*.005;state.lat=clamp(dragStart.lat-dy*.003,-1.2,1.2);});
c.addEventListener('pointerup',e=>{if(!dragStart)return;const p=canvasPoint(e);if(!state.drag){let best=null;for(const v of hitPoints){const d=Math.hypot(p.x-v.x,p.y-v.y);if(d<v.r+5&&(!best||d<best.distance))best={id:v.id,distance:d};}if(best)selectSite(best.id);}dragStart=null;});
c.addEventListener('pointercancel',()=>{dragStart=null});
c.addEventListener('wheel',e=>{if(!e.ctrlKey){e.preventDefault();state.zoom=clamp(state.zoom+(e.deltaY<0?.08:-.08),.75,1.45);}},{passive:false});
document.addEventListener('visibilitychange',()=>{state.visible=!document.hidden;state.lastStep=performance.now();});
function frame(now){requestAnimationFrame(frame);if(!state.visible)return;
 const interval=600/Math.max(1,state.speed);if(state.playing&&now-state.lastStep>=interval){const steps=Math.min(12,Math.floor((now-state.lastStep)/interval));for(let i=0;i<steps;i++)timelineStep();state.lastStep=now;}
 const frameInterval=reduceMotion?150:state.quality<1?33:16;if(now-state.lastDraw<frameInterval)return;
 const intervalObserved=state.lastDraw?now-state.lastDraw:null;
 const before=performance.now();drawUniverse(now);drawCivicNetwork(now);const end=performance.now();state.lastDraw=now;
 if(intervalObserved!==null&&intervalObserved<1000){state.frameTimes.push(intervalObserved);if(state.frameTimes.length>60)state.frameTimes.shift();}
 state.renderSamples.push(end-before);if(state.renderSamples.length>60)state.renderSamples.shift();
 if(now-state.lastTelemetry>=400){state.lastTelemetry=now;
 const avgFrame=state.frameTimes.reduce((a,b)=>a+b,0)/Math.max(1,state.frameTimes.length);
 const avgRender=state.renderSamples.reduce((a,b)=>a+b,0)/Math.max(1,state.renderSamples.length);
 // Measured wall-clock intervals between displayed frames; not theoretical render throughput.
 state.fps=state.frameTimes.length?Math.round(1000/Math.max(1,avgFrame)):0;$('fps').textContent=state.fps+' FPS';$('step-ms').textContent=state.stepMs.toFixed(2)+' ms';$('render-ms').textContent=state.renderMs.toFixed(2)+' ms';
 $('reduced-status').textContent=reduceMotion?'YES':'NO';if(avgRender>24&&state.quality===1&&!reduceMotion)state.quality=.75;else if(avgRender<13&&state.quality<1)state.quality=1;}
}
update.all();$('reduced-status').textContent=reduceMotion?'YES':'NO';requestAnimationFrame(frame);
// Test and diagnostic interface (read-only state; no remote execution endpoints).
Object.defineProperty(globalThis,'__UMBRA',{configurable:false,value:Object.freeze({engine:ENGINE_VERSION,getStatus:()=>({tick:w().tick,seed:w().seed,pop:w().population,trade:w().tradeVolume,fps:state.fps,playing:state.playing,lens:state.lens,renderMs:state.renderMs,stepMs:state.stepMs,experimental:!!state.exp,sensitivity:!!state.sweep,civic:civicAudit(w()),pacts:w().society.corridors.filter(x=>x.pact).length})})});
