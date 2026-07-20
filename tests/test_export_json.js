// Test Task 6 : buildStudyJSON() — extrait le code réel du fichier et l'exécute avec des stubs fidèles
const fs=require('fs');
const html=fs.readFileSync(require('path').join(__dirname,'..','calculateur-pv-nc.html'),'utf8');
const grab=(start,endMark)=>{const a=html.indexOf(start);const b=html.indexOf(endMark,a)+endMark.length;if(a<0||b<endMark.length)throw new Error('segment introuvable: '+start);return html.slice(a,b)};

// Extraction fidèle des fonctions réelles du fichier
const tranchesSrc=grab('const TRANCHES_NC=[','\n];');
const calcDeductionSrc=grab('function calcDeduction','\n}\n');
const buildAmortSrc=grab('function buildAmort(','\n}\n');
const sortieActiveSrc=grab('function sortieActive()','\n}');
const tabActifSrc=grab('function tabActif(){','\n}');
const getSSrc=grab('function getS(){','\n}');
const buildStudyJSONSrc=grab('function buildStudyJSON(){','\n}\n');
const exportStudyJSONSrc=grab('function exportStudyJSON(){','\n}');

// lastStudyData factice (étude T1 déjà calculée)
const lastStudyData={
  tab:1, devis:1850000, ecoAn:231000, ecoAn1:231000,
  fSansAn:385000, fAvecAn:154000, client:'TEST', kwc:6,
  batModel:4800, batQty:1, eco10:2000000, eco15:3500000, pb:5
};

// Stub DOM minimal pour getS() (aucun élément trouvé → valeurs par défaut utilisées)
const document={getElementById:()=>null,querySelector:()=>null};

const fn=new Function('lastStudyData','document',
  tranchesSrc+'\n'+
  calcDeductionSrc+'\n'+
  tabActifSrc+'\n'+
  sortieActiveSrc+'\n'+
  getSSrc+'\n'+
  buildAmortSrc+'\n'+
  buildStudyJSONSrc+'\n'+
  'return buildStudyJSON();'
);

const json=fn(lastStudyData,document);

let ok=true;
const check=(cond,msg)=>{if(!cond){ok=false;console.log('FAIL: '+msg)}else{console.log('OK  : '+msg)}};

check(json.meta && json.meta.sortie==='A', 'meta.sortie === "A" (T1)');
check(Array.isArray(json.tranchesFiscales) && json.tranchesFiscales.length===4, 'tranchesFiscales.length === 4 (taux>0 uniquement)');
check(json.tranchesFiscales.every(t=>t.deductionXPF>0), 'toutes les tranches ont deductionXPF > 0');
check(json.finances && json.finances.economieAn1XPF===231000, 'finances.economieAn1XPF === 231000');
check(json.finances.devisTTC===1850000, 'finances.devisTTC === 1850000');
check(json.installation.kwc===6, 'installation.kwc === 6');

// Sortie C (T4) : tranchesFiscales doit être vide
const fnT4=new Function('lastStudyData','document',
  tranchesSrc+'\n'+calcDeductionSrc+'\n'+tabActifSrc+'\n'+sortieActiveSrc+'\n'+getSSrc+'\n'+buildAmortSrc+'\n'+buildStudyJSONSrc+
  '\nreturn buildStudyJSON();'
);
const jsonT4=fnT4(Object.assign({},lastStudyData,{tab:4}),document);
check(jsonT4.meta.sortie==='C', 'meta.sortie === "C" (T4)');
check(Array.isArray(jsonT4.tranchesFiscales) && jsonT4.tranchesFiscales.length===0, 'tranchesFiscales vide en sortie C');

console.log(ok?'TEST PASS ✅':'TEST FAIL ❌');
process.exit(ok?0:1);
