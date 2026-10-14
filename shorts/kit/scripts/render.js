#!/usr/bin/env node
/* Headless Chromium capture for video-kit.
     node render.js WORK full [--workers 2] [--from F --to F]   -> WORK/frames/00000.jpg ...
     node render.js WORK preview 0.5,3.2,7          -> WORK/preview/t003.20.png (times in seconds)
     node render.js WORK auto-preview               -> scene 45%/90% + 0.06 s after each keyword
   Chromium flags: ONLY --no-sandbox --enable-unsafe-swiftshader (the "software GPU" flags slow Canvas 2D up to 8x). */
'use strict';
const fs = require('fs'), path = require('path'), http = require('http');
const CACHE = process.env.VIDEO_KIT_CACHE || path.join(require('os').homedir(), '.cache', 'video-kit');
const { chromium } = require(path.join(CACHE, 'node', 'node_modules', 'playwright-core'));
const ENGINE = path.resolve(__dirname, '..', 'engine');

const args = process.argv.slice(2), WORK = path.resolve(args[0]), MODE = args[1] || 'full';
const opt = n => { const i = args.indexOf('--' + n); return i > 0 ? args[i + 1] : null; };
const TL = JSON.parse(fs.readFileSync(path.join(WORK, 'timeline.json')));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg' };

function serve() {
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(req.url.split('?')[0]); let file = null;
    if (u.startsWith('/e/')) file = path.join(ENGINE, u.slice(3)); else if (u.startsWith('/w/')) file = path.join(WORK, u.slice(3));
    if (!file || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' }); fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => srv.listen(0, '127.0.0.1', () => r(srv)));
}
function chromePath() {
  if (process.env.VIDEO_KIT_CHROME) return process.env.VIDEO_KIT_CHROME;
  const f = path.join(CACHE, 'chromium.txt'); if (fs.existsSync(f)) return fs.readFileSync(f, 'utf8').trim();
  const base = '/opt/pw-browsers'; const d = fs.existsSync(base) ? fs.readdirSync(base).filter(n => n.startsWith('chromium-')).sort().pop() : null;
  return d ? path.join(base, d, 'chrome-linux', 'chrome') : undefined;
}
async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  const errs = []; page.on('pageerror', e => errs.push(String(e))); page.on('console', m => { if (m.type() === 'error' && !/status of 404/.test(m.text())) errs.push(m.text()); });
  const cust = fs.existsSync(path.join(WORK, 'scenes_custom.js')) ? '&c=1' : '';
  await page.goto(`http://127.0.0.1:${port}/e/template.html?w=/w/${cust}`);
  const ok = await page.waitForFunction(() => window.ready || window.bootError, null, { timeout: 120000 }).then(() => page.evaluate(() => window.bootError));
  if (ok) throw new Error('boot failed: ' + ok + '\n' + errs.join('\n'));
  page._errs = errs; return page;
}
const b64 = s => Buffer.from(s.slice(s.indexOf(',') + 1), 'base64');

(async () => {
  const srv = await serve(), port = srv.address().port;
  const browser = await chromium.launch({ executablePath: chromePath(), args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--no-proxy-server'], env: { ...process.env, HTTPS_PROXY: '', HTTP_PROXY: '', https_proxy: '', http_proxy: '' } });
  const t0 = Date.now();
  try {
    if (MODE === 'full') {
      const dir = path.join(WORK, 'frames'); fs.mkdirSync(dir, { recursive: true });
      const nW = +(opt('workers') || process.env.VIDEO_KIT_WORKERS || 2), from = +(opt('from') || 0), to = +(opt('to') || TL.frames - 1);
      const pages = await Promise.all(Array.from({ length: nW }, () => openPage(browser, port)));
      let done = 0; const total = to - from + 1;
      await Promise.all(pages.map(async (pg, w) => {
        for (let f = from + w; f <= to; f += nW) {
          const fn = path.join(dir, String(f).padStart(5, '0') + '.jpg');
          fs.writeFileSync(fn, b64(await pg.evaluate(f => window.frameJPEG(f), f)));
          if (++done % 60 === 0 || done === total) { const el = (Date.now() - t0) / 1000;
            console.log(`frames ${done}/${total}  ${el.toFixed(0)}s  ${(el / done * 1000 * nW).toFixed(0)} ms/frame/worker  eta ${((total - done) * el / done).toFixed(0)}s`); }
        }
        if (pg._errs.length) console.error('page errors:\n' + [...new Set(pg._errs)].slice(0, 5).join('\n'));
      }));
    } else {
      let times;
      if (MODE === 'auto-preview') { times = [];
        for (const s of TL.scenes) { const d = s.end - s.start; times.push(s.start + d * .45, s.start + d * .9); s.keys.forEach(k => times.push(k.s + .06)); }
        TL.scenes.slice(1).forEach(s => times.push(s.start + .02)); // transition midpoints
      } else times = (args[2] || '0').split(',').map(Number);
      const dir = path.join(WORK, 'preview'); fs.mkdirSync(dir, { recursive: true });
      for (const f of fs.readdirSync(dir)) fs.unlinkSync(path.join(dir, f));
      const pg = await openPage(browser, port), out = [];
      for (const t of [...new Set(times.map(t => Math.max(0, Math.min(TL.duration - .01, t))))].sort((a, b) => a - b)) {
        const f = Math.round(t * 30), fn = path.join(dir, `t${(f / 30).toFixed(2).padStart(6, '0')}.png`);
        const s0 = Date.now(); fs.writeFileSync(fn, b64(await pg.evaluate(f => window.framePNG(f), f))); out.push([fn, Date.now() - s0]);
      }
      out.forEach(([f, ms]) => console.log(`${path.basename(f)}  ${ms} ms`));
      if (pg._errs.length) console.error('page errors:\n' + [...new Set(pg._errs)].slice(0, 8).join('\n'));
    }
  } finally { await browser.close(); srv.close(); }
  console.log(`render ${MODE} done in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e.stack || e); process.exit(1); });
