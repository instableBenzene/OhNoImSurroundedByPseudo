/* 浏览器版本（VibeHub 托管）启动器。
 *
 * 引擎是纯标准库 Python，因此用 Pyodide（CPython→WebAssembly）在页面里直接运行；
 * 前端原本请求的 /api/* 全部改成直接调用 Python（见 vibehub_bridge.py）。
 * 内容层文件资产（图标 / 头像 / 素材位）由 Python 内联成 data URL，不再需要后端。
 *
 * 存档：本机 localStorage 始终生效；登录 VibeHub 后再同步一份到 vibe.save（玩家作用域）。
 *
 * 本文件由 tools/build_vibehub.py 复制进产物根目录。
 */

/* 必须与 `vibehub deploy/update --slug` 一致，也是试玩地址的第一段路径。 */
const WORK_SLUG = "oh-no-im-surrounded-by-pseudo";

const SAVES_KEY = "weiren_static_saves_v1";
const CLOUD_KEY = "weiren_saves";
const PYODIDE_VERSION = "314.0.7";

let pyodide = null;
let saveTimer = null;
let cloudTimer = null;
let vibe = null;
let currentUser = null;

/* ------------------------------------------------------------------ 存档读写 */

function b64encode(bytes) {
  let out = "";
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK) {
    out += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  }
  return btoa(out);
}

function b64decode(text) {
  const bin = atob(text);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i) & 0xff;
  return out;
}

function snapshotStorage() {
  const files = {};
  try {
    for (const name of pyodide.FS.readdir("/app/saves")) {
      if (name === "." || name === "..") continue;
      const full = "/app/saves/" + name;
      try {
        if (pyodide.FS.isFile(pyodide.FS.stat(full).mode)) {
          files["saves/" + name] = b64encode(pyodide.FS.readFile(full));
        }
      } catch (e) { /* 读不到就跳过这一份 */ }
    }
  } catch (e) { /* 目录还没建起来 */ }
  try {
    const cfg = "/app/game_config.json";
    if (pyodide.FS.isFile(pyodide.FS.stat(cfg).mode)) {
      files["game_config.json"] = b64encode(pyodide.FS.readFile(cfg));
    }
  } catch (e) { /* 可选文件 */ }
  return files;
}

function writeFilesIntoFs(files) {
  for (const rel of Object.keys(files || {})) {
    try {
      const full = "/app/" + rel;
      const cut = full.lastIndexOf("/");
      if (cut > 0) pyodide.FS.mkdirTree(full.slice(0, cut));
      pyodide.FS.writeFile(full, b64decode(files[rel]));
    } catch (e) { console.warn("恢复存档失败", rel, e); }
  }
}

function readLocal() {
  try {
    const raw = localStorage.getItem(SAVES_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) { return null; }
}

function writeLocal(payload) {
  try { localStorage.setItem(SAVES_KEY, JSON.stringify(payload)); } catch (e) { /* 满了就算了 */ }
}

function scheduleSaveSync() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    saveTimer = null;
    const payload = { updated: Date.now(), files: snapshotStorage() };
    writeLocal(payload);
    scheduleCloudPush(payload);
  }, 600);
}

function restoreStorage() {
  const local = readLocal();
  if (local && local.files) writeFilesIntoFs(local.files);
}

/* ------------------------------------------------------------------ 云存档（vibe.save） */

function scheduleCloudPush(payload) {
  if (!vibe || !currentUser) return;
  if (cloudTimer) clearTimeout(cloudTimer);
  cloudTimer = setTimeout(async () => {
    cloudTimer = null;
    try { await vibe.save.set(CLOUD_KEY, payload); }
    catch (e) { console.warn("云端存档写入失败", e); }
  }, 1500);
}

async function restoreCloud() {
  if (!vibe || !currentUser) return;
  let cloud = null;
  try { cloud = await vibe.save.get(CLOUD_KEY); } catch (e) { console.warn("云端存档读取失败", e); }
  if (!cloud || !cloud.files) {
    scheduleCloudPush({ updated: Date.now(), files: snapshotStorage() });
    return;
  }
  const local = readLocal();
  if (local && (local.updated || 0) >= (cloud.updated || 0)) {
    scheduleCloudPush(local);
    return;
  }
  writeFilesIntoFs(cloud.files);
  writeLocal(cloud);
  if (typeof window.renderSaves === "function") { try { window.renderSaves(); } catch (e) {} }
  if (typeof window.toast === "function") window.toast("已载入云端存档");
}

/* ------------------------------------------------------------------ 账号 UI */

