#!/usr/bin/env node
/* FredsDesk Loops - deterministic headless renderer (Three.js in Chromium/SwiftShader -> ffmpeg).
     node render.js --cfg cfg.json --out DIR [--mode full|preview|seam] [--times 0.5,3,9] [--limit N]
   full    -> DIR/silent.mp4 + DIR/events.json
   preview -> DIR/preview_<sec>.png for each time (fast look at the result)
   seam    -> DIR/seam_first.png + DIR/seam_last.png (frame 0 and frame N: must be near-identical for a perfect loop)
   Every frame is drawn at an exact time (not real-time), so output is identical on every run/machine. */
'use strict';
const fs = require('fs'), path = require('path'), http = require('http'), { spawn } = require('child_process');
let pw; try { pw = require('playwright'); } catch (e) { pw = require('playwright-core'); }
const { chromium } = pw;

const args = process.argv.slice(2);
const opt = (n, d = null) => { const i = args.indexOf('--' + n); return i >= 0 ? args[i + 1] : d; };
const cfg = JSON.parse(fs.readFileSync(opt('cfg'))), OUT = path.resolve(opt('out', 'out')), MODE = opt('mode', 'full');
const ROOT = __dirname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.woff2': 'font/woff2', '.png': 'image/png' };
fs.mkdirSync(OUT, { recursive: true });

function serve() {
  const srv = http.createServer((req, res) => {
    let u = decodeURIComponent(req.url.split('?')[0]); if (u === '/') u = '/engine/page.html';
    const file = path.join(ROOT, u);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' }); fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => srv.listen(0, '127.0.0.1', () => r(srv)));
}

(async () => {
  const srv = await serve(), port = srv.address().port;
  const browser = await chromium.launch({ args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server'] });
  const page = await browser.newPage({ viewport: { width: cfg.width, height: cfg.height } });
  const errs = []; page.on('pageerror', e => errs.push(String(e))); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(`http://127.0.0.1:${port}/`);
  const info = await page.evaluate(c => window.init(c), cfg).catch(e => { throw new Error('init failed: ' + e + '\n' + errs.join('\n')); });
  fs.writeFileSync(path.join(OUT, 'events.json'), JSON.stringify(info));
  const shot = async f => { await page.evaluate(f => window.frame(f), f); return page.screenshot({ type: 'jpeg', quality: 95 }); };
  const shotPng = async f => { await page.evaluate(f => window.frame(f), f); return page.screenshot({ type: 'png' }); };
  const t0 = Date.now();
  try {
    if (MODE === 'preview') {
      for (const s of (opt('times', '1,5,9')).split(',').map(Number)) {
        fs.writeFileSync(path.join(OUT, `preview_${s}.png`), await shotPng(Math.round(s * cfg.fps)));
      }
    } else if (MODE === 'seam') {
      fs.writeFileSync(path.join(OUT, 'seam_first.png'), await shotPng(0));
      fs.writeFileSync(path.join(OUT, 'seam_last.png'), await shotPng(cfg.frames));      // t = 1.0 must equal t = 0
    } else {
      const total = +(opt('limit') || cfg.frames);
      const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(cfg.fps), '-i', '-',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path.join(OUT, 'silent.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (let f = 0; f < total; f++) {
        const buf = await shot(f); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        if ((f + 1) % 30 === 0 || f + 1 === total) { const el = (Date.now() - t0) / 1000; console.log(`frames ${f + 1}/${total}  ${el.toFixed(0)}s  eta ${((total - f - 1) * el / (f + 1)).toFixed(0)}s`); }
      }
      ff.stdin.end(); await new Promise(r => ff.on('close', r));
    }
  } finally { await browser.close(); srv.close(); }
  if (errs.length) console.log('page errors:\n' + errs.slice(0, 6).join('\n'));
  console.log(`done ${MODE} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e.stack || e); process.exit(1); });
