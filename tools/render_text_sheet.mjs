// 把 `tools/dump_codex_text.py` 导出的文本过一遍真实排版函数 fmt()，截图供肉眼复核。
//
// 用法：node tools/render_text_sheet.mjs <texts.json> [宽] [高]
// 关键点：**不要**用手抄的文本（源码改了它还渲旧的），也**不要**用 position:fixed + overflow
// （`captureBeyondViewport` 抓不到滚动区，长图会被截断）。
import { spawn } from "node:child_process";
import { mkdtempSync, copyFileSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [jsonPath, widthArg, heightArg] = process.argv.slice(2);
if (!jsonPath) {
  console.error("用法：node tools/render_text_sheet.mjs <texts.json> [宽] [高]");
  process.exit(2);
}
const ROOT = join(import.meta.dirname, "..");
const SRC = join(ROOT, "weiren_game", "webui", "index.html");
const DEST = join(tmpdir(), "weiren-text-sheet.html");
copyFileSync(SRC, DEST);
const TEXTS = JSON.parse(readFileSync(jsonPath, "utf-8"));

const PORT = Number(process.env.CDP_PORT || 9416);
const EDGE = process.env.EDGE_PATH || "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const profile = mkdtempSync(join(tmpdir(), "text-sheet-"));
const WIDTH = Number(widthArg || 1000);
const HEIGHT = Number(heightArg || 2600);
const edge = spawn(EDGE, ["--headless=new", "--disable-gpu", "--no-first-run",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  `--window-size=${WIDTH},${HEIGHT}`, "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function target() {
  for (let i = 0; i < 80; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page;
    } catch {}
    await sleep(200);
  }
  throw new Error("无法连接 CDP");
}

const page = await target();
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
});
await new Promise((r) => ws.addEventListener("open", r));
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params }));
});
await send("Page.enable");
await send("Runtime.enable");
await send("Page.navigate", { url: "file:///" + DEST.replace(/\\/g, "/") });
await sleep(2500);

const render = `(() => {
  const items = ${JSON.stringify(TEXTS)};
  const host = document.createElement("div");
  // relative + z-index：留在正常流里（长图能整张截），又压过启动器那层 fixed 覆盖。
  host.style.cssText = "position:relative;z-index:99999;background:#0f1314;color:#e6ebe8;" +
    "padding:20px;font-family:var(--sans,system-ui);font-size:13.5px;line-height:1.7";
  host.innerHTML = items.map((r) =>
    "<div style='margin-bottom:16px;border-left:2px solid #333c3c;padding-left:10px'>" +
    "<div style='color:#a2acaa;font-size:11px;margin-bottom:4px'>" +
    r.character + " · " + r.ability + (r.chips && r.chips.length ? "  [" + r.chips.join(" / ") + "]" : "") +
    "</div><div>" + fmt(r.text) + "</div></div>").join("");
  document.body.appendChild(host);
  return String(items.length);
})()`;
const result = await send("Runtime.evaluate", { expression: render, returnByValue: true });
console.log("rendered", result.result && result.result.result ? result.result.result.value : "?");

const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
if (shot.result && shot.result.data) {
  const out = join(tmpdir(), "weiren-text-sheet.png");
  writeFileSync(out, Buffer.from(shot.result.data, "base64"));
  console.log("png", out);
}

ws.close();
edge.kill();
