// Mesure l'extent vertical du contenu de chaque page d'un PDF (jusqu'où l'encre
// descend sur la page) — c'est ça qui révèle le gâchis de place en bas de page,
// pas le % global de pixels sombres (une page pleine de texte n'a que ~15-20 % d'encre).
// Rend chaque page en PGM (P5, niveaux de gris) via pdftoppm, repère la dernière
// scanline contenant du contenu, et exprime ça en % de la hauteur totale.
// Usage : node tests/mesure-remplissage.js <fichier.pdf> [--seuil=80] [--skip=1,5]
//   --seuil : % minimal d'extent vertical exigé sur une page de contenu (défaut 80)
//   --skip  : numéros de pages 1-indexés à ignorer (garde, dernière page)
const {execFileSync}=require('child_process');
const fs=require('fs'),os=require('os'),path=require('path');

const args=process.argv.slice(2);
const pdf=args.find(a=>!a.startsWith('--'));
if(!pdf||!fs.existsSync(pdf)){console.error('PDF introuvable. Usage: node tests/mesure-remplissage.js <fichier.pdf> [--seuil=80] [--skip=1,5]');process.exit(2);}
const seuil=parseFloat((args.find(a=>a.startsWith('--seuil='))||'--seuil=80').split('=')[1]);
const skip=new Set(((args.find(a=>a.startsWith('--skip='))||'--skip=').split('=')[1]||'').split(',').filter(Boolean).map(Number));

const SEUIL_OCTET=245; // blanc = 255 ; on considère "encre" tout octet < 245
const MIN_PIXELS_LIGNE=3; // une scanline compte comme "avec contenu" si ≥ 3 pixels d'encre (ignore le bruit isolé)

// Parse un PNM binaire (P5 gris 1 octet/pixel, ou P6 couleur 3 octets/pixel).
// En-tête ASCII : "P5"/"P6" <ws> width <ws> height <ws> maxval <un seul ws> puis données binaires.
// Le header peut contenir des commentaires '#' jusqu'à fin de ligne.
// Retourne {width, height, tauxEncre, extentVertical} :
//   - tauxEncre        : % de pixels non-blancs sur toute la page (info secondaire)
//   - extentVertical   : % de la hauteur occupée jusqu'à la dernière ligne avec contenu
function analysePNM(buf){
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
  const [width,height]=fields;
  const rowBytes=width*bytesPerPixel;

  let totalPixels=0,darkPixels=0,lastContentRow=-1;
  for(let y=0;y<height;y++){
    const rowStart=pos+y*rowBytes;
    let darkInRow=0;
    for(let x=0;x<width;x++){
      let v;
      if(bytesPerPixel===1){
        v=buf[rowStart+x];
      }else{
        const k=rowStart+x*3;
        v=(buf[k]+buf[k+1]+buf[k+2])/3;
      }
      totalPixels++;
      if(v<SEUIL_OCTET){darkPixels++;darkInRow++;}
    }
    if(darkInRow>=MIN_PIXELS_LIGNE)lastContentRow=y;
  }
  const tauxEncre=totalPixels?darkPixels/totalPixels*100:0;
  const extentVertical=height?((lastContentRow+1)/height)*100:0;
  return {tauxEncre,extentVertical};
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
console.log('Page | Extent vertical | Encre (info) | Verdict');
try{
  for(let page=1;page<=nb;page++){
    const base=path.join(dir,'p'+page);
    execFileSync('pdftoppm',['-gray','-r','50','-f',String(page),'-l',String(page),pdf,base]);
    const rendu=fs.readdirSync(dir).map(f=>path.join(dir,f)).find(f=>f.startsWith(base)&&(f.endsWith('.pgm')||f.endsWith('.ppm')));
    if(!rendu){throw new Error(`Rendu introuvable pour la page ${page} (pdftoppm n'a produit aucun fichier).`);}
    const {tauxEncre,extentVertical}=analysePNM(fs.readFileSync(rendu));
    const extentPct=Math.round(extentVertical*10)/10;
    const encrePct=Math.round(tauxEncre*10)/10;
    const ignored=skip.has(page);
    const ok=ignored||extentPct>=seuil;
    if(!ok)allOK=false;
    console.log(`${String(page).padStart(4)} | ${String(extentPct).padStart(15)}% | ${String(encrePct).padStart(11)}% | ${ignored?'(ignorée)':(ok?'OK':'❌ < '+seuil+'%')}`);
  }
}catch(e){
  console.error('Erreur pendant le rendu/l\'analyse : '+e.message);
  quitter(2);
}
console.log(allOK?'\nREMPLISSAGE OK ✅':'\nREMPLISSAGE INSUFFISANT ❌');
quitter(allOK?0:1);
