"use strict";
// Measure a roof on Amazon Location satellite tiles: find the house, tap the roof's corners, and the
// usable area goes into the estimate. MapLibre (open source) loads only when the tracer opens.

(() => {
  const LIB = "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.min";
  const maps = window.SURYA_MAPS || {};
  const box = document.getElementById("roofer");
  const open = document.getElementById("roof-map");
  if (!maps.key || !box || typeof box.showModal !== "function") { if (open) open.hidden = true; return; }

  const RADIUS = 6378137;  // metres, the WGS84 radius used for areas on the sphere
  const USABLE = 0.65;     // what's left after stairs, the water tank and the edges
  const SQFT_PER_KW = 100; // the rule the estimate uses: 2 kW needs about 200 sq ft
  const TRACE_ZOOM = 17;   // below this a tap can't land on one roof
  const MAX_SQFT = 30000;  // past this it's a block or a field, not a home's roof
  const $ = (id) => document.getElementById(id);
  let map = null, points = [], closed = false, lib = null;

  function loadLib() {
    if (lib) return lib;
    lib = new Promise((resolve, reject) => {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = LIB + ".css";
      document.head.append(css);
      const js = document.createElement("script");
      js.src = LIB + ".js";
      js.onload = resolve;
      js.onerror = reject;
      document.head.append(js);
    });
    return lib;
  }

  // area of a closed ring on the sphere, in m² (the spherical-excess formula map libraries use)
  function area(ring) {
    const rad = (d) => d * Math.PI / 180;
    let sum = 0;
    for (let i = 0; i < ring.length; i++) {
      const [lon1, lat1] = ring[i], [lon2, lat2] = ring[(i + 1) % ring.length];
      sum += (rad(lon2) - rad(lon1)) * (2 + Math.sin(rad(lat1)) + Math.sin(rad(lat2)));
    }
    return Math.abs(sum * RADIUS * RADIUS / 2);
  }

  function measure() {
    const m2 = area(points);
    const gross = m2 * 10.7639;
    const usable = Math.round(gross * USABLE / 10) * 10;
    const kw = Math.floor(usable / SQFT_PER_KW * 2) / 2;
    return { m2: Math.round(m2), gross: Math.round(gross / 10) * 10, usable, kw };
  }

  function render() {
    const features = points.map((p) => ({ type: "Feature", geometry: { type: "Point", coordinates: p } }));
    if (closed) features.push({ type: "Feature", geometry: { type: "Polygon", coordinates: [[...points, points[0]]] } });
    else if (points.length > 1) features.push({ type: "Feature", geometry: { type: "LineString", coordinates: points } });
    if (map && map.getSource("roof")) map.getSource("roof").setData({ type: "FeatureCollection", features });
    const read = $("rf-read"), use = $("rf-use");
    if (closed) {
      const r = measure();
      if (r.gross > MAX_SQFT) {
        read.textContent = t("rfTooBig");
        use.textContent = t("rfUseIdle");
        use.disabled = true;
        $("rf-undo").disabled = false;
        return;
      }
      read.textContent = t("rfRead", r.gross.toLocaleString("en-IN"), r.m2, r.usable.toLocaleString("en-IN"), r.kw);
      use.textContent = t("rfUse", r.usable.toLocaleString("en-IN"));
      use.disabled = r.usable < 50;
    } else {
      read.textContent = points.length ? t("rfPoints", points.length) : "";
      use.textContent = t("rfUseIdle");
      use.disabled = true;
    }
    $("rf-undo").disabled = !points.length;
  }

  function startMap() {
    const here = state.lat !== null ? [state.lon, state.lat] : [77.21, 28.61];
    map = new maplibregl.Map({
      container: "rf-map",
      style: `https://maps.geo.${maps.region}.amazonaws.com/v2/styles/Hybrid/descriptor?key=${maps.key}`,
      center: here, zoom: state.lat !== null ? 16 : 11, maxZoom: 20.5,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.doubleClickZoom.disable();  // quick taps on corners shouldn't zoom
    map.on("load", () => {
      // shop and clinic pins sit on the very roofs being traced; street and area names stay
      for (const layer of map.getStyle().layers) {
        if (layer.type === "symbol" && /poi/i.test(layer.id)) map.setLayoutProperty(layer.id, "visibility", "none");
      }
      map.addSource("roof", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({ id: "roof-fill", type: "fill", source: "roof", filter: ["==", "$type", "Polygon"],
        paint: { "fill-color": "#f2a516", "fill-opacity": 0.32 } });
      map.addLayer({ id: "roof-line", type: "line", source: "roof", filter: ["in", "$type", "LineString", "Polygon"],
        paint: { "line-color": "#f2a516", "line-width": 3 } });
      map.addLayer({ id: "roof-corner", type: "circle", source: "roof", filter: ["==", "$type", "Point"],
        paint: { "circle-radius": 6, "circle-color": "#ffffff", "circle-stroke-color": "#f2a516", "circle-stroke-width": 3 } });
      render();
    });
    map.on("click", (e) => {
      if (closed) return;
      if (map.getZoom() < TRACE_ZOOM && !points.length) { $("rf-help").textContent = t("rfZoomIn"); return; }
      if (points.length >= 3) {
        const first = map.project(points[0]);
        if (Math.hypot(first.x - e.point.x, first.y - e.point.y) < 16) { closed = true; render(); return; }
      }
      points.push([e.lngLat.lng, e.lngLat.lat]);
      render();
    });
  }

  open.addEventListener("click", async () => {
    box.showModal();
    $("rf-help").textContent = t("rfLoading");
    try {
      await loadLib();
      if (!map) startMap(); else map.resize();
      $("rf-help").textContent = t("rfHelp");
    } catch (_) { $("rf-help").textContent = t("rfDown"); }
  });
  $("rf-close").addEventListener("click", () => box.close());
  box.addEventListener("click", (e) => { if (e.target === box) box.close(); });  // a click on the backdrop
  $("rf-undo").addEventListener("click", () => { if (closed) closed = false; else points.pop(); render(); });
  $("rf-clear").addEventListener("click", () => { points = []; closed = false; render(); });
  $("rf-search").addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = $("rf-q").value.trim();
    if (!q || !map) return;
    try {
      const p = await getJSON(`/places?q=${encodeURIComponent(q)}`);
      map.flyTo({ center: [p.lon, p.lat], zoom: 19 });
      $("rf-help").textContent = t("rfHelp");
    } catch (_) { $("rf-help").textContent = t("rfNotFound"); }
  });
  $("rf-use").addEventListener("click", () => {
    const r = measure();
    $("roof").value = r.usable;
    // two decimals (about 1 km), as with the location button: enough for sunlight, not an address
    const c = points.reduce((a, p) => [a[0] + p[0] / points.length, a[1] + p[1] / points.length], [0, 0]);
    state.lon = Math.round(c[0] * 100) / 100;
    state.lat = Math.round(c[1] * 100) / 100;
    $("locate").textContent = t("locationOn");
    open.textContent = t("roofMapDone", r.usable.toLocaleString("en-IN"));
    box.close();
  });
  window.renderRoof = () => { $("rf-q").placeholder = t("rfQ"); if (map || points.length) render(); };
  window.renderRoof();
})();
