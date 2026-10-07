// Usage: node render.js <buildDir> <workers> [frame ...]   (no frames = all; frames given => PNG previews)
const { chromium } = require('playwright-core');
const fs = require('fs'), path = require('path');
const dir = path.resolve(process.argv[2]), workers = +process.argv[3] || 2, only = process.argv.slice(4).map(Number);
const png = only.length > 0, framesDir = path.join(dir, png ? 'preview' : 'frames');
const exe = [process.env.CHROME_PATH, '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'].filter(Boolean).find(p => fs.existsSync(p));
fs.mkdirSync(framesDir, { recursive: true });
const url = 'file://' + path.resolve(__dirname, 'template.html') + '?tl=' + encodeURIComponent('file://' + path.join(dir, 'timeline.js'));
const TL = JSON.parse(fs.readFileSync(path.join(dir, 'timeline.json')));
const total = Math.round(TL.duration * TL.fps);
const frames = only.length ? only : Array.from({ length: total }, (_, i) => i);
async function worker(k) {
  const browser = await chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--allow-file-access-from-files', '--disable-gpu'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()) });
  await page.goto(url); await page.evaluate(() => window.ready);
  if (k === 0 && !png) fs.writeFileSync(path.join(dir, 'events.json'), JSON.stringify(await page.evaluate(() => window.getEvents())));
  let n = 0;
  for (let i = k; i < frames.length; i += workers) {
    const f = frames[i];
    const data = await page.evaluate(([f, png]) => { window.renderFrame(f); return document.getElementById('c').toDataURL(png ? 'image/png' : 'image/jpeg', 0.95) }, [f, png]);
    fs.writeFileSync(path.join(framesDir, png ? `p${String(f).padStart(5, '0')}.png` : `${String(f).padStart(5, '0')}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
    if (++n % 100 === 0) console.log(`worker ${k}: ${n}/${Math.ceil(frames.length / workers)}`);
  }
  await browser.close();
}
(async () => { const t0 = Date.now(); await Promise.all(Array.from({ length: workers }, (_, k) => worker(k))); console.log(`done ${frames.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`) })();
