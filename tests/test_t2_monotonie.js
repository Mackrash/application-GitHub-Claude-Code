// Test T2 : l'économie annuelle ne doit JAMAIS baisser quand la batterie grossit.
// Exécute le VRAI code extrait de calculateur-pv-nc.html (segment simulation + financier)
// avec les données réelles de l'étude Betty SOUNOU (20/07/2026).
const fs=require('fs');
const html=fs.readFileSync(require('path').join(__dirname,'..','calculateur-pv-nc.html'),'utf8');

// ── Extraire factureMois (fonction réelle) ──
const fmStart=html.indexOf('function factureMois');
const fmEnd=html.indexOf('\n}',fmStart)+2;
const factureMoisSrc=html.slice(fmStart,fmEnd);

// ── Extraire le segment simulation+financier de calcT2 (code réel) ──
const t2Start=html.indexOf('// === SIMULATION AJOUT BATTERIE ===');
const t2EndMarker='const ecoMois=fSansM.map((f,i)=>f-fAvecM[i]);';
const t2End=html.indexOf(t2EndMarker,t2Start)+t2EndMarker.length;
if(t2Start<0||t2End<t2EndMarker.length){console.error('SEGMENT INTROUVABLE');process.exit(2)}
const simSrc=html.slice(t2Start,t2End);

// ── Contexte identique au calculateur ──
const DM=[31,28,31,30,31,30,31,31,30,31,30,31];
const s={tl:37.91,th:42.24,tp:29.62,rh:21,rs:15,pf:608.42,kva:6.6,tc:9,rc:703,tgc:3};
// Données Betty SOUNOU (étude T2 réelle)
const reinjM=[490,315,350,330,335,300,350,325,400,520,530,515];
const achatM=[165,200,140,150,140,140,130,120,120,120,110,145];
const rev=21, dod=0.85;
const prodDedieM=new Array(12).fill(0); // pas de lot dédié chez Betty
// Variables définies plus haut dans calcT2 (hors segment extrait) — valeurs Betty
const prodM2=[780,600,580,540,530,470,510,505,680,760,830,800];
const prodAn=prodM2.reduce((a,b)=>a+b,0);
const autoconsoDirecteAn=prodM2.map((p,i)=>Math.max(0,p-reinjM[i])).reduce((a,b)=>a+b,0);

function ecoPour(batWh){
  const fn=new Function('batWh','dod','reinjM','achatM','prodDedieM','rev','s','DM','prodM2','prodAn','autoconsoDirecteAn',
    factureMoisSrc+'\n'+simSrc+'\nreturn {ecoAn,bChargeAn:bChargeM.reduce((a,b)=>a+b,0),bDischAn,newReinjAn};');
  return fn(batWh,dod,reinjM,achatM,prodDedieM,rev,s,DM,prodM2,prodAn,autoconsoDirecteAn);
}

const cases=[['Élite 4,8',4800],['Prestige 10,65',10650],['Maestro 14,3',14336],['Prestige ×2',21300]];
let prev=-Infinity,ok=true;
console.log('Batterie          | Économie/an XPF | Chargé kWh | Déchargé kWh | Chargé-perdu kWh');
for(const [nom,wh] of cases){
  const r=ecoPour(wh);
  const perdu=Math.round(r.bChargeAn-r.bDischAn);
  console.log(`${nom.padEnd(17)}| ${String(Math.round(r.ecoAn)).padStart(15)} | ${String(Math.round(r.bChargeAn)).padStart(10)} | ${String(Math.round(r.bDischAn)).padStart(12)} | ${String(perdu).padStart(16)}`);
  if(r.ecoAn<prev-1)ok=false; // tolérance arrondi 1 XPF
  if(perdu>1){ok=false;console.log(`  ⚠ ${perdu} kWh chargés jamais déchargés (énergie disparue)`)}
  prev=r.ecoAn;
}
console.log(ok?'\nTEST PASS ✅ — économie monotone, pas d\'énergie perdue':'\nTEST FAIL ❌ — économie décroissante et/ou énergie chargée perdue');
process.exit(ok?0:1);
