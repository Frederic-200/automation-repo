#!/usr/bin/env node
/* v2 frame renderer: timeline.json -> numbered JPEG frames (exact time per frame, deterministic).
     node render.js --tl WORK/timeline.json --out FRAMES_DIR [--mode full|preview] [--times 1,3,5]
   preview writes PNGs preview_<sec>.png instead of the full run. */
'use strict';
const fs = require('fs'), path = require('path'), http = require('http');
let pw; try { pw = require('playwright'); } catch (e) { pw = require('playwright-core'); }
const a = process.argv.slice(2), opt = (n, d) => { const i = a.indexOf('--' + n); return i >= 0 ? a[i + 1] : d; };
const tl = JSON.parse(fs.readFileSync(opt('tl'))), OUT = path.resolve(opt('out')), MODE = opt('mode', 'full');
const ROOT = path.resolve(__dirname, '..'), TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.json': 'application/json' };
fs.mkdirSync(OUT, { recursive: true });
const srv = http.createServer((req, res) => {
  let u = decodeURIComponent(req.url.split('?')[0]); if (u === '/') u = '/engine/page.html';
  const f = path.join(ROOT, u); if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const port = srv.address().port;
  const browser = await pw.chromium.launch({ args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server'] });
  const page = await browser.newPage({ viewport: { width: tl.W, height: tl.H } });
  const errs = []; page.on('pageerror', e => errs.push(String(e))); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.evaluate(t => window.init(t), tl).catch(e => { throw new Error('init failed: ' + e + '\n' + errs.join('\n')); });
  const t0 = Date.now();
  try {
    if (MODE === 'preview') {
      for (const s of opt('times', '0.2,2,5').split(',').map(Number)) { await page.evaluate(f => window.frame(f), Math.round(s * tl.fps)); fs.writeFileSync(path.join(OUT, `preview_${s}.png`), await page.screenshot({ type: 'png' })); }
    } else {
      for (let f = 0; f < tl.frames; f++) {
        await page.evaluate(f => window.frame(f), f);
        fs.writeFileSync(path.join(OUT, String(f + 1).padStart(5, '0') + '.jpg'), await page.screenshot({ type: 'jpeg', quality: 93 }));
        if ((f + 1) % 150 === 0 || f + 1 === tl.frames) console.log(`frames ${f + 1}/${tl.frames} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      }
    }
  } finally { await browser.close(); srv.close(); }
  if (errs.length) console.log('page errors:\n' + errs.slice(0, 6).join('\n'));
  console.log(`done ${MODE} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e.stack || e); process.exit(1); });