function mountAccountUI() {
  const inner = document.querySelector("#lpaneMain .lpane-inner");
  if (!inner || document.getElementById("vhAccount")) return;
  const row = document.createElement("div");
  row.id = "vhAccount";
  row.className = "mc-row";
  row.style.cssText = "margin-top:14px;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap";
  row.innerHTML =
    '<span id="vhAccStatus" style="font-size:12.5px;color:var(--ink2)">未登录 VibeHub（存档仅保存在本机）</span>'
    + '<button class="mc-btn" id="vhLogin" type="button">登录 VibeHub</button>'
    + '<button class="mc-btn" id="vhLogout" type="button" style="display:none">退出登录</button>';
  const foot = inner.querySelector(".mc-foot");
  if (foot) inner.insertBefore(row, foot); else inner.appendChild(row);
  row.querySelector("#vhLogin").addEventListener("click", () => {
    if (vibe) vibe.login().catch((e) => console.warn("登录失败", e));
  });
  row.querySelector("#vhLogout").addEventListener("click", () => {
    if (vibe) vibe.logout().catch((e) => console.warn("退出失败", e));
  });
}

function renderAccount() {
  const status = document.getElementById("vhAccStatus");
  const login = document.getElementById("vhLogin");
  const logout = document.getElementById("vhLogout");
  if (!status || !login || !logout) return;
  if (currentUser) {
    status.textContent = "已登录：" + (currentUser.name || currentUser.id) + "（存档同步到云端）";
    login.style.display = "none";
    logout.style.display = "";
  } else {
    status.textContent = "未登录 VibeHub（存档仅保存在本机）";
    login.style.display = "";
    logout.style.display = "none";
  }
}

async function initVibe() {
  if (!window.VibeHub || typeof window.VibeHub.init !== "function") {
    console.warn("VibeHub SDK 未加载：登录与云存档不可用，本机存档照常工作。");
    return;
  }
  try {
    vibe = await window.VibeHub.init({ work: WORK_SLUG });
  } catch (e) {
    console.warn("VibeHub.init 失败：", e);
    return;
  }
  window.vhVibe = vibe;
  vibe.onAuthChange((user) => {
    currentUser = user || null;
    renderAccount();
    if (user) restoreCloud();
  });
  if (vibe.isLoggedIn()) {
    try { currentUser = vibe.user || await vibe.login(); } catch (e) { /* 恢复失败按游客处理 */ }
  }
  renderAccount();
}

/* ------------------------------------------------------------------ 引擎加载 */

async function loadFiles(msg) {
  const manifest = await (await fetch("./app-manifest.json", { cache: "force-cache" })).json();
  const queue = (manifest.files || []).slice();
  const total = queue.length;
  let done = 0;
  const worker = async () => {
    for (;;) {
      const rel = queue.shift();
      if (rel === undefined) return;
      const res = await fetch("./app/" + rel, { cache: "force-cache" });
      if (!res.ok) throw new Error("缺少作品文件：" + rel);
      const buf = new Uint8Array(await res.arrayBuffer());
      const full = "/app/" + rel;
      const cut = full.lastIndexOf("/");
      if (cut > 0) pyodide.FS.mkdirTree(full.slice(0, cut));
      pyodide.FS.writeFile(full, buf);
      done++;
      if (done % 50 === 0 || done === total) msg("载入作品文件 " + done + " / " + total);
    }
  };
  await Promise.all(Array.from({ length: 12 }, worker));
}

export async function start(msg = () => {}) {
  msg("加载 Python 运行时（首次约 13 MB，之后走浏览器缓存）…");
  const base = new URL("./pyodide/", document.baseURI).href;
  const mod = await import(base + "pyodide.mjs");
  pyodide = await mod.loadPyodide({ indexURL: base, packageBaseUrl: base });
  window.__pyodide = pyodide;

  await loadFiles(msg);
  pyodide.FS.mkdirTree("/app/saves");
  restoreStorage();

  msg("启动游戏引擎…");
  await pyodide.runPythonAsync(`
import os, sys
os.environ["WEIREN_SAVES_DIR"] = "/app/saves"
if "/app" not in sys.path:
    sys.path.insert(0, "/app")
import vibehub_bridge
from vibehub_bridge import bridge_handle
vibehub_bridge.init()
`);

  const handle = pyodide.globals.get("bridge_handle");

  window.vhApi = function (method, path, body) {
    const payload = method === "POST"
      ? JSON.stringify(body === undefined || body === null ? {} : body)
      : "";
    let res = null;
    try { res = JSON.parse(handle(method, path, payload)); } catch (e) { res = null; }
    if (!res) return { ok: false, error: "引擎调用失败" };
    let data = null;
    try { data = JSON.parse(res.body); }
    catch (e) { data = { ok: false, error: String(res.body || "").slice(0, 400) }; }
    scheduleSaveSync();
    return data;
  };

  window.vhExport = function (path) {
    try { return JSON.parse(handle("GET", path, "")).body || ""; }
    catch (e) { return ""; }
  };

  /* 账号栏先挂上：SDK 没加载 / 未发布时也要能看到登录状态。 */
  mountAccountUI();
  renderAccount();
  await initVibe();

  msg("准备就绪");
  const overlay = document.getElementById("vhBoot");
  if (overlay) overlay.remove();
}

export const meta = { work: WORK_SLUG, pyodide: PYODIDE_VERSION };
