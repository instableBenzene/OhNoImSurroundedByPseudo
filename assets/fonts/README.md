# 随作品打包的字体

`weiren-sans-regular.woff2` / `weiren-sans-bold.woff2` 是 **Noto Sans SC** 的子集，
只保留作品实际会用到的字符（由 `tools/vibehub/make_font_subset.mjs` 从
`weiren_game/`、`dlc/`、`resourcepacks/` 的全部文本里收集）。

为什么打包：VibeHub 托管的作品不能依赖玩家设备的系统字体。中文必须随作品带字体，
并在 Theme 默认字体或 fallback 中配置（见 `docs/STYLE.md` 的字体栈说明）。

- 上游：<https://github.com/notofonts/noto-cjk>（`Sans/SubsetOTF/SC/NotoSansSC-{Regular,Bold}.otf`）
- 许可：SIL Open Font License 1.1（见 `OFL.txt`）
- 子集范围：`weiren_game/**`、`dlc/**`、`resourcepacks/**` 里 `.py/.html/.json/.md/.txt/.js/.vbs`
  出现的全部字符 + ASCII 可打印字符与常用全角标点。玩家自己输入的存档名若含子集外的生僻字，
  会由系统字体兜底。

改内容后要重新回到这里时，跑一次 `tools/vibehub/make_font_subset.mjs`（需要 Node），
把新的 woff2 放回本目录即可。
