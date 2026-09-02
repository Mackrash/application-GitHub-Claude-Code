// L'horizon d'étude (paramètre dpv) doit s'afficher partout où il est annoncé :
// à l'écran comme à l'impression, et jusque dans les libellés du panneau
// d'impression. Un titre « 20 ans » au-dessus d'une courbe de 15 ans fait
// croire au client que le document a changé d'horizon.
const { chromium } = require('playwright');
const path = require('path');
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');

let ko = 0;
const eq = (nom, obtenu, attendu) => {
  const ok = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!ok) ko++;
  console.log(`  ${ok ? '✓' : '✗'} ${nom}` + (ok ? '' : `\n     attendu : ${JSON.stringify(attendu)}\n     obtenu  : ${JSON.stringify(obtenu)}`));
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
  await p.goto(FILE, { waitUntil: 'networkidle' });
  await p.waitForFunction(() => typeof pmPrint === 'function');
  await p.click('button.btn-calc');
  await p.waitForTimeout(2200);

  console.log("après CALCULER, sans passer par l'impression");
  let r = await p.evaluate(() => ({
    dpv: getS().dpv,
    titres: [...document.querySelectorAll('.roi-dur')].map(e => e.textContent),
  }));
  eq('titres du graphe ROI alignés sur l\'horizon', r.titres, r.titres.map(() => String(r.dpv)));

  console.log('libellés du panneau d\'impression');
  r = await p.evaluate(() => { openPrintModal();
    return { dpv: getS().dpv, labels: [...document.querySelectorAll('#pm-list label')].map(l => l.textContent.trim()) }; });
  const roi = r.labels.find(l => /ROI/.test(l) && /ans/.test(l));
  eq('le libellé du graphe ROI annonce l\'horizon réel', /\b(\d+) ans/.exec(roi || '')?.[1], String(r.dpv));

  console.log('après un changement d\'horizon dans les paramètres');
  r = await p.evaluate(async () => {
    document.getElementById('s_dpv').value = 22;
    document.querySelector('button.btn-calc').click();
    await new Promise(r => setTimeout(r, 1800));
    return { dpv: getS().dpv, titres: [...document.querySelectorAll('.roi-dur')].map(e => e.textContent) };
  });
  eq('les titres suivent le nouvel horizon', r.titres, r.titres.map(() => String(r.dpv)));

  await b.close();
  console.log(ko ? '\nTEST FAIL ❌' : '\nTEST PASS ✅');
  process.exit(ko ? 1 : 0);
})();
