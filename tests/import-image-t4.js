// Import du logo client et de la photo du site (sortie C) : un fichier illisible
// doit le dire. Sans onerror, t4LoadImage() échouait en silence — l'utilisateur
// choisissait un fichier, rien ne se passait, aucune explication.
const { chromium } = require('playwright');
const fs = require('fs'), os = require('os'), path = require('path');
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');

let ko = 0;
const check = (nom, cond) => { if (!cond) ko++; console.log(`  ${cond ? '✓' : '✗'} ${nom}`); };

// Un PNG 2×2 valide, en dur : le test ne dépend d'aucun fichier du dépôt.
const PNG_OK = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR4nGP8z8Dwn4GBgYEJRIAAIxUDBQoVAWEAAAAASUVORK5CYII=', 'base64');

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'import-img-'));
  const bon = path.join(dir, 'logo.png');
  const faux = path.join(dir, 'pas-une-image.png');   // extension d'image, contenu texte
  fs.writeFileSync(bon, PNG_OK);
  fs.writeFileSync(faux, 'ceci n est pas une image');

  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  const err = [];
  p.on('pageerror', e => err.push(e.message));
  await p.goto(FILE, { waitUntil: 'networkidle' });
  await p.waitForFunction(() => typeof t4LoadImage === 'function');

  console.log('fichier illisible');
  await p.setInputFiles('#t4_logo_file', faux);
  await p.waitForTimeout(600);
  let r = await p.evaluate(() => ({
    prev: document.getElementById('t4_logo_prev').textContent.trim(),
    stocke: t4Images.logo,
  }));
  check('un message explique le refus', /illisible|pas une image|invalide|impossible/i.test(r.prev));
  check("l'image n'est pas enregistrée", !r.stocke);

  console.log('image valide');
  await p.setInputFiles('#t4_logo_file', bon);
  await p.waitForTimeout(600);
  r = await p.evaluate(() => ({
    aImg: !!document.querySelector('#t4_logo_prev img'),
    stocke: (t4Images.logo || '').slice(0, 22),
  }));
  check("l'aperçu s'affiche", r.aImg);
  check("l'image est enregistrée", r.stocke.startsWith('data:image/jpeg'));

  console.log('retour à un fichier illisible après un import réussi');
  await p.setInputFiles('#t4_logo_file', faux);
  await p.waitForTimeout(600);
  r = await p.evaluate(() => ({ prev: document.getElementById('t4_logo_prev').textContent.trim(), stocke: t4Images.logo }));
  check('le message revient', /illisible|pas une image|invalide|impossible/i.test(r.prev));
  check("l'ancienne image est retirée", !r.stocke);

  check('aucune erreur JS', err.length === 0);
  if (err.length) console.log('    ' + err.join(' | '));
  await b.close();
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(ko ? '\nTEST FAIL ❌' : '\nTEST PASS ✅');
  process.exit(ko ? 1 : 0);
})();
