#!/usr/bin/env node
/* v2 prototype renderer: one world -> frame-exact screenshots -> ffmpeg. Deterministic (every frame drawn at an exact time).
   node render.js --world a_type --out DIR [--w 720 --h 1280 --fps 30 --sec 10] [--mode full|preview] [--times 1,3,5] */
'use strict';
const fs = require('fs'), path = require('path'), http = require('http'), { spawn } = require('child_process');
let pw; try { pw = require('playwright'); } catch (e) { pw = require('playwright-core'); }
const a = process.argv.slice(2), opt = (n, d) => { const i = a.indexOf('--' + n); return i >= 0 ? a[i + 1] : d; };
const world = opt('world'), OUT = path.resolve(opt('out', 'out')), W = +opt('w', 720), H = +opt('h', 1280), FPS = +opt('fps', 30), SEC = +opt('sec', 10), MODE = opt('mode', 'full');
const ROOT = __dirname, TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };
fs.mkdirSync(OUT, { recursive: true });
const srv = http.createServer((req, res) => {
  let u = decodeURIComponent(req.url.split('?')[0]); if (u === '/') u = '/page.html';
  const f = path.join(ROOT, u); if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});
(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const port = srv.address().port;
  const browser = await pw.chromium.launch({ args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-proxy-server'] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  const errs = []; page.on('pageerror', e => errs.push(String(e))); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(`http://127.0.0.1:${port}/?world=${world}&w=${W}&h=${H}&d=${SEC}`);
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 }).catch(() => { throw new Error('world did not start:\n' + errs.join('\n')); });
  const t0 = Date.now();
  try {
    if (MODE === 'preview') {
      for (const s of opt('times', '1,3,5,7,9').split(',').map(Number)) {
        await page.evaluate(([f, fps]) => window.frame(f, fps), [Math.round(s * FPS), FPS]);
        fs.writeFileSync(path.join(OUT, `${world}_t${s}.png`), await page.screenshot({ type: 'png' }));
      }
    } else {
      const N = FPS * SEC;
      const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path.join(OUT, `${world}.mp4`)], { stdio: ['pipe', 'inherit', 'inherit'] });
      for (let f = 0; f < N; f++) {
        await page.evaluate(([f, fps]) => window.frame(f, fps), [f, FPS]);
        const buf = await page.screenshot({ type: 'jpeg', quality: 93 }); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        if ((f + 1) % 60 === 0) console.log(`frames ${f + 1}/${N} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      }
      ff.stdin.end(); await new Promise(r => ff.on('close', r));
    }
  } finally { await browser.close(); srv.close(); }
  if (errs.length) console.log('page errors:\n' + errs.slice(0, 6).join('\n'));
  console.log(`done ${world} ${MODE} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e.stack || e); process.exit(1); });
