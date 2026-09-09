/* ABAWD waiver map — client app. Vanilla JS; reads the embedded JSON payloads,
   renders one state × fiscal-year × document at a time. No network requests. */
(() => {
"use strict";

const DATA = JSON.parse(document.getElementById("wmap-data").textContent);
const TOPO = JSON.parse(document.getElementById("wmap-topology").textContent);
const tj = window.topojson;

const $ = (id) => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
const VB_W = 960, VB_H = 600, PAD = 0.04;

const RULE_ORDER = ["pct20_above_natl", "lsa", "pct10_statutory", "eb_trigger", "federal_suspension", "other", "uncoded"];
const ruleAttr = (code) => code == null ? "uncoded" : code;
const ruleLabel = (code) => code == null ? "No criterion recorded"
  : (DATA.rule_labels[code] ? DATA.rule_labels[code].short : code);

// prio breaks ties when one county sits in several groups: the strongest outcome wins
// the fill. withdrawn_by_state (v1_5) outranks "no action" — the state did act — but
// not an FNS denial, which is a decision on the merits.
const ACTION = {
  approved:           { word: "Approved", chip: "Approved", cls: "a-ok", prio: 4, pat: null },
  rejected:           { word: "Denied", chip: "Denied", cls: "a-no", prio: 3, pat: "hatch" },
  withdrawn_by_state: { word: "Withdrawn by the state", chip: "Withdrawn", cls: "a-wd", prio: 2, pat: "cross" }
};
const actionInfo = (a) => ACTION[a] ||
  { word: "No FNS action recorded", chip: "No action", cls: "a-na", prio: 1, pat: "dots" };

// area_type arrives normalized and lowercase from the data build; these are the ones
// whose raw form reads badly in a sentence. Anything unlisted falls through as-is.
const AREA_LABEL = {
  "lma": "labor-market area",
  "zcta": "ZIP-code tabulation area",
  "city (partial)": "part of a city"
};
const areaLabel = (t) => AREA_LABEL[t] || t || "area";

const DOCTYPE = {
  fns_response_only: "FNS response",
  state_request_only: "State request",
  full_application: "Full application",
  other_nonstandard: "Nonstandard document"
};

// ---------- formatting ----------
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function fmtDate(iso) {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(iso);
  if (!m) return String(iso);
  const mon = MON[+m[2] - 1] || m[2];
  return m[3] ? `${mon} ${+m[3]}, ${m[1]}` : `${mon} ${m[1]}`;
}
const isoish = (v) => /^\d{4}-\d{2}/.test(String(v == null ? "" : v));
const fmtRate = (r) => r == null ? null : String(+r) + "%";
function windowLabel(lu) {
  const parts = [];
  if (lu.window_type && lu.window_type !== "other")
    parts.push(lu.window_type.replace(/_/g, " ").replace(/^(\d+) month/, "$1-month"));
  const span = [fmtDate(lu.start), fmtDate(lu.end)].filter(Boolean).join(" – ");
  if (span) parts.push(span);
  return parts.join(", ");
}

// ---------- projection: per-state spherical Albers equal-area conic ----------
function eachCoord(geom, fn) {
  const c = geom.coordinates;
  if (geom.type === "Polygon") c.forEach((r) => r.forEach(fn));
  else if (geom.type === "MultiPolygon") c.forEach((p) => p.forEach((r) => r.forEach(fn)));
  else if (geom.type === "LineString") c.forEach(fn);
  else if (geom.type === "MultiLineString") c.forEach((l) => l.forEach(fn));
}

// Standard parallels at 1/6 and 5/6 of the latitude range; lon span > 180
// means the state crosses the antimeridian (Alaska) — unwrap negative lons.
// Raw y is negated so north is up in screen coordinates.
function makeProjector(features) {
  let lo0, lo1, la0, la1, wrap = false;
  const scan = () => {
    lo0 = la0 = Infinity; lo1 = la1 = -Infinity;
    features.forEach((f) => eachCoord(f.geometry, (p) => {
      let x = p[0];
      if (wrap && x < 0) x += 360;
      if (x < lo0) lo0 = x; if (x > lo1) lo1 = x;
      if (p[1] < la0) la0 = p[1]; if (p[1] > la1) la1 = p[1];
    }));
  };
  scan();
  if (lo1 - lo0 > 180) { wrap = true; scan(); }
  const R = Math.PI / 180;
  const f1 = (la0 + (la1 - la0) / 6) * R, f2 = (la0 + (la1 - la0) * 5 / 6) * R;
  const l0 = ((lo0 + lo1) / 2) * R, p0 = ((la0 + la1) / 2) * R;
  const s1 = Math.sin(f1), n = (s1 + Math.sin(f2)) / 2;
  const C = Math.cos(f1) * Math.cos(f1) + 2 * n * s1;
  const rho = (ph) => Math.sqrt(Math.max(0, C - 2 * n * Math.sin(ph))) / n;
  const r0 = rho(p0);
  const raw = (lon, lat) => {
    if (wrap && lon < 0) lon += 360;
    const th = n * (lon * R - l0), r = rho(lat * R);
    return [r * Math.sin(th), r * Math.cos(th) - r0];
  };
  // fit projected bbox into the viewBox, 4% padding, uniform scale, centered
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  features.forEach((f) => eachCoord(f.geometry, (p) => {
    const q = raw(p[0], p[1]);
    if (q[0] < x0) x0 = q[0]; if (q[0] > x1) x1 = q[0];
    if (q[1] < y0) y0 = q[1]; if (q[1] > y1) y1 = q[1];
  }));
  const s = Math.min(VB_W * (1 - 2 * PAD) / (x1 - x0), VB_H * (1 - 2 * PAD) / (y1 - y0));
  const tx = (VB_W - s * (x1 - x0)) / 2 - s * x0;
  const ty = (VB_H - s * (y1 - y0)) / 2 - s * y0;
  return (lon, lat) => {
    const q = raw(lon, lat);
    return [q[0] * s + tx, q[1] * s + ty];
  };
}

function geoPath(geom, prj) {
  if (!geom) return "";
  const run = (pts, close) => {
    let s = "";
    for (let i = 0; i < pts.length; i++) {
      const p = prj(pts[i][0], pts[i][1]);
      s += (i ? "L" : "M") + p[0].toFixed(1) + "," + p[1].toFixed(1);
    }
    return s + (close ? "Z" : "");
  };
  const t = geom.type, c = geom.coordinates;
  if (t === "Polygon") return c.map((r) => run(r, true)).join("");
  if (t === "MultiPolygon") return c.map((p) => p.map((r) => run(r, true)).join("")).join("");
  if (t === "LineString") return run(c, false);
  if (t === "MultiLineString") return c.map((l) => run(l, false)).join("");
  return "";
}

// Marker anchor: area centroid of the largest ring (projected, shoelace).
function polyCentroid(geom, prj) {
  const rings = geom.type === "Polygon" ? [geom.coordinates[0]]
    : geom.type === "MultiPolygon" ? geom.coordinates.map((p) => p[0]) : [];
  let best = null, bestA = 0;
  rings.forEach((r) => {
    const P = r.map((p) => prj(p[0], p[1]));
    let a = 0, cx = 0, cy = 0;
    for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
      const cr = P[j][0] * P[i][1] - P[i][0] * P[j][1];
      a += cr; cx += (P[j][0] + P[i][0]) * cr; cy += (P[j][1] + P[i][1]) * cr;
    }
    if (Math.abs(a) > Math.abs(bestA)) { bestA = a; best = [cx / (3 * a), cy / (3 * a)]; }
  });
  return best;
}

// ---------- per-state layer cache ----------
const stateCache = {};
function buildStateLayer(stFips) {
  if (stateCache[stFips]) return stateCache[stFips];
  const geoms = TOPO.objects.counties.geometries.filter((g) => g.id && g.id.slice(0, 2) === stFips);
  const coll = { type: "GeometryCollection", geometries: geoms };
  const fc = tj.feature(TOPO, coll);
  const prj = makeProjector(fc.features);
  const dByFips = new Map(), centroidByFips = new Map(), nameByFips = new Map();
  fc.features.forEach((f, i) => {
    const id = geoms[i].id;
    dByFips.set(id, geoPath(f.geometry, prj));
    centroidByFips.set(id, polyCentroid(f.geometry, prj));
    nameByFips.set(id, (f.properties && f.properties.name) || id);
  });
  const stGeom = TOPO.objects.states.geometries.find((g) => g.id === stFips);
  const layer = {
    geoms, prj, dByFips, centroidByFips, nameByFips,
    fipsList: geoms.map((g) => g.id),
    meshInner: geoPath(tj.mesh(TOPO, coll, (a, b) => a !== b), prj),
    outer: geoPath(tj.mesh(TOPO, stGeom || coll), prj)
  };
  stateCache[stFips] = layer;
  return layer;
}

const bundleCache = {};
function bundleD(docStub, bid, fipsList, layer) {
  const key = docStub + "|" + bid;
  if (bundleCache[key] !== undefined) return bundleCache[key];
  const set = new Set(fipsList);
  const geoms = layer.geoms.filter((g) => set.has(g.id));
  return (bundleCache[key] = geoms.length ? geoPath(tj.merge(TOPO, geoms), layer.prj) : "");
}

// ---------- app state ----------
const S = { tab: "map", state: null, fy: null, docIdx: 0, hover: null, rulesSlug: null };
const stateFys = (st) => Object.keys(DATA.states[st].fys).sort((a, b) => +a - +b);
const curDocs = () => DATA.states[S.state].fys[S.fy];
const curDoc = () => curDocs()[S.docIdx];
const curLayer = () => buildStateLayer(DATA.states[S.state].state_fips);

let viewCache = null, viewKey = null;
function curView() {
  const doc = curDoc();
  if (viewKey !== doc.doc_stub) { viewCache = buildView(doc, curLayer()); viewKey = doc.doc_stub; }
  return viewCache;
}

// ---------- view model for one document ----------
// Unit render kinds come from the data build (2611), which owns the area_type
// vocabulary: county | boc | city | statewide | partial_statewide | offmap.
function buildView(doc, layer) {
  const mem = new Map();        // county fips -> memberships [{g,u,kind}]
  const add = (f, m) => { if (!mem.has(f)) mem.set(f, []); mem.get(f).push(m); };
  const panelRows = [];         // non-county units for the side panel
  const bundles = new Map();    // bundle_id -> {id,label,fips,tally}
  let statewide = null, offmapN = 0;
  doc.groups.forEach((g) => {
    g.units.forEach((u) => {
      if (u.kind === "statewide") {
        if (!statewide) statewide = { g, u };
        layer.fipsList.forEach((f) => add(f, { g, u, kind: "statewide" }));
      } else if ((u.kind === "county" || u.kind === "boc") && u.fips) {
        add(u.fips, { g, u, kind: u.kind === "boc" ? "boc" : "direct" });
        if (u.kind === "boc") panelRows.push({ kind: "boc", g, u, fips: [u.fips] });
      } else if (u.kind === "city") {
        (u.parent_fips || []).forEach((f) => add(f, { g, u, kind: "city" }));
        if (!(u.parent_fips || []).length) offmapN++;
        panelRows.push({ kind: "city", g, u, fips: u.parent_fips || [] });
      } else if (u.kind === "partial_statewide") {
        // Whole state EXCEPT named carve-outs, stated as one aggregate unit. The
        // complement is never enumerated, so painting the state would assert 9
        // counties that the document excludes (open decision D-01): panel only.
        offmapN++;
        panelRows.push({ kind: "partial", g, u, fips: [] });
      } else if (u.fips) {
        add(u.fips, { g, u, kind: "direct" });
      } else {
        // reservation areas, ZCTAs, labor-market areas: real waiver areas, no geometry
        offmapN++;
        panelRows.push({ kind: "offmap", g, u, fips: [] });
      }
    });
    const b = bundles.get(g.bundle_id) || { id: g.bundle_id, label: g.bundle_label, fips: [], tally: new Map() };
    if (!b.label && g.bundle_label) b.label = g.bundle_label;
    g.units.forEach((u) => {
      if ((u.kind === "county" || u.kind === "boc") && u.fips) {
        b.fips.push(u.fips);
        const k = g.group_action || "none";
        b.tally.set(k, (b.tally.get(k) || 0) + 1);
      }
    });
    bundles.set(g.bundle_id, b);
  });
  // Fill class per county: approved > denied > withdrawn > no action; a county-specific
  // membership beats a statewide one at equal priority. City units mark the
  // parent county but never set its fill.
  const fill = new Map();
  mem.forEach((list, f) => {
    let best = null, bs = -1;
    list.forEach((m) => {
      if (m.kind === "city") return;
      const s = actionInfo(m.g.group_action).prio * 2 + (m.kind !== "statewide" ? 1 : 0);
      if (s > bs) { bs = s; best = m; }
    });
    if (best) fill.set(f, { rule: ruleAttr(best.g.criterion_code), action: best.g.group_action });
  });
  return { mem, fill, panelRows, bundles, statewide, offmapN };
}

// ---------- tooltip ----------
const tip = $("wm-tip");
function showTip(html, ev) { tip.innerHTML = html; tip.hidden = false; moveTip(ev); }
function hideTip() { tip.hidden = true; }
function moveTip(ev) {
  if (tip.hidden || !ev) return;
  const m = 14, r = tip.getBoundingClientRect();
  let x = ev.clientX + m, y = ev.clientY + m;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - m;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - m;
  tip.style.transform = `translate(${Math.max(8, x)}px,${Math.max(8, y)}px)`;
}

function seedLine(u) {
  if (u.seed === true) {
    if (u.qualifying_basis === "own_designation") return "Qualified on its own designation";
    return "Qualified on its own" + (u.own_rate != null ? " — rate " + fmtRate(u.own_rate) : "");
  }
  if (u.seed === false) return "Carried by its group" + (u.own_rate != null ? " — own rate " + fmtRate(u.own_rate) : "");
  return "Qualifying basis unknown";
}

function kvBlock(title, obj) {
  let h = `<div class="tip-kv"><span class="tip-kvt">${esc(title)}</span>`;
  Object.keys(obj).forEach((k) => {
    const v = obj[k];
    if (v == null) return;
    h += `<div class="tip-line">${esc(k.replace(/_/g, " "))}: ${esc(typeof v === "object" ? JSON.stringify(v) : v)}</div>`;
  });
  return h + "</div>";
}

function membershipHTML(m, view) {
  const g = m.g, u = m.u, ai = actionInfo(g.group_action);
  let h = '<div class="tip-mem">';
  h += `<div class="tip-rule"><span class="sw" data-rule="${ruleAttr(g.criterion_code)}"></span>${esc(ruleLabel(g.criterion_code))}<span class="chip ${ai.cls}">${ai.chip}</span></div>`;
  if (m.kind === "city") h += `<div class="tip-ctx">${esc(u.name)} (${esc(areaLabel(u.area_type) || "city")})${m.fips && !m.fips.length ? " — no parent county in the current reference" : " — within this county"}</div>`;
  else if (m.kind === "boc") h += `<div class="tip-ctx">Balance of ${esc(u.name)} County</div>`;
  else if (m.kind === "statewide") h += `<div class="tip-ctx">Statewide waiver</div>`;
  else if (m.kind === "partial") h += `<div class="tip-ctx">Statewide except named counties — the covered set is stated as a count, never listed, so it is not drawn</div>`;
  else if (m.kind === "offmap") h += `<div class="tip-ctx">${esc(areaLabel(u.area_type))} — no county geometry</div>`;
  if (u.orig_text && u.orig_text !== u.name) h += `<div class="tip-verb">“${esc(u.orig_text)}”</div>`;
  if (u.non_standard_note) h += `<div class="tip-line">${esc(u.non_standard_note)}</div>`;
  if (g.criterion_verbatim) h += `<div class="tip-verb">“${esc(g.criterion_verbatim)}”</div>`;
  if (g.criterion_code === "other" && g.criterion_other_explanation)
    h += `<div class="tip-line">${esc(g.criterion_other_explanation)}</div>`;
  if (g.state_alternative_coverage)
    h += `<div class="tip-line">State alternative coverage: ${esc(g.state_alternative_coverage)}</div>`;
  h += `<div class="tip-line">${seedLine(u)}</div>`;
  const b = view.bundles.get(g.bundle_id);
  if (b && b.fips.length > 1) {
    const parts = [];
    b.tally.forEach((n, k) => {
      parts.push(n + " " + (k === "none" ? "no action" : actionInfo(k).chip.toLowerCase()));
    });
    h += `<div class="tip-line">Part of ${b.label ? "“" + esc(b.label) + "”" : "a combined area"} — ${b.fips.length} counties: ${parts.join(", ")}</div>`;
  }
  h += `<div class="tip-line">${ai.word}${g.group_action_reason ? " — " + esc(g.group_action_reason) : ""}</div>`;
  if (g.waiver_effective || g.waiver_expiry)
    h += `<div class="tip-line num">Waiver ${fmtDate(g.waiver_effective) || "?"} → ${fmtDate(g.waiver_expiry) || "?"}</div>`;
  const lu = g.local_unemployment || {};
  if (lu.rate != null) {
    let s = `Group rate ${fmtRate(lu.rate)}`;
    const w = windowLabel(lu);
    if (w) s += ` (${w})`;
    if (typeof g.national_rate_cited === "number") s += ` · national ${fmtRate(g.national_rate_cited)}`;
    h += `<div class="tip-line num">${s}</div>`;
  }
  if (typeof g.national_rate_cited === "string") h += `<div class="tip-verb">${esc(g.national_rate_cited)}</div>`;
  // extension points — populated in a future data build
  if (u.unemployment) h += kvBlock("Unemployment", u.unemployment);
  if (u.optimality) h += kvBlock("Optimality", u.optimality);
  return h + "</div>";
}

function countyTipHTML(f) {
  const layer = curLayer(), view = curView();
  const ms = view.mem.get(f) || [];
  let h = `<div class="tip-head"><b>${esc(layer.nameByFips.get(f))} County</b><span class="tip-fips">${f}</span></div>`;
  if (!ms.length) return h + '<div class="tip-none">Not part of this waiver request.</div>';
  ms.forEach((m) => { h += membershipHTML(m, view); });
  return h;
}

function panelTipHTML(row) {
  const kindLabel = { city: "City", boc: "Balance of county", partial: "Partial statewide" }[row.kind]
    || (row.kind === "offmap" ? areaLabel(row.u.area_type) : "");
  let h = `<div class="tip-head"><b>${esc(row.u.name)}</b><span class="tip-fips">${kindLabel}</span></div>`;
  return h + membershipHTML(row, curView());
}

// ---------- map rendering + hover ----------
function renderMap() {
  const layer = curLayer(), view = curView();
  const gC = $("wm-counties"), gO = $("wm-overlays"), gCity = $("wm-cities");
  gC.textContent = ""; gO.textContent = ""; gCity.textContent = ""; $("wm-co").textContent = "";
  $("wm-bundle").setAttribute("d", ""); $("wm-hov").setAttribute("d", "");
  layer.fipsList.forEach((f) => {
    const p = document.createElementNS(svgNS, "path");
    p.setAttribute("d", layer.dByFips.get(f));
    p.setAttribute("class", "cty");
    p.dataset.fips = f;
    const fl = view.fill.get(f);
    if (fl) {
      p.dataset.rule = fl.rule;
      if (fl.action == null) p.classList.add("noact");
      const pat = actionInfo(fl.action).pat;   // null only for 'approved'
      if (pat) {
        const o = document.createElementNS(svgNS, "path");
        o.setAttribute("d", layer.dByFips.get(f));
        o.setAttribute("class", "pat");
        o.setAttribute("fill", `url(#wm-${pat})`);
        gO.appendChild(o);
      }
    }
    gC.appendChild(p);
  });
  $("wm-mesh").setAttribute("d", layer.meshInner);
  $("wm-outer").setAttribute("d", layer.outer);
  // one ring marker per parent county, however many cities share it
  const marked = new Set();
  view.panelRows.forEach((r) => {
    if (r.kind !== "city") return;
    r.fips.forEach((f) => {
      const c = layer.centroidByFips.get(f);
      if (!c || marked.has(f)) return;
      marked.add(f);
      const g = document.createElementNS(svgNS, "g");
      g.setAttribute("class", "wm-city");
      g.setAttribute("transform", `translate(${c[0].toFixed(1)},${c[1].toFixed(1)})`);
      g.dataset.fips = f;
      g.innerHTML = '<circle r="5" class="halo"></circle><circle r="5" class="ring"></circle>';
      gCity.appendChild(g);
    });
  });
  const off = $("wm-offmap");
  off.hidden = !view.offmapN;
  if (view.offmapN) off.textContent = `+${view.offmapN} off-map area${view.offmapN > 1 ? "s" : ""} — see panel`;
}

function coHighlight(fipsList, exclude) {
  const co = $("wm-co"), layer = curLayer();
  fipsList.forEach((f) => {
    if (f === exclude || !layer.dByFips.has(f)) return;
    const p = document.createElementNS(svgNS, "path");
    p.setAttribute("d", layer.dByFips.get(f));
    p.setAttribute("class", "co");
    p.setAttribute("vector-effect", "non-scaling-stroke");
    co.appendChild(p);
  });
}
function clearCo() { $("wm-co").textContent = ""; $("wm-bundle").setAttribute("d", ""); }

let hovFips = null;
function applyCountyHover(f, ev) {
  if (f === hovFips) { if (f) moveTip(ev); return; }
  hovFips = f;
  S.hover = f ? { type: "county", fips: f } : null;
  clearCo();
  $("wm-hov").setAttribute("d", f ? curLayer().dByFips.get(f) : "");
  if (!f) { hideTip(); return; }
  // merged outline + co-highlight for every multi-county bundle this county belongs to
  const view = curView(), doc = curDoc(), layer = curLayer();
  let bd = "";
  const done = new Set();
  (view.mem.get(f) || []).forEach((m) => {
    const b = view.bundles.get(m.g.bundle_id);
    if (b && b.fips.length > 1 && !done.has(b.id)) {
      done.add(b.id);
      bd += bundleD(doc.doc_stub, b.id, b.fips, layer);
      coHighlight(b.fips, f);
    }
  });
  $("wm-bundle").setAttribute("d", bd);
  showTip(countyTipHTML(f), ev);
}

// ---------- controls / header / panel / legend / footer ----------
function renderControls() {
  const stSel = $("wm-state");
  if (!stSel.options.length) {
    Object.keys(DATA.states)
      .map((c) => [DATA.states[c].name, c])
      .sort((a, b) => a[0].localeCompare(b[0]))
      .forEach(([n, c]) => stSel.add(new Option(n, c)));
  }
  stSel.value = S.state;
  const fys = stateFys(S.state), fySel = $("wm-fy");
  fySel.textContent = "";
  fys.forEach((fy) => fySel.add(new Option("FY " + fy, fy)));
  fySel.value = S.fy;
  $("wm-fy-prev").disabled = fys.indexOf(S.fy) <= 0;
  $("wm-fy-next").disabled = fys.indexOf(S.fy) >= fys.length - 1;
  const docs = curDocs(), seg = $("wm-docseg");
  seg.hidden = docs.length < 2;
  seg.textContent = "";
  if (docs.length > 1) docs.forEach((d, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "wm-segbtn" + (i === S.docIdx ? " on" : "");
    b.setAttribute("aria-pressed", i === S.docIdx);
    b.textContent = d.doc_label || d.doc_stub;
    b.dataset.i = i;
    seg.appendChild(b);
  });
}

function renderDocHead() {
  const doc = curDoc(), view = curView();
  $("wm-viewtitle").textContent = `${DATA.states[S.state].name} · FY ${S.fy}`;
  $("wm-doclabel").textContent = doc.doc_label || doc.doc_stub;
  $("wm-doctype").textContent = DOCTYPE[doc.document_type] || doc.document_type || "";
  const banner = $("wm-banner");
  const partial = view.panelRows.find((r) => r.kind === "partial");
  if (view.statewide || partial) {
    const src = view.statewide || partial, ai = actionInfo(src.g.group_action);
    banner.hidden = false;
    banner.className = "wm-chip wm-banner " + ai.cls;
    banner.textContent = (view.statewide ? "Statewide waiver — "
                                         : "Statewide except named counties — ") + ai.word.toLowerCase();
  } else banner.hidden = true;
  // Source PDF: direct link from file://, otherwise copy an `open` command
  const holder = $("wm-pdf");
  holder.textContent = "";
  if (location.protocol === "file:") {
    const a = document.createElement("a");
    a.className = "wm-btn";
    a.href = "../../" + doc.source_pdf;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "Source PDF";
    holder.appendChild(a);
  } else {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "wm-btn";
    b.textContent = "Source PDF";
    b.addEventListener("click", () => copyCmd("open " + doc.source_pdf));
    holder.appendChild(b);
  }
  // Request strip. Some documents print the expiry as a sentence rather than a date
  // ("This waiver extension is effective October 1, 2015 through December 31, 2015"),
  // and the extractor transcribes what the page says. Only date-shaped values go in
  // the strip; the prose is moved down to the note, where it reads as the sentence
  // it is instead of dangling after the word "expires".
  const rq = doc.request || {}, seg = [], prose = [];
  const dated = (v) => (isoish(v) ? fmtDate(v) : null);
  if (!isoish(rq.expiration_date) && rq.expiration_date) prose.push(String(rq.expiration_date));
  const req = dated(rq.date_state_request), resp = dated(rq.response_date);
  const impl = dated(rq.implementation_date), exp = dated(rq.expiration_date);
  if (req && resp) seg.push(`Requested ${req} → response ${resp}`);
  else if (req) seg.push(`Requested ${req}`);
  else if (resp) seg.push(`FNS response ${resp}`);
  if (impl && exp) seg.push(`Implemented ${impl} → expires ${exp}`);
  else if (impl) seg.push(`Implemented ${impl}`);
  else if (exp) seg.push(`Expires ${exp}`);
  let h = seg.map((s) => `<span class="num">${s}</span>`).join('<span class="wm-dot">·</span>');
  if (rq.possible_double_counting)
    h += ` <span class="chip a-warn" title="${esc(rq.double_counting_note || "Possible double counting")}">⚠ possible double counting</span>`;
  const strip = $("wm-request");
  strip.innerHTML = h;
  strip.hidden = !h;
  // v1_5 extraction notes: why a referenced area got no row, what a partial-statewide
  // grant actually covers — the context that is nowhere in the group/unit records.
  const text = prose.concat([rq.non_conforming_reason, rq.notes]).filter(Boolean).join(" — ");
  $("wm-notetext").textContent = text;
  $("wm-note").hidden = !text;
}

function renderPanel() {
  const view = curView(), layer = curLayer(), body = $("wm-panelbody");
  body.textContent = "";
  if (!curDoc().groups.length) {
    body.innerHTML = '<p class="wm-empty">No areas recorded in this document.</p>';
    return;
  }
  if (!view.panelRows.length) {
    body.innerHTML = '<p class="wm-empty">All applied areas are counties.</p>';
    return;
  }
  view.panelRows.forEach((r, i) => {
    const ai = actionInfo(r.g.group_action);
    const names = r.fips.map((f) => layer.nameByFips.get(f)).filter(Boolean);
    const ctx = r.kind === "city"
        ? (names.length ? "in " + names.join(", ") + (names.length > 1 ? " Counties" : " County")
                        : "city — no parent county in the current reference")
      : r.kind === "boc" ? "balance of county"
      : r.kind === "partial" ? "statewide except named counties — not drawn"
      : areaLabel(r.u.area_type) + " — not drawn on map";
    const div = document.createElement("div");
    div.className = "wm-row";
    div.dataset.row = i;
    div.innerHTML = `<div class="wm-rowmain"><span class="sw" data-rule="${ruleAttr(r.g.criterion_code)}"></span>` +
      `<div><div class="wm-rowname">${esc(r.u.name)}${r.kind === "city" ? " city" : ""}</div>` +
      `<div class="wm-rowctx">${esc(ctx)}</div></div></div>` +
      `<span class="chip ${ai.cls}">${ai.chip}</span>`;
    body.appendChild(div);
  });
}

function renderLegend() {
  const view = curView();
  const counts = new Map();
  let anyRej = false, anyNo = false, anyWd = false;
  view.fill.forEach((fl) => {
    counts.set(fl.rule, (counts.get(fl.rule) || 0) + 1);
    if (fl.action === "rejected") anyRej = true;
    if (fl.action === "withdrawn_by_state") anyWd = true;
    if (fl.action == null) anyNo = true;
  });
  let h = "";
  RULE_ORDER.forEach((k) => {
    // fixed map key: every criterion level is always listed (dimmed when absent
    // from this document); "uncoded" is a data-quality fold, not a level
    if (k === "uncoded" && !counts.has(k)) return;
    const n = counts.get(k) || 0;
    h += `<span class="lg${n ? "" : " lg-off"}"><span class="sw" data-rule="${k}"></span>${esc(k === "uncoded" ? "No criterion recorded" : ruleLabel(k))}<span class="lg-n">${n}</span></span>`;
  });
  h += `<span class="lg${anyRej ? "" : " lg-off"}"><span class="sw sw-hatch"></span>denied</span>`;
  h += `<span class="lg${anyWd ? "" : " lg-off"}"><span class="sw sw-cross"></span>withdrawn by the state</span>`;
  h += `<span class="lg${anyNo ? "" : " lg-off"}"><span class="sw sw-dots"></span>no action recorded</span>`;
  h += '<span class="lg"><span class="sw sw-neutral"></span>not applied</span>';
  h += '<div class="lg-note">Seed status — whether a county qualified on its own rate or was carried by its group — is shown in each county’s tooltip.</div>';
  $("wm-legend").innerHTML = h;
}

function renderFoot() {
  // The corpus can span several extraction arms; name the one that produced the
  // document on screen, and give the whole-corpus arm list after it.
  const doc = curDoc();
  const arms = (DATA.extraction_arms || []).map((a) => `${a.arm} (${a.docs})`).join(", ");
  const corpus = DATA.corpus
    ? `${DATA.corpus.states} states · ${DATA.corpus.documents} documents` : "";
  $("wm-foot").textContent =
    `${doc.doc_stub} · extracted under ${doc.arm || "?"} · ${DATA.extraction_spec} · `
    + `schema ${DATA.schema_version}` + (corpus ? ` · corpus: ${corpus}` : "")
    + (arms ? ` from ${arms}` : "");
}

// ---------- CSV export ----------
function docCSV(doc) {
  const cols = ["doc_stub", "state", "fiscal_year", "extraction_arm", "doc_label", "gid", "bundle_label",
    "qualification_level", "criterion_code", "criterion_label", "group_action", "group_action_reason",
    "state_alternative_coverage", "group_rate", "group_rate_window",
    "national_rate_cited", "waiver_effective", "waiver_expiry", "unit_name", "orig_text", "area_type", "kind",
    "fips", "parent_fips", "balance_of_county", "qualifying_basis", "seed", "own_rate",
    "non_standard_geography", "non_standard_note"];
  const q = (v) => {
    if (v == null) return "";
    v = String(v);
    return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  };
  const rows = [cols.join(",")];
  doc.groups.forEach((g) => {
    const lu = g.local_unemployment || {};
    const win = [lu.window_type, [lu.start, lu.end].filter(Boolean).join("..")].filter(Boolean).join(" ");
    g.units.forEach((u) => {
      rows.push([doc.doc_stub, S.state, S.fy, doc.arm, doc.doc_label, g.gid, g.bundle_label,
        g.qualification_level, g.criterion_code, g.criterion_code ? ruleLabel(g.criterion_code) : "",
        g.group_action, g.group_action_reason, g.state_alternative_coverage,
        lu.rate, win, g.national_rate_cited, g.waiver_effective, g.waiver_expiry, u.name, u.orig_text,
        u.area_type, u.kind, u.fips, (u.parent_fips || []).join(";"), u.balance_of_county, u.qualifying_basis,
        u.seed == null ? "unknown" : u.seed, u.own_rate,
        u.non_standard_geography, u.non_standard_note].map(q).join(","));
    });
  });
  return rows.join("\n");
}

// ---------- clipboard + toast ----------
function toast(msg) {
  const t = $("wm-toast");
  t.textContent = msg;
  t.hidden = false;
  t.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.classList.remove("show"); t.hidden = true; }, 3600);
}
function copyCmd(cmd) {
  const done = () => toast("Hosted page can’t open local files — command copied, paste in a terminal at the repo root.");
  const fallback = () => {
    const ta = document.createElement("textarea");
    ta.value = cmd;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* best effort */ }
    ta.remove();
    done();
  };
  if (navigator.clipboard && navigator.clipboard.writeText)
    navigator.clipboard.writeText(cmd).then(done, fallback);
  else fallback();
}

