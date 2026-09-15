// 浏览器对局压力测试：CDP 驱动。
// - 导航/菜单用真实鼠标事件（Input.dispatchMouseEvent）
// - 其余交互用浏览器原生 click()（触发与点击相同的处理器，可靠且覆盖 UI 逻辑）
// 用法：node tools/browser_playtest.mjs url=http://127.0.0.1:8767/ games=30 turns=8 port=9340
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = Object.fromEntries(process.argv.slice(2).map((a) => a.split("=")));
const URL = args.url || "http://127.0.0.1:8767/";
const GAMES = Number(args.games || 30);
const TURNS = String(args.turns || 12);
const PORT = Number(args.port || 9340);
const BUDGET = Number(args.budget || 480) * 1000;
const EDGE = args.edge || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const profile = mkdtempSync(join(tmpdir(), "playtest-"));
const edge = spawn(EDGE, ["--headless", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "--window-size=1440,900", "about:blank"], { stdio: "ignore" });

async function target() {
  for (let i = 0; i < 80; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const p = l.find((t) => t.type === "page"); if (p) return p; } catch {}
    await sleep(200);
  }
  throw new Error("无法连接 CDP");
}
const page = await target();
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0; const pending = new Map(); const errors = [];
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.method === "Runtime.exceptionThrown") { const d = m.params.exceptionDetails; errors.push("JS异常: " + ((d.exception && d.exception.description) || d.text)); }
  if (m.method === "Log.entryAdded" && m.params.entry.level === "error") { const t = m.params.entry.text || ""; if (!/favicon/i.test(t) && !/404/.test(t)) errors.push("控制台错误: " + t); }
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
await new Promise((r) => (ws.onopen = r));
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable");

async function evalJS(expr) {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.result && r.result.exceptionDetails) errors.push("求值异常: " + r.result.exceptionDetails.text);
  const res = r.result && r.result.result;
  return res ? res.value : undefined;
}
async function mouseClickAt(x, y) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
}
// 真实鼠标点击（用于菜单）
async function mouseClickText(txt) {
  const r = await evalJS(`(()=>{const a=[...document.querySelectorAll("button,.mc-btn,.btn")];const e=a.find(x=>x.textContent.trim()===${JSON.stringify(txt)})||a.find(x=>x.textContent.includes(${JSON.stringify(txt)}));if(!e)return null;e.scrollIntoView&&e.scrollIntoView({block:"center"});const b=e.getBoundingClientRect();if(b.width<1)return null;return {x:b.left+b.width/2,y:b.top+b.height/2};})()`);
  if (!r) return false; await mouseClickAt(r.x, r.y); return true;
}
async function clickText(txt) {
  return evalJS(`(()=>{const a=[...document.querySelectorAll("button,.mc-btn,.btn,.pick-card,.card")];const e=a.find(x=>x.textContent.trim()===${JSON.stringify(txt)})||a.find(x=>x.textContent.includes(${JSON.stringify(txt)}));if(!e)return false;e.scrollIntoView&&e.scrollIntoView({block:"center"});e.click();return true;})()`);
}
async function clickSel(sel, idx = 0) {
  return evalJS(`(()=>{const e=document.querySelectorAll(${JSON.stringify(sel)})[${idx}];if(!e)return false;e.scrollIntoView&&e.scrollIntoView({block:"center"});e.click();return true;})()`);
}
async function state() {
  return evalJS(`(()=>{const s=(typeof STATE!=="undefined")?STATE:{};const q=x=>{const e=document.querySelector(x);return e?e.classList.contains("on"):false;};return {turn:s.turn||0, over:!!s.game_over, launcher:q("#launcher"), mask:q("#mask"), door:(s.door||[]).length, pending:!!(s.pending&&(s.pending.choice||s.pending.interaction)), tenants:(s.tenants||[]).length};})()`);
}

let clicks = 0, finished = 0, mouseClicks = 0, stuck = 0;
const START = Date.now();
const gamesLog = [];
for (let g = 0; g < GAMES; g++) {
  await send("Page.navigate", { url: URL });
  await sleep(1100);
  // 先用真实鼠标点一次主菜单（演示鼠标行为），再用 click() 确保流程
  if (await mouseClickText("开始游戏")) mouseClicks++; await sleep(250);
  if (await clickText("开始游戏")) clicks++; await sleep(300);
  if (await clickText("创建新对局")) clicks++; await sleep(300);
  await evalJS(`(()=>{const e=document.getElementById("cTurns");if(e)e.value=${JSON.stringify(TURNS)};const r=document.getElementById("cRandom");if(r)r.checked=true;})()`);
  if (await clickText("创建并开始")) clicks++; await sleep(900);
  if (g === 0) process.stdout.write("setup: " + JSON.stringify(await state()) + " toast=" + (await evalJS('(document.querySelector("#toastWrap .toast")||{}).textContent||""')) + "\n");
  let steps = 0, guard = 0;
  while (steps++ < 300) {
    if (Date.now() - START > BUDGET) { process.stdout.write("到达时间预算，提前结束\n"); break; }
    const s = await state();
    if (s.over) { finished++; break; }
    if (s.launcher) { if (++guard > 25) { stuck++; break; } if (await clickText("开始游戏")) clicks++; await sleep(150); continue; }
    if (s.mask) {
      const picked = (await clickSel("#dBody .card")) || (await clickSel("#dBody .pick-card"));
      if (picked) { await clickSel("#dialog .dfoot .btn.p"); }
      else if (!((await clickSel("#dBody .btn.p")) || (await clickSel("#dBody .pick-row .btn.p")))) {
        await evalJS('(()=>{const b=[...document.querySelectorAll("#dialog .dfoot .btn")].pop(); if(b) b.click();})()');
      }
      clicks++; await sleep(70); continue;
    }
    const roll = Math.random();
    if (s.door > 0) { if (await clickText("处理门口")) clicks++; }
    else if (roll < 0.12) { if (await clickText("指派搜索")) clicks++; }
    else if (roll < 0.18) { if (await clickSel(".turn-controls button", 0)) clicks++; }
    else { if (!(await clickSel(".turn-controls button.p", 0)) && (await clickText("结束回合"))) clicks++; else clicks++; }
    await sleep(20);
  }
  if (steps >= 300) { stuck++; errors.push(`第 ${g + 1} 局步数超限`); }
  gamesLog.push(`#${g + 1} 步=${steps} turn=${(await state()).turn} over=${(await state()).over}`);
  if ((g + 1) % 5 === 0 || g === GAMES - 1) process.stdout.write(`进度 ${g + 1}/${GAMES}\n${gamesLog.slice(-5).join("\n")}\n`);
}
console.log(JSON.stringify({ games: GAMES, finished, clicks, mouseClicks, stuck, errorCount: errors.length, errors: errors.slice(0, 30) }, null, 2));
edge.kill();
ws.close();
process.exit(0);
