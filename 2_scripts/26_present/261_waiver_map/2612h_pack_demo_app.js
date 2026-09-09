/* Set-packing demo — self-contained IIFE. Hand-authored 6×6 dataset, manual
   group building with live feasibility readout, and a greedy solver over all
   contiguous groups of ≤6 squares. Initialized lazily on the wm:pack-init
   CustomEvent (fired by 2612b the first time the tab is shown); shares nothing
   with the map app except CSS classes. No network requests. */
(() => {
"use strict";

// Dataset verified offline (brute force over all 4,465 connected subsets ≤6:
// 790 admissible; greedy-from-scratch = 769; optimum = 896; the four metro
// squares E1 E2 F1 F2 appear in no admissible group). Threshold 6.0 = 1.2 × a
// fake 5.0% national rate; comparison is on the aggregate rate rounded half-up
// to one decimal, so the effective cutoff is 5.95%.
const CELLS = [
  { id: "A1", L: 3000, U: 255, V: 30 },  { id: "A2", L: 4000, U: 310, V: 35 },
  { id: "A3", L: 2500, U: 205, V: 25 },  { id: "A4", L: 6000, U: 330, V: 40 },
  { id: "A5", L: 5000, U: 255, V: 30 },  { id: "A6", L: 4000, U: 215, V: 25 },
  { id: "B1", L: 2000, U: 170, V: 20 },  { id: "B2", L: 5000, U: 380, V: 45 },
  { id: "B3", L: 3000, U: 215, V: 28 },  { id: "B4", L: 7000, U: 390, V: 45 },
  { id: "B5", L: 6000, U: 310, V: 35 },  { id: "B6", L: 5000, U: 270, V: 30 },
  { id: "C1", L: 8000, U: 420, V: 40 },  { id: "C2", L: 9000, U: 480, V: 50 },
  { id: "C3", L: 7000, U: 385, V: 38 },  { id: "C4", L: 8000, U: 430, V: 42 },
  { id: "C5", L: 6000, U: 335, V: 33 },  { id: "C6", L: 5000, U: 310, V: 26 },
  { id: "D1", L: 10000, U: 520, V: 55 }, { id: "D2", L: 12000, U: 610, V: 60 },
  { id: "D3", L: 9000, U: 465, V: 48 },  { id: "D4", L: 8000, U: 425, V: 44 },
  { id: "D5", L: 7000, U: 380, V: 40 },  { id: "D6", L: 6000, U: 345, V: 32 },
  { id: "E1", L: 30000, U: 1050, V: 90 },{ id: "E2", L: 25000, U: 1000, V: 80 },
  { id: "E3", L: 10000, U: 540, V: 50 }, { id: "E4", L: 9000, U: 510, V: 70 },
  { id: "E5", L: 2000, U: 230, V: 15 },  { id: "E6", L: 4000, U: 250, V: 22 },
  { id: "F1", L: 40000, U: 1240, V: 95 },{ id: "F2", L: 28000, U: 1260, V: 85 },
  { id: "F3", L: 8000, U: 430, V: 40 },  { id: "F4", L: 8000, U: 452, V: 60 },
  { id: "F5", L: 7000, U: 400, V: 65 },  { id: "F6", L: 5000, U: 290, V: 30 },
];
const THRESH = 6.0;
const MAXG = 6;                    // solver's group-size cap (manual building is uncapped)
const HUES = 5;                    // committed-group fill slots in the CSS

const BY_ID = new Map(CELLS.map((c) => [c.id, c]));
const IDS = CELLS.map((c) => c.id);
const rc = (id) => [id.charCodeAt(0) - 65, +id[1] - 1];
const NEI = new Map(IDS.map((id) => {
  const [r, c] = rc(id);
  return [id, IDS.filter((j) => {
    const [r2, c2] = rc(j);
    return Math.abs(r - r2) + Math.abs(c - c2) === 1;
  })];
}));

const round1 = (x) => Math.round(x * 10) / 10;
function agg(ids) {
  let L = 0, U = 0, V = 0;
  ids.forEach((i) => { const c = BY_ID.get(i); L += c.L; U += c.U; V += c.V; });
  const exact = 100 * U / L;
  return { L, U, V, exact, rounded: round1(exact), pass: round1(exact) >= THRESH };
}
const cellRate = (c) => 100 * c.U / c.L;
const aloneOK = (c) => round1(cellRate(c)) >= THRESH;
const slack = (c) => c.U - (THRESH / 100) * c.L;   // s_i at the 6.0% threshold
function contiguous(ids) {
  if (!ids.length) return false;
  const set = new Set(ids), seen = new Set([ids[0]]), stack = [ids[0]];
  while (stack.length) {
    NEI.get(stack.pop()).forEach((j) => {
      if (set.has(j) && !seen.has(j)) { seen.add(j); stack.push(j); }
    });
  }
  return seen.size === set.size;
}

// ---------- admissible-group enumeration (connected subsets ≤ MAXG) ----------
// Min-vertex-anchored with a banned list: each connected subset is generated
// exactly once. 6×6 grid → 4,465 subsets; instant.
function enumAdmissible() {
  const out = [];
  IDS.forEach((v) => {
    const rec = (cur, cand, banned) => {
      out.push(cur.slice());
      if (cur.length === MAXG) return;
      for (let k = 0; k < cand.length; k++) {
        const u = cand[k];
        const nb = new Set(banned);
        for (let j = 0; j < k; j++) nb.add(cand[j]);
        const next = cand.slice(k + 1);
        NEI.get(u).forEach((w) => {
          if (w > v && !cur.includes(w) && !nb.has(w) && !next.includes(w) && w !== u) next.push(w);
        });
        cur.push(u);
        rec(cur, next, nb);
        cur.pop();
      }
    };
    rec([v], NEI.get(v).filter((w) => w > v), new Set());
  });
  return out
    .map((ids) => ({ ids: ids.sort(), ...agg(ids) }))
    .filter((g) => g.pass)
    .sort((a, b) => (b.V - a.V) || (a.ids.join() < b.ids.join() ? -1 : 1));
}

// ---------- state ----------
const S = { sel: new Set(), committed: [], groups: null, running: false };
const $ = (id) => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
const CELL = 84, GAP = 6, M = 3;
const xy = (id) => { const [r, c] = rc(id); return [M + c * (CELL + GAP), M + r * (CELL + GAP)]; };
const committedIds = () => new Set(S.committed.flatMap((g) => g.ids));
const fmtN = (n) => n.toLocaleString("en-US");

let inited = false;
document.addEventListener("wm:pack-init", () => { if (!inited) { inited = true; init(); } });

function init() {
  S.groups = enumAdmissible();
  // greedy-from-scratch total, computed (not hard-coded) so a dataset edit
  // cannot leave a stale number on the scoreboard
  const taken = new Set();
  let gv = 0;
  S.groups.forEach((g) => {
    if (g.ids.every((i) => !taken.has(i))) { gv += g.V; g.ids.forEach((i) => taken.add(i)); }
  });
  $("pk-greedy").textContent = gv;
  buildGrid();
  wire();
  readout();
}

// ---------- grid ----------
function buildGrid() {
  const svg = $("pk-svg");
  svg.textContent = "";
  CELLS.forEach((c) => {
    const [x, y] = xy(c.id);
    const g = document.createElementNS(svgNS, "g");
    const r = document.createElementNS(svgNS, "rect");
    r.setAttribute("x", x); r.setAttribute("y", y);
    r.setAttribute("width", CELL); r.setAttribute("height", CELL);
    r.setAttribute("class", "pk-sq" + (aloneOK(c) ? " pk-alone" : ""));
    r.dataset.id = c.id;
    g.appendChild(r);
    const lab = document.createElementNS(svgNS, "g");
    lab.setAttribute("class", "pk-lab");
    lab.innerHTML =
      `<text class="pk-id" x="${x + 6}" y="${y + 15}">${c.id}</text>` +
      (aloneOK(c) ? `<text class="pk-tick" x="${x + CELL - 6}" y="${y + 15}" text-anchor="end">✓</text>` : "") +
      `<text class="pk-rate" x="${x + CELL / 2}" y="${y + CELL / 2 + 5}" text-anchor="middle">${cellRate(c).toFixed(1)}%</text>` +
      `<text class="pk-v" x="${x + CELL / 2}" y="${y + CELL - 9}" text-anchor="middle">V ${c.V}</text>`;
    g.appendChild(lab);
    svg.appendChild(g);
  });
  const outline = document.createElementNS(svgNS, "path");
  outline.setAttribute("id", "pk-outline");
  outline.setAttribute("class", "pk-outline");
  svg.appendChild(outline);
}

const sq = (id) => document.querySelector(`#pk-svg rect[data-id="${id}"]`);

// merged outline of committed groups: each cell expanded by half the gap so
// neighbors touch, then only exposed edges are drawn
function drawOutlines() {
  let d = "";
  S.committed.forEach((grp) => {
    const set = new Set(grp.ids);
    grp.ids.forEach((id) => {
      const [x, y] = xy(id), [r, c] = rc(id);
      const x0 = x - GAP / 2, y0 = y - GAP / 2, s = CELL + GAP;
      const has = (rr, cc) => set.has(String.fromCharCode(65 + rr) + (cc + 1));
      if (!has(r - 1, c)) d += `M${x0},${y0}h${s}`;
      if (!has(r + 1, c)) d += `M${x0},${y0 + s}h${s}`;
      if (!has(r, c - 1)) d += `M${x0},${y0}v${s}`;
      if (!has(r, c + 1)) d += `M${x0 + s},${y0}v${s}`;
    });
  });
  $("pk-outline").setAttribute("d", d);
}

// ---------- readout ----------
function verdictChips(ids) {
  if (!ids.length) return "";
  const a = agg(ids), conn = contiguous(ids);
  let h = `<span class="chip ${conn ? "a-ok" : "a-no"}">${conn ? "Contiguous" : "Not contiguous"}</span>`;
  h += `<span class="chip ${a.pass ? "a-ok" : "a-no"}">${a.rounded.toFixed(1)} ${a.pass ? "≥" : "<"} ${THRESH.toFixed(1)} — ${a.pass ? "qualifies" : "fails"}</span>`;
  return h;
}
function readout() {
  const ids = [...S.sel].sort();
  const has = ids.length > 0;
  const a = has ? agg(ids) : null;
  $("pk-n").textContent = ids.length;
  $("pk-L").textContent = has ? fmtN(a.L) : "—";
  $("pk-U").textContent = has ? fmtN(a.U) : "—";
  $("pk-exact").textContent = has ? a.exact.toFixed(2) + "%" : "—";
  $("pk-round").textContent = has ? a.rounded.toFixed(1) + "%" : "—";
  $("pk-V").textContent = has ? a.V : "—";
  $("pk-verdict").innerHTML = verdictChips(ids);
  $("pk-members").innerHTML = ids.map((i) => {
    const c = BY_ID.get(i), s = slack(c);
    return `<div><span class="num">${i}</span> — ${cellRate(c).toFixed(2)}% ` +
      `${aloneOK(c) ? "(qualifies alone)" : "(fails alone)"} · ` +
      `<span class="num">slack ${s > 0 ? "+" : ""}${Math.round(s)}</span></div>`;
  }).join("");
  $("pk-commit").disabled = !(has && contiguous(ids) && a.pass) || S.running;
  $("pk-clear").disabled = !has || S.running;
  $("pk-undo").disabled = !S.committed.length || S.running;
  $("pk-reset").disabled = !(S.committed.length || has) || S.running;
  $("pk-step").disabled = S.running;
  $("pk-run").disabled = S.running;
  const you = S.committed.filter((g) => g.who === "you").reduce((n, g) => n + g.V, 0);
  const grd = S.committed.filter((g) => g.who === "greedy").reduce((n, g) => n + g.V, 0);
  $("pk-covered").textContent = you && grd ? `${you + grd} (you ${you} · greedy ${grd})`
    : you ? `${you} (you)` : grd ? `${grd} (greedy)` : "0";
}

function log(line) {
  const el = $("pk-log");
  el.textContent += (el.textContent ? "\n" : "") + line;
  el.scrollTop = el.scrollHeight;
}
const arith = (g) => `{${g.ids.join(" ")}} — ${fmtN(g.U)}/${fmtN(g.L)} = ${g.exact.toFixed(2)}% → ${g.rounded.toFixed(1)} ${g.pass ? "≥" : "<"} 6.0 ${g.pass ? "✓" : "✗"} · +${g.V}`;

// ---------- commits ----------
function commit(ids, who) {
  const g = { ids: ids.slice().sort(), who, hue: S.committed.length % HUES, ...agg(ids) };
  S.committed.push(g);
  g.ids.forEach((i) => {
    const r = sq(i);
    r.classList.remove("pk-sel", "pk-pulse");
    r.classList.add("pk-comm");
    r.dataset.hue = g.hue;
    S.sel.delete(i);
  });
  log(`${who === "you" ? "you" : "greedy"}: ${arith(g)}`);
  drawOutlines();
  readout();
}
function undo() {
  const g = S.committed.pop();
  if (!g) return;
  g.ids.forEach((i) => { const r = sq(i); r.classList.remove("pk-comm"); delete r.dataset.hue; });
  log(`undo: {${g.ids.join(" ")}} · −${g.V}`);
  drawOutlines();
  readout();
}
function reset() {
  S.committed = [];
  S.sel.clear();
  document.querySelectorAll("#pk-svg .pk-sq").forEach((r) => {
    r.classList.remove("pk-comm", "pk-sel", "pk-pulse");
    delete r.dataset.hue;
  });
  $("pk-log").textContent = "";
  drawOutlines();
  readout();
}

// ---------- greedy ----------
function nextGreedy() {
  const taken = committedIds();
  return S.groups.find((g) => g.ids.every((i) => !taken.has(i))) || null;
}
const noMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function greedyStep(done) {
  const g = nextGreedy();
  if (!g) { log("greedy: no admissible group remains — done"); if (done) done(false); return; }
  if (noMotion()) { commit(g.ids, "greedy"); if (done) done(true); return; }
  g.ids.forEach((i) => sq(i).classList.add("pk-pulse"));
  setTimeout(() => { commit(g.ids, "greedy"); if (done) done(true); }, 450);
}
function greedyRun() {
  S.running = true;
  readout();
  const tick = () => greedyStep((more) => {
    if (more && nextGreedy()) setTimeout(tick, noMotion() ? 0 : 380);
    else { S.running = false; readout(); }
  });
  tick();
}

// ---------- events ----------
function wire() {
  $("pk-svg").addEventListener("click", (e) => {
    if (S.running) return;
    const r = e.target.closest("rect[data-id]");
    if (!r || r.classList.contains("pk-comm")) return;
    const id = r.dataset.id;
    if (S.sel.has(id)) { S.sel.delete(id); r.classList.remove("pk-sel"); }
    else { S.sel.add(id); r.classList.add("pk-sel"); }
    readout();
  });
  $("pk-commit").addEventListener("click", () => commit([...S.sel], "you"));
  $("pk-clear").addEventListener("click", () => {
    S.sel.forEach((i) => sq(i).classList.remove("pk-sel"));
    S.sel.clear();
    readout();
  });
  $("pk-step").addEventListener("click", () => { if (!S.running) greedyStep(); });
  $("pk-run").addEventListener("click", () => { if (!S.running) greedyRun(); });
  $("pk-undo").addEventListener("click", undo);
  $("pk-reset").addEventListener("click", reset);

  // hover inspector — own tip div, styled by the shared .wm-tip class
  const tip = document.createElement("div");
  tip.className = "wm-tip";
  tip.id = "pk-tip";
  tip.hidden = true;
  document.body.appendChild(tip);
  const svg = $("pk-svg");
  svg.addEventListener("pointermove", (ev) => {
    const r = ev.target.closest("rect[data-id]");
    if (!r) { tip.hidden = true; return; }
    const c = BY_ID.get(r.dataset.id), s = slack(c);
    tip.innerHTML = `<div class="tip-head"><b>${c.id}</b><span class="tip-fips">fake county</span></div>` +
      `<div class="tip-line num">labor force ${fmtN(c.L)} · unemployed ${fmtN(c.U)}</div>` +
      `<div class="tip-line num">rate ${cellRate(c).toFixed(2)}% → ${round1(cellRate(c)).toFixed(1)} ${aloneOK(c) ? "≥ 6.0 — qualifies alone" : "< 6.0 — fails alone"}</div>` +
      `<div class="tip-line num">slack at 6.0%: ${s > 0 ? "+" : ""}${Math.round(s)} · weight V = ${c.V}</div>`;
    tip.hidden = false;
    const m = 14, b = tip.getBoundingClientRect();
    let x = ev.clientX + m, y = ev.clientY + m;
    if (x + b.width > innerWidth - 8) x = ev.clientX - b.width - m;
    if (y + b.height > innerHeight - 8) y = ev.clientY - b.height - m;
    tip.style.transform = `translate(${Math.max(8, x)}px,${Math.max(8, y)}px)`;
  });
  svg.addEventListener("pointerleave", () => { tip.hidden = true; });
}
})();
