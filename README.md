# 党韫葳 · 演出排期（月光档案）

自动抓取自 [saoju.net](https://y.saoju.net) 音乐剧演出数据库，本地离线生成展示页（月光夜空风）。

## 在线预览
https://moone7.github.io/dang-yunwei-shows/

## 安装到桌面（PWA）
本页已做成 PWA，支持在安卓 Chrome / iOS Safari / 桌面 Chrome 上「添加到主屏幕」：
1. 用浏览器打开上方在线预览链接（必须是 `https://`，本地双击 `index.html` 不支持安装）。
2. 安卓 Chrome：点击菜单 →「添加到主屏幕」；iOS Safari：底部分享按钮 →「添加到主屏幕」。
3. 安装后桌面会生成一个月光图标，点击即可像 App 一样全屏打开，首次联网后会缓存页面，后续弱网/离线也能看排期。

## 本地使用
- 查看：双击 `index.html`（自包含，无需联网）
- 更新数据：`python dang_yunwei_scraper.py`
- 未来场 / 其它来源补充：编辑 `supplement.json`（不会被重抓覆盖）
- 换演员抓取：`python dang_yunwei_scraper.py --artist-id <id> --name <姓名>`

## 自动更新（GitHub Actions）
项目内置 `.github/workflows/daily.yml`：每天 **北京时间 04:00** 自动运行抓取脚本，并把最新的 `shows.json` / `index.html` 推送回仓库（GitHub Pages 随之刷新），全程无需本机参与。
- 触发方式：定时 `schedule` + 网页手动（`Actions` 标签页 → 选 `每日更新演出档案` → `Run workflow`）
- 凭据：使用 GitHub 自带的 `GITHUB_TOKEN`，**不需要你自己的 Personal Access Token**
- 注意：GitHub 运行服务器在境外，抓取国内站点偶尔可能不稳定；若某天失败，可到网页手动点一次 `Run workflow` 补救

## 文件
- `.github/workflows/daily.yml` 每日自动更新流水线
- `dang_yunwei_scraper.py` 抓取脚本（仅 Python 标准库，零第三方依赖）
- `template.html` 展示页模板（月光夜空风）
- `shows.json` 抓取数据存档
- `index.html` 生成的展示页（自包含）
- `supplement.json` 手工补充的演出（如《四大美女》未来场）
- `README.md` 本文件

## 数据来源说明
- **主源**：saoju.net 演员页（历史/已演场次，结构化程度高）。
- **巡演 / 未来场**：saoju.net 巡演页（脚本内 `TOUR_SEEDS` 配置，如《她对此感到厌烦2026巡演》），补充演员页未覆盖的分城未来场次。
- **其它来源**：大麦独占、或驻演类无逐场排期的演出（如《连璧》《四大美女》），手工补录于 `supplement.json`，重抓不会被覆盖。
- **关于大麦**：大麦的搜索/列表/接口均有风控签名层，纯本地零依赖脚本无法稳定自动抓取（GitHub 境外节点更易被拦），故未做自动化；如需大麦独占演出，请把信息填入 `supplement.json`。

## 说明
数据仅供个人追演参考，版权归原作者与各平台所有。
