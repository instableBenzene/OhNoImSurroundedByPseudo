/*
 * 重新生成 assets/fonts/ 里的随作品字体（Noto Sans SC 子集）。
 *
 * 只在内容新增了大量生僻字、或者上游字体更新时才需要跑。需要 Node：
 *
 *     npm install subset-font
 *     node tools/vibehub/make_font_subset.mjs
 *
 * 子集范围 = weiren_game / dlc / resourcepacks 下全部文本文件出现过的字符
 * + ASCII 可打印字符 + 常用全角标点。
 */

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import subsetFont from "subset-font";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT_DIR = path.join(REPO, "assets", "fonts");
const CACHE = path.join(os.tmpdir(), "vibehub-build");
const SOURCE = "https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/SubsetOTF/SC/";
const FACES = [
  ["NotoSansSC-Regular.otf", "weiren-sans-regular.woff2"],
  ["NotoSansSC-Bold.otf", "weiren-sans-bold.woff2"],
];
const EXTS = new Set([".py", ".html", ".json", ".md", ".txt", ".js", ".vbs", ".mjs"]);
const SKIP = new Set(["__pycache__", ".git", "runtime", "saves", "logs", "node_modules"]);
const EXTRA_PUNCT = "　、。〈〉《》「」『』【】〔〕・ー—…‰′″“”‘’±×÷≈≤≥≠→←↑↓★☆♦◆●○※§¥€£©®™°％";

function collectChars() {
  const chars = new Set();
  for (const top of ["weiren_game", "dlc", "resourcepacks"]) {
    const walk = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (SKIP.has(entry.name)) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) { walk(full); continue; }
        if (!EXTS.has(path.extname(entry.name).toLowerCase())) continue;
        try {
          for (const ch of fs.readFileSync(full, "utf8")) chars.add(ch);
        } catch (e) { /* 读不了就当没有 */ }
      }
    };
    walk(path.join(REPO, top));
  }
  for (let code = 0x20; code < 0x7f; code++) chars.add(String.fromCharCode(code));
  for (const ch of EXTRA_PUNCT) chars.add(ch);
  return [...chars].filter((c) => c === " " || c.trim() !== "" || c === "　").sort().join("");
}

async function download(name) {
  fs.mkdirSync(CACHE, { recursive: true });
  const target = path.join(CACHE, name);
  if (fs.existsSync(target) && fs.statSync(target).size > 1_000_000) return target;
  const url = SOURCE + name;
  console.log("downloading", url);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  fs.writeFileSync(target, Buffer.from(await res.arrayBuffer()));
  return target;
}

const text = collectChars();
console.log("charset:", text.length, "characters");
fs.mkdirSync(OUT_DIR, { recursive: true });
for (const [source, target] of FACES) {
  const src = await download(source);
  const buf = fs.readFileSync(src);
  const out = await subsetFont(buf, text, { targetFormat: "woff2" });
  fs.writeFileSync(path.join(OUT_DIR, target), out);
  console.log(`${target}: ${buf.length} -> ${out.length} bytes`);
}