// ---------- URL hash sync (#map/nd/2025/0 | #rules[/slug] | #pack) ----------
function normalize() {
  if (!DATA.states[S.state]) {
    S.state = Object.keys(DATA.states)
      .sort((a, b) => DATA.states[a].name.localeCompare(DATA.states[b].name))[0];
  }
  const fys = stateFys(S.state);
  if (!DATA.states[S.state].fys[S.fy]) S.fy = fys[fys.length - 1];
  if (!(S.docIdx >= 0 && S.docIdx < curDocs().length)) S.docIdx = 0;
}
function writeHash() {
  // a slugged rules hash (#rules/rounding) is left in place — it is already correct
  if (S.tab === "rules" && /^#rules(\/|$)/.test(location.hash)) return;
  const h = S.tab === "rules" ? "#rules"
    : S.tab === "pack" ? "#pack"
    : `#map/${S.state.toLowerCase()}/${S.fy}/${S.docIdx}`;
  if (location.hash === h) return;
  try { history.replaceState(null, "", h); } catch (e) { location.hash = h; }
}
function readHash() {
  const h = location.hash || "";
  let m = /^#map\/([a-z]{2,3})\/(\d{4})\/(\d+)$/i.exec(h);
  if (m) { S.tab = "map"; S.state = m[1].toUpperCase(); S.fy = m[2]; S.docIdx = +m[3]; return; }
  m = /^#rules(?:\/([a-z0-9-]+))?$/i.exec(h);
  if (m) { S.tab = "rules"; S.rulesSlug = m[1] || null; return; }
  if (/^#pack$/i.test(h)) { S.tab = "pack"; return; }
  // legacy pre-tab form (#nd/2025/0); anything unparseable falls through to map defaults
  m = /^#([a-z]{2,3})\/(\d{4})\/(\d+)$/i.exec(h);
  if (m) { S.state = m[1].toUpperCase(); S.fy = m[2]; S.docIdx = +m[3]; }
  S.tab = "map";
}

// ---------- tab switching ----------
// Views are shown/hidden as whole sections; the map render path is untouched.
// The set-packing demo lives in its own IIFE (2612h) and is initialized once,
// lazily, via a CustomEvent — the only contact point between the two scripts.
let rulesInited = false, packInited = false;
function syncView() {
  ["map", "rules", "pack"].forEach((tb) => {
    $("wm-view-" + tb).hidden = tb !== S.tab;
    const b = $("wm-tab-" + tb);
    b.setAttribute("aria-selected", tb === S.tab);
    b.classList.toggle("on", tb === S.tab);
  });
  if (S.tab === "map") {
    renderAll();
  } else {
    if (S.tab === "rules" && !rulesInited) { rulesInited = true; renderRulesExample(); }
    if (S.tab === "pack" && !packInited) { packInited = true; document.dispatchEvent(new CustomEvent("wm:pack-init")); }
    writeHash();
  }
  if (S.tab === "rules" && S.rulesSlug) {
    const el = $("wm-r-" + S.rulesSlug);
    if (el) el.scrollIntoView({ block: "start" });
    S.rulesSlug = null;
  } else if (syncView._prev !== undefined && syncView._prev !== S.tab) {
    window.scrollTo(0, 0);
  }
  syncView._prev = S.tab;
}

// ---------- rules tab: worked example (TN FY2005), built from the payload ----------
// Looked up by doc_stub, not index, so a re-extracted payload cannot silently point
// the figure at a different document; if the stub ever leaves the corpus the prose
// stands alone and the figure says why it is absent.
const EXAMPLE_STUB = "tn-abawd-response-fy2005";
function renderRulesExample() {
  const holder = $("wm-rules-example");
  if (!holder) return;
  const st = DATA.states.TN;
  const docs = (st && st.fys["2005"]) || [];
  const doc = docs.find((d) => d.doc_stub === EXAMPLE_STUB);
  if (!doc) {
    holder.innerHTML = '<p class="wm-empty">The TN FY2005 document is not in the current extraction payload, so the figure is omitted; the narrative above still describes it.</p>';
    return;
  }
  const link = `#map/tn/2005/${docs.indexOf(doc)}`;
  const order = { pct20_above_natl: 0, lsa: 1, pct10_statutory: 2 };
  const groups = doc.groups.slice().sort((a, b) => {
    const c = (order[a.criterion_code] ?? 9) - (order[b.criterion_code] ?? 9);
    if (c) return c;
    return (a.qualification_level === "joint_aggregate" ? 0 : 1) - (b.qualification_level === "joint_aggregate" ? 0 : 1);
  });
  let rows = "";
  groups.forEach((g) => {
    const ai = actionInfo(g.group_action), lu = g.local_unemployment || {};
    const n = g.units.length;
    const carried = g.units.filter((u) => u.seed === false).length;
    const name = g.bundle_label || (n === 1 ? g.units[0].name : `${n} areas`);
    const joint = g.qualification_level === "joint_aggregate";
    let basis = joint ? `joint — ${n} units` : (n === 1 ? "on its own" : `each of ${n} units on its own`);
    if (carried) basis += `, ${carried} carried`;
    let rate = lu.rate != null ? fmtRate(lu.rate) : "—";
    const w = lu.rate != null ? windowLabel(lu) : "";
    rows += `<tr><td><span class="sw" data-rule="${ruleAttr(g.criterion_code)}"></span> ${esc(ruleLabel(g.criterion_code))}</td>` +
      `<td>${esc(name)}</td><td class="num">${esc(basis)}</td>` +
      `<td class="num">${esc(rate)}${w ? `<span class="wm-exwin">${esc(w)}</span>` : ""}</td>` +
      `<td><span class="chip ${ai.cls}">${ai.chip}</span></td></tr>`;
  });
  holder.innerHTML =
    `<div class="wm-extop"><span class="wm-doclabel">${esc(doc.doc_label || doc.doc_stub)}</span>` +
    `<a class="wm-btn" href="${link}">Open this document in the map →</a></div>` +
    `<div class="wm-extable"><table><thead><tr><th>Criterion</th><th>Area / bundle</th>` +
    `<th>Qualification</th><th>Rate (window)</th><th>FNS action</th></tr></thead>` +
    `<tbody>${rows}</tbody></table></div>`;
}

function renderAll() {
  normalize();
  renderControls();
  renderDocHead();
  renderMap();
  renderPanel();
  renderLegend();
  renderFoot();
  applyCountyHover(null);
  writeHash();
}

// ---------- events ----------
$("wm-state").addEventListener("change", (e) => { S.state = e.target.value; S.fy = null; S.docIdx = 0; renderAll(); });
$("wm-fy").addEventListener("change", (e) => { S.fy = e.target.value; S.docIdx = 0; renderAll(); });
const stepFy = (d) => {
  const fys = stateFys(S.state), i = fys.indexOf(S.fy) + d;
  if (i >= 0 && i < fys.length) { S.fy = fys[i]; S.docIdx = 0; renderAll(); }
};
$("wm-fy-prev").addEventListener("click", () => stepFy(-1));
$("wm-fy-next").addEventListener("click", () => stepFy(1));
$("wm-docseg").addEventListener("click", (e) => {
  const b = e.target.closest(".wm-segbtn");
  if (b) { S.docIdx = +b.dataset.i; renderAll(); }
});
$("wm-csv").addEventListener("click", () => {
  const doc = curDoc();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([docCSV(doc)], { type: "text/csv" }));
  a.download = doc.doc_stub + ".csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
});
window.addEventListener("hashchange", () => { readHash(); syncView(); });
$("wm-tabs").addEventListener("click", (e) => {
  const b = e.target.closest(".wm-tab");
  if (b && b.dataset.tab !== S.tab) { S.tab = b.dataset.tab; syncView(); }
});

const svg = $("wm-svg");
svg.addEventListener("pointermove", (ev) => {
  const t = ev.target.closest("[data-fips]");
  applyCountyHover(t ? t.dataset.fips : null, ev);
});
svg.addEventListener("pointerleave", () => applyCountyHover(null));

let panelRow = null;
const pb = $("wm-panelbody");
pb.addEventListener("pointermove", (ev) => {
  const row = ev.target.closest(".wm-row");
  if (row === panelRow) { if (row) moveTip(ev); return; }
  panelRow = row;
  clearCo();
  if (!row) { hideTip(); S.hover = null; return; }
  const r = curView().panelRows[+row.dataset.row];
  S.hover = { type: "unit", row: +row.dataset.row };
  coHighlight(r.fips);
  showTip(panelTipHTML(r), ev);
});
pb.addEventListener("pointerleave", () => { panelRow = null; clearCo(); hideTip(); S.hover = null; });

// ---------- boot ----------
// Corpus scope, computed once: it describes the payload, not the current view.
(() => {
  const codes = Object.keys(DATA.states);
  let lo = Infinity, hi = -Infinity;
  codes.forEach((c) => stateFys(c).forEach((fy) => { lo = Math.min(lo, +fy); hi = Math.max(hi, +fy); }));
  const nDocs = (DATA.corpus && DATA.corpus.documents) ||
    codes.reduce((n, c) => n + Object.values(DATA.states[c].fys).reduce((m, d) => m + d.length, 0), 0);
  $("wm-scope").textContent =
    `${codes.length} states extracted so far · ${nDocs} documents · FY${lo}–FY${hi} · `
    + codes.sort().join(" ");
})();

readHash();
syncView();
})();
