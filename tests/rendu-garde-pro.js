// Rend la garde entreprise (sortie C) dans ses deux états — sans photo du site
// et avec — en passant par la vraie route : onglet 4 → CALCULER → panneau
// d'impression → pmPrint(). Contrôle aussi que le document reste à 2 pages et
// que la bascule HT/TTC ne déplace ni le ROI ni la production.
//
// Usage : node tests/rendu-garde-pro.js [dossier-de-sortie]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const OUT = process.argv[2] || path.join(__dirname, '..', '_rendu');
fs.mkdirSync(OUT, { recursive: true });
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');
const PHOTO = path.join(__dirname, '..', 'Graphique', 'MAison 2.jpg');
const LOGO_CLIENT = path.join(__dirname, '..', 'Graphique', 'LOGO-230x230.png');

// Paramètres du test de référence du CLAUDE.md (18,9 kWc).
async function saisirReference(p) {
  await p.evaluate(() => {
    const set = (id, v) => { const e = document.getElementById(id); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); } };
    set('t4_kwc', 18.9); set('t4_wc', 450); set('t4_kva', 19.8);
    set('t4_primefix', 964); set('t4_redev', 681); set('t4_tc', 9);
    set('t4_tarif', 29.62); set('t4_auto', 65); set('t4_rev', 0);
    set('t4_devis', 2900000); set('t4_is', 30); set('t4_amortd', 10);
    set('t4_nom', 'SARL TOULTEMPS'); set('t4_commune', '98800 Nouméa');
    for (let i = 0; i < 12; i++) set('m4_' + i, 2300);
  });
  await p.waitForTimeout(300);
}

async function imprimer(p, nom) {
  await p.evaluate(() => { window.print = () => {}; });
  await p.click('button.btn-print:has-text("Enregistrer en PDF")');
  await p.waitForTimeout(300);
  await p.click('button.pm-print');
  await p.waitForTimeout(1500);
  const pdf = path.join(OUT, `garde-pro-${nom}.pdf`);
  // preferCSSPageSize est indispensable ici : sans lui, Playwright impose son
  // propre format et ignore la règle @page cover (marge nulle) dont dépend la
  // barre orange bord à bord. Le test rognait la barre alors que Chrome, lui,
  // la rendait correctement.
  await p.pdf({ path: pdf, printBackground: true, preferCSSPageSize: true });
  const pages = (fs.readFileSync(pdf).toString('latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
  return { pdf, pages };
}

(async () => {
  const b = await chromium.launch();
  const erreurs = [];
  let ko = false;

  for (const avecPhoto of [false, true]) {
    const nom = avecPhoto ? 'avec-photo' : 'sans-photo';
    const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
    p.on('pageerror', e => erreurs.push(`[${nom}] ${e.message}`));
    await p.goto(FILE, { waitUntil: 'networkidle' });
    await p.evaluate(() => showTab(3));
    await saisirReference(p);
    // Logo client dans les deux cas : c'est un emplacement de la garde, il doit
    // être vérifié indépendamment de la photo du site.
    await p.setInputFiles('#t4_logo_file', LOGO_CLIENT);
    await p.waitForTimeout(900);
    if (avecPhoto) {
      await p.setInputFiles('#t4_photo_file', PHOTO);
      await p.waitForTimeout(1200);
    }
    await p.click('#tab3 button.btn-calc');
    await p.waitForTimeout(2000);

    const { pdf, pages } = await imprimer(p, nom);
    console.log(`${nom} : ${pages} page(s) — ${pdf}`);
    if (pages !== 2) { console.log(`  ✗ attendu 2 pages, obtenu ${pages}`); ko = true; }

    // La garde n'est visible qu'en média print.
    await p.emulateMedia({ media: 'print' });
    await p.waitForTimeout(400);
    const el = await p.$('#cover-page');
    if (el && await el.isVisible()) {
      await el.screenshot({ path: path.join(OUT, `garde-pro-${nom}.png`), timeout: 15000 });
    } else {
      console.log('  ✗ #cover-page invisible'); ko = true;
    }
    await p.emulateMedia({ media: 'screen' });
    await p.close();
  }

  // Bascule HT → TTC : le ROI et la production ne doivent pas bouger.
  const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
  p.on('pageerror', e => erreurs.push(`[ttc] ${e.message}`));
  await p.goto(FILE, { waitUntil: 'networkidle' });
  await p.evaluate(() => showTab(3));
  await saisirReference(p);
  await p.click('#tab3 button.btn-calc');
  await p.waitForTimeout(1800);
  const ht = await p.evaluate(() => ({ rsi: lastStudyData.rsi, prod: lastStudyData.prodAn }));
  await p.selectOption('#t4_mode', 'ttc');
  await p.click('#tab3 button.btn-calc');
  await p.waitForTimeout(1800);
  const ttc = await p.evaluate(() => ({ rsi: lastStudyData.rsi, prod: lastStudyData.prodAn }));
  const stable = Math.abs(ht.rsi - ttc.rsi) < 0.01 && Math.abs(ht.prod - ttc.prod) < 1;
  console.log(`HT/TTC : ROI ${ht.rsi.toFixed(2)} → ${ttc.rsi.toFixed(2)}, production ${Math.round(ht.prod)} → ${Math.round(ttc.prod)} kWh`);
  if (!stable) { console.log('  ✗ le ROI ou la production varie entre HT et TTC'); ko = true; }

  // Valeurs du test de référence du CLAUDE.md.
  console.log(`Référence : production ${Math.round(ht.prod)} kWh (attendu 28 085), ROI ${ht.rsi.toFixed(1)} ans (attendu 3,5)`);
  await p.close();
  await b.close();

  if (erreurs.length) { console.log('ERREURS JS :'); erreurs.forEach(e => console.log(' - ' + e)); ko = true; }
  console.log(ko ? 'ÉCHEC' : 'RENDU OK → ' + OUT);
  process.exit(ko ? 1 : 0);
})();
