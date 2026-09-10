// Les graphiques Plotly doivent prendre la largeur de leur conteneur — à
// l'écran, sur le papier, et de nouveau à l'écran après une impression.
//
// ⚠️ PIÈGE QUE CE TEST EXISTE POUR ATTRAPER : Chrome déclenche `beforeprint`
// AVANT d'appliquer la mise en page d'impression. Un test qui force
// `emulateMedia({media:'print'})` puis dispatche `beforeprint` à la main ne
// reproduit donc PAS la vraie séquence : il mesure la page papier là où Chrome
// mesure encore l'écran. C'est exactement ce qui a laissé passer un graphique
// tracé à 1331 px dans une page de 794 — il ne montrait plus que quatre mois.
// D'où la règle : ici on ne force aucun média, on ne simule aucun événement.
// On appelle page.pdf(), qui déclenche beforeprint comme le vrai navigateur.
//
// Usage : node tests/largeur-graphiques.js
const { chromium } = require('playwright');
const path = require('path');

const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');
const LARGEUR_PAPIER = 794;   // 210 mm à 96 dpi
const TOLERANCE = 2;
// Fenêtre volontairement plus large que la page A4 : c'est la configuration
// qui révèle le bug (sur une fenêtre étroite, écran et papier se ressemblent).
const VIEWPORT = { width: 1500, height: 1200 };

const mesure = () => {
  const g = document.getElementById('g2_mois');
  const svg = g && g.querySelector('svg.main-svg');
  const R = el => (el ? Math.round(el.getBoundingClientRect().width) : null);
  return { conteneur: R(g), svg: R(svg) };
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: VIEWPORT });
  const echecs = [];
  const dire = (ok, txt) => { console.log(`  ${ok ? '✓' : '✗'} ${txt}`); if (!ok) echecs.push(txt); };

  await p.goto(FILE, { waitUntil: 'networkidle' });
  await p.evaluate(() => showTab(1));
  await p.click('.tab-content.active button.btn-calc');
  await p.waitForTimeout(1500);

  console.log('à l\'écran, après CALCULER');
  const ecran = await p.evaluate(mesure);
  dire(ecran.svg !== 700,
    `le graphique n'est pas resté au défaut Plotly de 700 px (mesuré ${ecran.svg})`);
  dire(Math.abs(ecran.svg - ecran.conteneur) <= TOLERANCE,
    `le graphique remplit son conteneur (${ecran.svg} / ${ecran.conteneur} px)`);

  // Impression par la vraie route : panneau, case cochée, bouton, puis page.pdf().
  await p.evaluate(() => { window.print = () => {}; });
  await p.click('button.btn-print:has-text("Enregistrer en PDF")');
  await p.waitForTimeout(300);
  await p.check('input[data-psec-id="gfact"]');
  await p.click('button.pm-print');
  await p.waitForTimeout(1200);

  let papier = null;
  p.once('console', () => {});
  await p.evaluate(() => { window.__mesurePapier = null; });
  await p.exposeFunction('__noteMesure', m => { papier = m; });
  await p.evaluate(() => {
    // Lecture SYNCHRONE : window.onbeforeprint de la page est enregistré avant
    // ce listener, donc il a déjà tourné. Un relevé différé (setTimeout) ne
    // vaut rien ici — afterprint a le temps de restaurer la largeur écran, et
    // le test croit alors à un débordement qui n'existe pas.
    window.addEventListener('beforeprint', () => {
      const g = document.getElementById('g2_mois');
      const svg = g && g.querySelector('svg.main-svg');
      window.__noteMesure({
        svg: svg ? Math.round(parseFloat(svg.getAttribute('width'))) : null,
        layout: g && g._fullLayout ? Math.round(g._fullLayout.width) : null,
      });
    });
  });

  await p.pdf({ printBackground: true, preferCSSPageSize: true });
  await p.waitForTimeout(400);

  console.log('à l\'impression (beforeprint déclenché par page.pdf, mise en page écran)');
  if (!papier) {
    dire(false, 'aucune mesure relevée pendant beforeprint');
  } else {
    dire(Math.abs(papier.layout - LARGEUR_PAPIER) <= TOLERANCE,
      `le graphique adopte la largeur papier et non celle de l'écran (${papier.layout} px, attendu ${LARGEUR_PAPIER})`);
    dire(papier.layout < VIEWPORT.width - 100,
      `le graphique ne déborde pas de la page (${papier.layout} px pour une fenêtre de ${VIEWPORT.width})`);
  }

  console.log('retour à l\'écran, après impression');
  const retour = await p.evaluate(mesure);
  dire(retour.svg !== 700,
    `le graphique ne retombe pas au défaut 700 px (mesuré ${retour.svg})`);
  dire(Math.abs(retour.svg - retour.conteneur) <= TOLERANCE,
    `le graphique reprend la largeur de son conteneur (${retour.svg} / ${retour.conteneur} px)`);

  await p.close();
  await b.close();
  console.log(echecs.length ? `\nÉCHEC — ${echecs.length} contrôle(s)` : '\nTEST PASS ✅');
  process.exit(echecs.length ? 1 : 0);
})();
