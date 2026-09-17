// 定向探针模板：复制这个文件改「步骤」段。
// 用法：node probe.mjs http://127.0.0.1:8730/ [种子…]
// 约定：结论以**纯 ASCII 转义**的 JSON 打出来（控制台编码会弄坏中文）。
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const URL_ = process.argv[2];
const SEEDS = process.argv.slice(3);
const PORT = 9360;                                  // 撞端口就换一个
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const profile = mkdtempSync(join(tmpdir(), "probe-"));
const edge = spawn(EDGE, ["--headless", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "--window-size=1440,900", "about:blank"], { stdio: "ignore" });

async function page() {
  for (let i = 0; i < 80; i++) {
    try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const p = l.find(t => t.type === "page"); if (p) return p; } catch {}
    await sleep(200);
  }
  throw new Error("no CDP");
}
const ws = new WebSocket((await page()).webSocketDebuggerUrl);
let id = 0; const pending = new Map(); const errors = [];
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.method === "Runtime.exceptionThrown") { const d = m.params.exceptionDetails;
    errors.push("JS: " + ((d.exception && d.exception.description) || d.text).slice(0, 200)); }
  if (m.method === "Log.entryAdded" && m.params.entry.level === "error") { const t = m.params.entry.text || "";
    if (!/favicon/i.test(t) && !/404/.test(t)) errors.push("console: " + t.slice(0, 150)); }
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
await new Promise(r => (ws.onopen = r));
const send = (method, params = {}) => new Promise(res => {
  const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params }));
});
await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable");
async function js(expr) {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.result && r.result.exceptionDetails) errors.push("eval: " + r.result.exceptionDetails.text);
  const v = r.result && r.result.result; return v ? v.value : undefined;
}
const clickText = (t) => js(`(()=>{const a=[...document.querySelectorAll("button,.mc-btn,.btn,.card,.pick-card")];
  const e=a.find(x=>x.textContent.includes(${JSON.stringify(t)}));if(!e)return false;e.click();return true;})()`);
const foot = () => js('(()=>{const b=document.querySelector("#dialog .dfoot .btn.p");if(!b)return false;b.click();return true;})()');
const snap = () => js(`(()=>({mask:document.getElementById("mask").classList.contains("on"),
  bare:document.getElementById("dialog").classList.contains("bare"),
  cards:document.querySelectorAll("#dBody .card").length, pending:!!(STATE&&STATE.pending)}))()`);
const dump = (o) => console.log(JSON.stringify(o).replace(/[\u0080-\uffff]/g, c => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0")));

/* ---------------- 步骤（改这里） ---------------- */
const out = {};
await send("Page.navigate", { url: URL_ }); await sleep(1200);
await clickText("\u5f00\u59cb\u6e38\u620f"); await sleep(250);
await clickText("\u521b\u5efa\u65b0\u5bf9\u5c40"); await sleep(350);
await js(`(()=>{const s=document.getElementById("cSeed");if(s)s.value=${JSON.stringify(SEEDS[0] || "")};
  const d=document.getElementById("cDiff");if(d)d.value="a0";
  const r=document.getElementById("cRandom");if(r)r.checked=false;
  const t=document.getElementById("cTurns");if(t)t.value=32;})()`);
await clickText("\u521b\u5efa\u5e76\u5f00\u59cb"); await sleep(1200);
for (let i = 0; i < 6; i++) {                        // 走完开局的「发现」
  if (!(await js('document.getElementById("mask").classList.contains("on")'))) break;
  await js('(()=>{const c=document.querySelectorAll("#dBody .card")[0];if(c)c.click();})()');
  await sleep(150); await foot(); await sleep(450);
}
out.boot = await snap();
/* ---------------- 断言 + 输出 ---------------- */
out.errors = errors;
dump(out);
edge.kill(); ws.close(); process.exit(0);
