// Test T1 : économie non-décroissante quand la batterie grossit (code réel extrait)
const fs=require('fs');
const html=fs.readFileSync(require('path').join(__dirname,'..','calculateur-pv-nc.html'),'utf8');
const grab=(start,endMark)=>{const a=html.indexOf(start);const b=html.indexOf(endMark,a)+endMark.length;if(a<0||b<endMark.length)throw new Error('segment introuvable: '+start);return html.slice(a,b)};
const factureMoisSrc=grab('function factureMois','\n}');
const prodMSrc=grab('function prodM(','\n}');
const t1Src=grab('  const prod=prodM(kwc,s.en,s.pe);','const ecoMois=fSansM.map((f,i)=>f-fAvecM[i]);');

const DM=[31,28,31,30,31,30,31,31,30,31,30,31];
const IDX=[1.38,1.38,1.32,0.90,0.80,0.65,0.80,0.95,1.25,1.25,1.40,1.50];
const IDXSUM=IDX.reduce((a,b)=>a+b,0);
const s={tl:37.91,th:42.24,tp:29.62,pf:608.42,kva:6.6,tc:9,rc:703,tgc:3,en:4.2,pe:10,dod:85};
const consoM=[450,475,365,360,335,305,255,290,270,320,380,420];
const tauxAuto=60,piscOn=false,piscKwh=0,rev=21,kwc=6.6,panWc=330;

function eco(batWh){
  const fn=new Function('s','consoM','tauxAuto','piscOn','piscKwh','rev','kwc','panWc','batWh','DM','IDX','IDXSUM',
    factureMoisSrc+'\n'+prodMSrc+'\n'+t1Src+
    '\nreturn {ecoAn,ch:batWh>0?directAutoM.map((_,i)=>0).reduce((a)=>a,0):0,batAutoAn,reinjAn,achatAn};');
  return fn(s,consoM,tauxAuto,piscOn,piscKwh,rev,kwc,panWc,batWh,DM,IDX,IDXSUM);
}
let prev=-Infinity,ok=true;
console.log('Batterie   | Économie/an | Couvert bat | Reinj | Achat');
for(const [n,wh] of [['sans',0],['4,8',4800],['10,65',10650],['14,3',14336],['21,3',21300]]){
  const r=eco(wh);
  console.log(`${n.padEnd(10)} | ${String(Math.round(r.ecoAn)).padStart(11)} | ${String(Math.round(r.batAutoAn)).padStart(11)} | ${String(Math.round(r.reinjAn)).padStart(5)} | ${String(Math.round(r.achatAn)).padStart(5)}`);
  if(r.ecoAn<prev-1)ok=false;
  prev=r.ecoAn;
}
console.log(ok?'TEST PASS ✅':'TEST FAIL ❌');
process.exit(ok?0:1);
