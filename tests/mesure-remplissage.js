// Mesure le taux de remplissage (pixels non-blancs) de chaque page d'un PDF.
// Rend chaque page en PGM (P5, niveaux de gris) via pdftoppm et compte les pixels sombres.
// Usage : node tests/mesure-remplissage.js <fichier.pdf> [--seuil=70] [--skip=1,5]
//   --seuil : % minimal de remplissage exigé sur une page de contenu (défaut 70)
//   --skip  : numéros de pages 1-indexés à ignorer (garde, dernière page)
const {execFileSync}=require('child_process');
const fs=require('fs'),os=require('os'),path=require('path');

const args=process.argv.slice(2);
const pdf=args.find(a=>!a.startsWith('--'));
if(!pdf||!fs.existsSync(pdf)){console.error('PDF introuvable. Usage: node tests/mesure-remplissage.js <fichier.pdf> [--seuil=70] [--skip=1,5]');process.exit(2);}
const seuil=parseFloat((args.find(a=>a.startsWith('--seuil='))||'--seuil=70').split('=')[1]);
const skip=new Set(((args.find(a=>a.startsWith('--skip='))||'--skip=').split('=')[1]||'').split(',').filter(Boolean).map(Number));

// Parse un PNM binaire (P5 gris 1 octet/pixel, ou P6 couleur 3 octets/pixel) → % de pixels non-blancs.
// En-tête ASCII : "P5"/"P6" <ws> width <ws> height <ws> maxval <un seul ws> puis données binaires.
// Le header peut contenir des commentaires '#' jusqu'à fin de ligne.
function tauxPNM(buf){
  const magic=buf.toString('ascii',0,2);
  if(magic!=='P5'&&magic!=='P6')throw new Error('Format PNM inattendu: '+magic);
  const bytesPerPixel=magic==='P6'?3:1;
  let pos=2,fields=[];
  function skipWs(){
    while(pos<buf.length){
      const c=buf[pos];
      if(c===0x23){while(pos<buf.length&&buf[pos]!==0x0a)pos++;}
      else if(c===0x20||c===0x09||c===0x0a||c===0x0d){pos++;}
      else break;
    }
  }
  while(fields.length<3){skipWs();let s=pos;while(pos<buf.length&&buf[pos]>0x20)pos++;fields.push(parseInt(buf.toString('ascii',s,pos),10));}
  pos++; // le seul whitespace après maxval
  let total=0,dark=0;
  const seuilOctet=245; // blanc = 255 ; on considère "encre" tout octet < 245
  if(bytesPerPixel===1){
    for(let k=pos;k<buf.length;k++){total++;if(buf[k]<seuilOctet)dark++;}
  }else{
    for(let k=pos;k+2<buf.length;k+=3){
      total++;
      const moy=(buf[k]+buf[k+1]+buf[k+2])/3;
      if(moy<seuilOctet)dark++;
    }
  }
  return total?dark/total*100:0;
}

// process.exit() court-circuite les blocs finally : on centralise donc la sortie
// dans une seule fonction qui nettoie systématiquement le dossier temp avant de quitter.
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'remplissage-'));
function quitter(code){
  fs.rmSync(dir,{recursive:true,force:true});
  process.exit(code);
}

let infoOut;
try{
  infoOut=execFileSync('pdfinfo',[pdf]).toString();
}catch(e){
  console.error('Erreur pdfinfo (pdf illisible ou corrompu) : '+e.message);
  quitter(2);
}
const m=infoOut.match(/Pages:\s+(\d+)/);
if(!m){console.error('Impossible de déterminer le nombre de pages.');quitter(2);}
const nb=parseInt(m[1],10);
let allOK=true;
console.log('Page | Remplissage | Verdict');
try{
  for(let page=1;page<=nb;page++){
    const base=path.join(dir,'p'+page);
    execFileSync('pdftoppm',['-gray','-r','50','-f',String(page),'-l',String(page),pdf,base]);
    const rendu=fs.readdirSync(dir).map(f=>path.join(dir,f)).find(f=>f.startsWith(base)&&(f.endsWith('.pgm')||f.endsWith('.ppm')));
    if(!rendu){throw new Error(`Rendu introuvable pour la page ${page} (pdftoppm n'a produit aucun fichier).`);}
    const pct=Math.round(tauxPNM(fs.readFileSync(rendu))*10)/10;
    const ignored=skip.has(page);
    const ok=ignored||pct>=seuil;
    if(!ok)allOK=false;
    console.log(`${String(page).padStart(4)} | ${String(pct).padStart(9)}% | ${ignored?'(ignorée)':(ok?'OK':'❌ < '+seuil+'%')}`);
  }
}catch(e){
  console.error('Erreur pendant le rendu/l\'analyse : '+e.message);
  quitter(2);
}
console.log(allOK?'\nREMPLISSAGE OK ✅':'\nREMPLISSAGE INSUFFISANT ❌');
quitter(allOK?0:1);
