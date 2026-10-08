"use strict";

/* A pixel-art Delhi skyline, drawn in code: rooftops with solar panels and water tanks, India Gate
   Qutub Minar and the Lotus Temple, wind turbines, a passing metro, drifting clouds and the sun.
   data-theme="dark" turns it to night. The canvas is drawn at low resolution and scaled up with
   crisp pixels. */
(function () {
  const PALETTES = {
    day: {
      sky: ["#8cc8f2", "#a2d3f5", "#b6ddf7", "#c9e6f9", "#dbeefa", "#ecf6fc"],
      sun: "#ffd23f", sunRim: "#ffb21e", cloud: "#ffffff", cloudShade: "#dbe9f5",
      far: "#a8c4df", farDark: "#93b3d3", track: "#8aa3bd", train: "#e8edf2", trainStripe: "#2f6bc0", trainWindow: "#5b7fa6",
      walls: ["#f2dcb8", "#e9bf91", "#f6f1e7", "#d8e6c9", "#f0cfc0", "#e2d6c5"], wallShade: "rgba(0,0,0,0.10)",
      window: "#6b8fb5", windowLit: "#6b8fb5", parapet: "rgba(0,0,0,0.12)",
      panel: "#1f3b6e", panelLine: "#4c72b0", panelGlint: "#c9dcff", tank: "#2d2d2d", tankHi: "#5a5a5a",
      tree: "#4a9a52", treeDark: "#357a3e", treeHi: "#78bf6a", ground: "#9cc77a", groundDark: "#86b467",
      turbine: "#f4f7fa", turbineShade: "#c6d3df", star: null,
      gate: "#e8c99d", gateShade: "#c9a578", gateDark: "#a8845a",
      minar: "#c96f47", minarShade: "#a5532f", minarBand: "#eaa97d",
      lotus: "#fbf8f2", lotusShade: "#d8d2c5",
    },
    night: {
      sky: ["#0b1630", "#0f1d3c", "#142649", "#1a3057", "#223b66", "#2b4675"],
      sun: "#f3efd8", sunRim: "#d9d3b4", cloud: "#2a3b5e", cloudShade: "#22324f",
      far: "#22365a", farDark: "#1c2d4c", track: "#2a3d61", train: "#3a4c70", trainStripe: "#5d8be0", trainWindow: "#ffd36b",
      walls: ["#3a3550", "#433b4f", "#363b55", "#2f3f4c", "#45394a", "#3b3a48"], wallShade: "rgba(0,0,0,0.18)",
      window: "#28304a", windowLit: "#ffd36b", parapet: "rgba(0,0,0,0.25)",
      panel: "#16233f", panelLine: "#2c4472", panelGlint: "#6f88b8", tank: "#141414", tankHi: "#2c2c2c",
      tree: "#1f4a2c", treeDark: "#17391f", treeHi: "#2c6338", ground: "#25402c", groundDark: "#1d3424",
      turbine: "#9aa8bd", turbineShade: "#6c7a91", star: "#e8eefc",
      gate: "#76624f", gateShade: "#5e4e3f", gateDark: "#463a2f",
      minar: "#74443a", minarShade: "#58312a", minarBand: "#98634f",
      lotus: "#a7acc0", lotusShade: "#80859b",
    },
  };
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];

  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // The site is light by default; the night sky only appears when the page asks for it.
  function isNight() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function Scene(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.t = 0;
    this.layout();
  }

  Scene.prototype.layout = function () {
    const box = this.canvas.getBoundingClientRect();
    if (!box.width || !box.height) return;
    const px = Math.max(3, Math.round(box.width / 340));
    this.W = Math.max(120, Math.ceil(box.width / px));
    this.H = Math.max(60, Math.ceil(box.height / px));
    this.canvas.width = this.W;
    this.canvas.height = this.H;
    this.skyFor = null;
    const r = rng(20261008);
    const W = this.W, H = this.H;
    // The city lives in a band along the bottom; above it is open sky for the page's content.
    // mirrors .hero's --band in style.css: clamp(170px, 26vh, 280px), or 190px on narrow screens
    const wide = window.innerWidth > 900;
    const bandPx = wide ? Math.max(170, Math.min(280, window.innerHeight * 0.26)) : 190;
    const S = this.S = Math.min(H, Math.round(bandPx / px));
    this.ground = H - Math.max(4, Math.round(S * 0.08));
    const skyTop = H - S;
    this.clouds = Array.from({ length: Math.ceil(W / 60) + 2 }, (_, i) => ({
      x: (i * 60 + r() * 40) % (W + 60) - 30, y: 4 + r() * Math.max(10, skyTop + S * 0.2) * 0.8, w: 16 + r() * 22, h: 5 + r() * 4, speed: 0.04 + r() * 0.05,
    }));
    this.stars = Array.from({ length: Math.round(W * H / 220) }, () => ({ x: Math.floor(r() * W), y: Math.floor(r() * (skyTop + S * 0.5)), tw: r() * 6.28 }));
    this.sunAt = wide ? [Math.round(W * 0.575), Math.round(Math.max(skyTop * 0.16, S * 0.2))] : [Math.round(W * 0.86), Math.round(Math.max(10, S * 0.18))];
    this.far = [];
    for (let x = -4; x < W + 8;) {
      const w = 6 + Math.floor(r() * 12), h = Math.round(S * (0.14 + r() * 0.2));
      this.far.push({ x, w, h, shade: r() < 0.35 });
      x += w + Math.floor(r() * 3);
    }
    // landmarks stand on open ground under the page's text; houses fill the rest of the street
    this.gateW = Math.round(S * 0.36);
    this.gate = Math.round(W * (wide ? 0.13 : 0.2) - this.gateW / 2);
    this.minar = Math.round(W * (wide ? 0.47 : 0.8));
    this.lotusW = W >= 200 ? Math.round(S * 0.36) : 0;
    this.lotus = Math.round(W * (wide ? 0.3 : 0.5));
    const open = [[this.gate - 4, this.gate + this.gateW + 4], [this.minar - 9, this.minar + 9]];
    if (this.lotusW) open.push([this.lotus - this.lotusW / 2 - 4, this.lotus + this.lotusW / 2 + 4]);
    this.houses = [];
    for (let x = -6; x < W + 10;) {
      const w = 14 + Math.floor(r() * 18), h = Math.round(S * (0.16 + r() * 0.18));
      const house = {
        x, w, h, wall: Math.floor(r() * 6), panel: r() < 0.62, tank: r() < 0.55, tankX: r(), floors: 1 + Math.floor(h / 9),
        lit: Array.from({ length: 24 }, () => r() < 0.45), glint: Math.floor(r() * 40),
      };
      if (!open.some(([a, b]) => x < b && x + w > a)) this.houses.push(house);
      x += w + Math.floor(r() * 3);
    }
    this.trees = Array.from({ length: Math.ceil(W / 26) }, (_, i) => ({ x: i * 26 + Math.floor(r() * 18), r: 3 + Math.floor(r() * 3) }));
    this.turbines = wide ? [Math.round(W * 0.035), Math.round(W * 0.965)] : [Math.round(W * 0.06), Math.round(W * 0.94)];
  };

  Scene.prototype.rect = function (x, y, w, h, c) { this.ctx.fillStyle = c; this.ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h)); };

  Scene.prototype.line = function (x0, y0, x1, y1, c) {
    x0 = Math.round(x0); y0 = Math.round(y0); x1 = Math.round(x1); y1 = Math.round(y1);
    const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx + dy;
    this.ctx.fillStyle = c;
    for (;;) {
      this.ctx.fillRect(x0, y0, 1, 1);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
  };

  // The dithered sky is the same every frame, so it is drawn once into a buffer and copied.
  Scene.prototype.sky = function (p, night) {
    if (this.skyFor !== night) {
      const buf = this.skyBuf || (this.skyBuf = document.createElement("canvas"));
      buf.width = this.W;
      buf.height = this.ground;
      const c = buf.getContext("2d"), bands = p.sky.length, H = this.ground;
      for (let y = 0; y < H; y++) {
        const f = (y / H) * (bands - 1), i = Math.floor(f), frac = f - i;
        for (let x = 0; x < this.W; x++) {
          const k = BAYER[y % 4][x % 4] / 16;
          c.fillStyle = p.sky[Math.min(bands - 1, frac > k ? i + 1 : i)];
          c.fillRect(x, y, 1, 1);
        }
      }
      this.skyFor = night;
    }
    this.ctx.drawImage(this.skyBuf, 0, 0);
  };

  Scene.prototype.sun = function (p, night) {
    const [cx, cy] = this.sunAt, R = Math.max(5, Math.round(this.S * 0.085));
    if (!night) {
      const n = 8, pulse = Math.round(Math.sin(this.t / 9) + 1);
      for (let k = 0; k < n; k++) {
        const a = (k / n) * Math.PI * 2 + 0.2;
        this.line(cx + Math.cos(a) * (R + 2), cy + Math.sin(a) * (R + 2), cx + Math.cos(a) * (R + 4 + pulse), cy + Math.sin(a) * (R + 4 + pulse), p.sunRim);
      }
    }
    for (let y = -R; y <= R; y++) for (let x = -R; x <= R; x++) {
      const d = x * x + y * y;
      if (d <= R * R) this.rect(cx + x, cy + y, 1, 1, d > (R - 1.2) * (R - 1.2) ? p.sunRim : p.sun);
    }
    if (night) this.rect(cx + 2, cy - 2, 2, 2, p.sunRim);
  };

  Scene.prototype.cloud = function (c, p) {
    const x = Math.round(c.x), y = Math.round(c.y), w = Math.round(c.w), h = Math.round(c.h);
    this.rect(x + 2, y + 2, w - 4, h - 2, p.cloud);
    this.rect(x, y + Math.round(h / 2), w, Math.ceil(h / 2), p.cloud);
    this.rect(x + Math.round(w * 0.25), y, Math.round(w * 0.35), 3, p.cloud);
    this.rect(x + Math.round(w * 0.55), y + 1, Math.round(w * 0.25), 2, p.cloud);
    this.rect(x + 1, y + h - 1, w - 2, 1, p.cloudShade);
  };

  Scene.prototype.turbine = function (x, p) {
    const top = this.ground - Math.round(this.S * 0.52), base = this.ground - 2;
    this.rect(x, top, 1, base - top, p.turbine);
    this.rect(x + 1, top + 3, 1, base - top - 3, p.turbineShade);
    this.rect(x - 1, top - 1, 3, 2, p.turbine);
    const L = Math.round(this.S * 0.17), a0 = this.t / 14;
    for (let k = 0; k < 3; k++) {
      const a = a0 + (k * Math.PI * 2) / 3;
      this.line(x, top, x + Math.cos(a) * L, top + Math.sin(a) * L, p.turbine);
    }
  };

  Scene.prototype.landmarks = function (p) {
    const g = this.ground;
    const behind = p.sky[p.sky.length - 2];

    // India Gate: a sandstone arch with piers, a cornice, an attic and the bowl on top
    const gx = this.gate, gw = this.gateW, gh = Math.round(this.S * 0.44);
    this.rect(gx - 2, g - 3, gw + 4, 3, p.gateShade);
    this.rect(gx, g - gh, gw, gh - 3, p.gate);
    this.rect(gx + gw - 2, g - gh, 2, gh - 3, p.gateShade);
    const aw = Math.round(gw * 0.38), ah = Math.round(gh * 0.6), ax = gx + Math.round((gw - aw) / 2);
    this.rect(ax, g - 3 - ah, aw, ah, behind);
    for (let i = 1; i <= 3; i++) this.rect(ax + i, g - 3 - ah - i, aw - 2 * i, 1, behind);
    this.rect(ax - 1, g - 3 - ah, 1, ah, p.gateDark);
    const sw = Math.max(2, Math.round(gw * 0.08)), sh = Math.round(gh * 0.28);
    this.rect(gx + 3, g - 3 - sh, sw, sh, p.gateDark);
    this.rect(gx + gw - 3 - sw, g - 3 - sh, sw, sh, p.gateDark);
    this.rect(gx + 2, g - gh + 3, gw - 4, 1, p.gateShade);
    this.rect(gx - 2, g - gh - 2, gw + 4, 2, p.gateShade);
    this.rect(gx + 2, g - gh - 6, gw - 4, 4, p.gate);
    this.rect(gx + gw - 4, g - gh - 6, 2, 4, p.gateShade);
    this.rect(gx + 4, g - gh - 7, gw - 8, 1, p.gateShade);
    const bx = gx + Math.round(gw / 2);
    this.rect(bx - 4, g - gh - 9, 8, 2, p.gateShade);
    this.rect(bx - 2, g - gh - 10, 4, 1, p.gateDark);

    // Lotus Temple: two rings of white petals on a low plinth
    if (this.lotusW) {
      const lx = this.lotus, lw = this.lotusW, lh = Math.round(this.S * 0.2);
      const petal = (cx, pw, ph, base, c, shade) => {
        for (let y = 0; y < ph; y++) {
          const w = Math.max(1, Math.round(pw * (1 - y / ph) ** 0.8));
          this.rect(cx - Math.floor(w / 2), base - y, w, 1, c);
          this.rect(cx + Math.ceil(w / 2) - 1, base - y, 1, 1, shade);
        }
      };
      const base = g - 3;
      for (let k = -1; k <= 1; k++) petal(lx + Math.round((k * lw) / 4.2), Math.round(lw / 3.2), lh, base, p.lotus, p.lotusShade);
      for (let k = -2; k <= 2; k++) petal(lx + Math.round((k * lw) / 5.2), Math.round(lw / 4.2), Math.round(lh * 0.6), base, p.lotus, p.lotusShade);
      this.rect(lx - Math.round(lw / 2) - 2, g - 3, lw + 4, 3, p.lotusShade);
    }

    // Qutub Minar: a tapering, fluted red-sandstone tower with balcony bands and a cupola
    const mx = this.minar, mh = Math.round(this.S * 0.7);
    const bands = [0.3, 0.52, 0.7, 0.85].map((f) => Math.round(mh * f));
    for (let y = 0; y < mh; y++) {
      const w = Math.max(4, Math.round(11 - (y / mh) * 6)), left = mx - Math.floor(w / 2);
      for (let x = 0; x < w; x++) this.rect(left + x, g - 1 - y, 1, 1, (x + (y >> 3)) % 3 === 0 ? p.minarShade : p.minar);
      if (bands.includes(y)) this.rect(left - 1, g - 1 - y - 1, w + 2, 2, p.minarBand);
    }
    this.rect(mx - 2, g - mh - 3, 4, 3, p.minarBand);
    this.rect(mx - 1, g - mh - 5, 2, 2, p.minarBand);
    this.rect(mx - 7, g - 2, 14, 2, p.minarShade);
  };

  Scene.prototype.metro = function (p) {
    const y = this.ground - Math.round(this.S * 0.2);
    this.rect(0, y, this.W, 2, p.track);
    for (let x = 6; x < this.W; x += 22) this.rect(x, y + 2, 2, this.ground - y - 2, p.track);
    const len = 46, span = this.W + len + 40, tx = this.W - ((this.t * 0.9) % span) + 20;
    this.rect(tx, y - 5, len, 5, p.train);
    this.rect(tx, y - 2, len, 1, p.trainStripe);
    for (let k = 2; k < len - 2; k += 5) this.rect(tx + k, y - 4, 3, 1, p.trainWindow);
    this.rect(tx, y - 5, 2, 4, p.trainStripe);
  };

  Scene.prototype.house = function (h, p, night) {
    const top = this.ground - h.h, wall = p.walls[h.wall];
    this.rect(h.x, top, h.w, h.h, wall);
    this.rect(h.x + h.w - 2, top, 2, h.h, p.wallShade);
    this.rect(h.x - 1, top - 1, h.w + 2, 1, p.parapet);
    let i = 0;
    for (let fy = top + 3; fy < this.ground - 3; fy += 6) {
      for (let fx = h.x + 2; fx < h.x + h.w - 3; fx += 5) {
        this.rect(fx, fy, 3, 3, night && h.lit[i % h.lit.length] ? p.windowLit : p.window);
        i++;
      }
    }
    if (h.tank) {
      const tx = h.x + 2 + Math.round(h.tankX * Math.max(1, h.w - 8));
      this.rect(tx, top - 5, 4, 4, p.tank);
      this.rect(tx + 1, top - 6, 2, 1, p.tank);
      this.rect(tx + 1, top - 4, 1, 2, p.tankHi);
    }
    if (h.panel) {
      const pw = Math.max(6, Math.round(h.w * 0.6)), px = h.x + Math.round((h.w - pw) / 2) + (h.tank ? 0 : 0);
      const py = top - 4;
      for (let k = 0; k < pw; k++) {
        this.rect(px + k, py + 1, 1, 3, p.panel);
        if (k % 3 === 2) this.rect(px + k, py + 1, 1, 3, p.panelLine);
      }
      this.rect(px, py + 2, pw, 1, p.panelLine);
      this.rect(px, py, pw, 1, p.panelLine);
      if (!night) {
        const g = (Math.floor(this.t / 3) + h.glint) % 40;
        if (g < pw) this.rect(px + g, py + 1, 1, 1, p.panelGlint);
      }
      this.rect(px + 1, py + 4, 1, 1, p.parapet);
      this.rect(px + pw - 2, py + 4, 1, 1, p.parapet);
    }
  };

  Scene.prototype.tree = function (t, p) {
    const cy = this.ground - t.r;
    for (let y = -t.r; y <= t.r; y++) for (let x = -t.r; x <= t.r; x++) {
      if (x * x + y * y <= t.r * t.r) this.rect(t.x + x, cy + y, 1, 1, y > t.r / 3 ? p.treeDark : (x + y < -t.r / 2 ? p.treeHi : p.tree));
    }
    this.rect(t.x, this.ground - 1, 1, 1, p.treeDark);
  };

  Scene.prototype.draw = function () {
    if (!this.W) return;
    const night = isNight(), p = PALETTES[night ? "night" : "day"];
    this.sky(p, night);
    if (night) for (const s of this.stars) if (Math.sin(this.t / 12 + s.tw) > -0.3) this.rect(s.x, s.y, 1, 1, p.star);
    this.sun(p, night);
    for (const c of this.clouds) this.cloud(c, p);
    for (const f of this.far) this.rect(f.x, this.ground - f.h, f.w, f.h, f.shade ? p.farDark : p.far);
    for (const x of this.turbines) this.turbine(x, p);
    this.metro(p);
    for (const h of this.houses) this.house(h, p, night);
    this.landmarks(p);
    this.rect(0, this.ground, this.W, this.H - this.ground, p.ground);
    for (let x = 0; x < this.W; x += 2) this.rect(x + ((x / 2) % 2), this.ground + 1, 1, 1, p.groundDark);
    for (const t of this.trees) this.tree(t, p);
  };

  Scene.prototype.step = function () {
    if (!this.W) return;  // the hero is hidden (an inner page is open); layout runs when it shows
    this.t += 1;
    for (const c of this.clouds) { c.x += c.speed * 4; if (c.x > this.W + 10) c.x = -c.w - 10; }
    this.draw();
  };

  function start() {
    const canvas = document.getElementById("scene");
    if (!canvas || !canvas.getContext) return;
    const scene = new Scene(canvas);
    scene.draw();
    const still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let visible = true, last = 0;
    if ("IntersectionObserver" in window) new IntersectionObserver((e) => { visible = e[0].isIntersecting; }).observe(canvas);
    function loop(ts) {
      if (visible && !still && ts - last > 85) { last = ts; scene.step(); }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
    // the hero grows and shrinks with its content (fonts loading, language switch), not only the window
    let resize, size = "";
    const relayout = () => {
      const b = canvas.getBoundingClientRect(), now = `${Math.round(b.width)}x${Math.round(b.height)}`;
      if (now !== size && b.width && b.height) { size = now; scene.layout(); scene.draw(); }
    };
    if ("ResizeObserver" in window) new ResizeObserver(() => { clearTimeout(resize); resize = setTimeout(relayout, 120); }).observe(canvas);
    else window.addEventListener("resize", () => { clearTimeout(resize); resize = setTimeout(relayout, 150); });
    new MutationObserver(() => scene.draw()).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
