// Full-page or viewport screenshots of the local preview, with headless Edge over the DevTools protocol.
// The link-preview image web/og.png came from it: serve the site (python scripts/serve_local.py --port 8766), then
//   VIEWPORT=1 INJECT=scripts/og_inject.js AFTER=2500 node scripts/og_image.mjs og 1600 840 13000 http://localhost:8766/
// and downscale og/1-home-1600.png to 1200x630. og_inject.js hides the page chrome for the capture only.
// usage: node og_image.mjs <out-dir> <width> <height> <wait-ms> <url> [<url> ...]
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { basename, join } from "node:path";

const [outDir, w, h, wait, ...urls] = process.argv.slice(2);
const W = +w, H = +h, WAIT = +wait;
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const port = 9300 + Math.floor(Math.random() * 600);
const profile = mkdtempSync(join(tmpdir(), "edge-shot-"));
mkdirSync(outDir, { recursive: true });
const proc = spawn(EDGE, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--force-device-scale-factor=1", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let version;
for (let i = 0; i < 60 && !version; i++) {
  try { version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); } catch { await sleep(250); }
}
if (!version) { console.error("edge did not start"); proc.kill(); rmSync(profile, { recursive: true, force: true }); process.exit(1); }

let n = 0;
for (const url of urls) {
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
  const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
  await new Promise((r) => { ws.onopen = r; });
  const mobile = W < 768;
  await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile });
  if (mobile) await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Page.navigate", { url });
  await sleep(WAIT);
  if (process.env.INJECT) {  // capture-only tweaks, evaluated in the page
    const code = (await import("node:fs")).readFileSync(process.env.INJECT, "utf8");
    await send("Runtime.evaluate", { expression: code, awaitPromise: true });
    await sleep(+(process.env.AFTER || 1500));
  }
  const m = await send("Page.getLayoutMetrics");
  const size = m.result.cssContentSize || m.result.contentSize;
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: W, height: process.env.VIEWPORT ? H : Math.ceil(size.height), scale: 1 } });
  const name = (new URL(url).hash.slice(1) || "home").replace(/[^a-z0-9-]/gi, "_");
  const file = join(outDir, `${++n}-${name}-${W}.png`);
  writeFileSync(file, Buffer.from(shot.result.data, "base64"));
  console.log(file, Math.ceil(size.height));
  ws.close();
}
// Edge relaunches itself, so its browser processes aren't children of the one spawned here, and each
// run's throwaway profile is about 170 MB. Ask the browser to close, stop anything still running from this
// profile, then remove the profile.
try {
  const b = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { b.onopen = resolve; b.onerror = reject; });
  b.send(JSON.stringify({ id: 1, method: "Browser.close" }));
  await sleep(1500);
} catch { proc.kill(); }
const leftover = `Get-CimInstance Win32_Process -Filter "Name = 'msedge.exe'" | Where-Object { $_.CommandLine -like '*${basename(profile)}*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }`;
try { execFileSync("powershell", ["-NoProfile", "-Command", leftover], { stdio: "ignore" }); } catch {}
await sleep(500);
try { rmSync(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); } catch (e) { console.error("could not remove", profile, e.code); }
