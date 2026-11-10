#!/usr/bin/env node
// node tools/propsheet.js OUT.png [style=a] [pal=ember]  -> contact sheet of every prop in a world style
'use strict';
const fs = require('fs'), path = require('path'), http = require('http');
let pw; try { pw = require('playwright'); } catch (e) { pw = require('playwright-core'); }
const [out, style = 'a', pal = 'ember'] = process.argv.slice(2), ROOT = path.resolve(__dirname, '..'), TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };
const srv = http.createServer((req, res) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res); });
(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const b = await pw.chromium.launch({ args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-proxy-server'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1620 } }), errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => m.type() === 'error' && errs.push(m.text()));
  await p.goto(`http://127.0.0.1:${srv.address().port}/props/sheet.html?style=${style}&pal=${pal}`); await p.waitForFunction('window.ready===true', null, { timeout: 20000 }).catch(() => { });
  fs.writeFileSync(out, await p.screenshot({ type: 'png' })); await b.close(); srv.close(); if (errs.length) console.log(errs.join('\n')); console.log('wrote', out);
})();
