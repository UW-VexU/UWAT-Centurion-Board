import { chromium } from 'playwright';
import fs from 'fs';
const [,, svg, out, scale, bg] = process.argv;
const txt = fs.readFileSync(svg, 'utf8');
const m = txt.match(/width="([\d.]+)mm"\s+height="([\d.]+)mm"/) || txt.match(/viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"/);
const wmm = parseFloat(m[1]), hmm = parseFloat(m[2]);
const s = parseFloat(scale || '20');
const W = Math.round(wmm * s), H = Math.round(hmm * s);
const b = await chromium.launch();   // needs: npm install playwright && npx playwright install chromium (in this folder)
const p = await b.newPage({ viewport: { width: W, height: H } });
await p.setContent(`<html><body style="margin:0;background:${bg || '#fff'}"><img src="data:image/svg+xml;base64,${Buffer.from(txt).toString('base64')}" style="width:${W}px;height:${H}px;display:block"></body></html>`);
await p.waitForTimeout(500);
await p.screenshot({ path: out });
await b.close();
console.log(out, W, H);
