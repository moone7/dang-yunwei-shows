# 党韫葳 · 演出排期（月光档案）

自动抓取自 [saoju.net](https://y.saoju.net) 音乐剧演出数据库，本地离线生成展示页（月光夜空风）。

## 在线预览
https://moone7.github.io/dang-yunwei-shows/

## 本地使用
- 查看：双击 `index.html`（自包含，无需联网）
- 更新数据：`python dang_yunwei_scraper.py`
- 未来场 / 其它来源补充：编辑 `supplement.json`（不会被重抓覆盖）
- 换演员抓取：`python dang_yunwei_scraper.py --artist-id <id> --name <姓名>`

## 文件
- `dang_yunwei_scraper.py` 抓取脚本（仅 Python 标准库，零第三方依赖）
- `template.html` 展示页模板（月光夜空风）
- `shows.json` 抓取数据存档
- `index.html` 生成的展示页（自包含）
- `supplement.json` 手工补充的演出（如《四大美女》未来场）
- `README.md` 本文件

## 说明
数据仅供个人追演参考，版权归原作者与各平台所有。
