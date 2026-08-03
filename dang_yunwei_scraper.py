#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
党韫葳演出抓取工具  (本地离线, 数据不出本机)
------------------------------------------------------------
数据源 : saoju.net 音乐剧演出数据库  (y.saoju.net)
输出   : shows.json  —— 纯数据存档, 便于二次处理 / 版本管理
          index.html —— 自包含展示页, 数据已内联, 双击即可打开, 无需联网/服务器
用法   : python dang_yunwei_scraper.py
依赖   : 仅 Python 标准库 (urllib / ssl / html.parser / json / re)
"""

import urllib.request, ssl, os, re, json, sys, time
from html.parser import HTMLParser

# 演员信息可通过命令行参数覆盖: --artist-id <id> --name <姓名>
# （saoju 演员页 URL 形如 https://y.saoju.net/yyj/artist/<id>/show）

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# saoju 巡演页 ID: 这些巡演含党韫葳未来场/分城场次 (大麦无按人聚合入口且接口有风控,
# 故改用 saoju tour 页 —— 同源、零风控、可自动化)。需要追新巡演时手动增删此列表。
TOUR_SEEDS = [705]


def fetch_url(url):
    """抓取任意 URL (带重试)。"""
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            time.sleep(1.5)
    raise RuntimeError(f"抓取失败: {url} -> {last}")


def get_tour_title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    t = m.group(1).strip() if m else "巡演"
    t = re.split(r'[-_|]', t)[0].strip()
    return t or "巡演"


class RowParser(HTMLParser):
    """把演出 <table> 的每一行 <tr> 收集为 cell 列表 (cell 含文本与内部链接)。"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.cur_row = None
        self.cur_cell = None
        self.in_cell = False
        self.in_tr = False
        self.cur_a = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_tr = True
            self.cur_row = []
        elif tag == 'td' and self.in_tr:
            self.in_cell = True
            self.cur_cell = {'text': '', 'links': []}
        elif tag == 'a' and self.in_cell:
            self.cur_a = {'href': dict(attrs).get('href', ''), 'text': ''}

    def handle_endtag(self, tag):
        if tag == 'td' and self.in_cell:
            self.cur_row.append(self.cur_cell)
            self.cur_cell = None
            self.in_cell = False
            self.cur_a = None
        elif tag == 'tr' and self.in_tr:
            if self.cur_row:
                self.rows.append(self.cur_row)
            self.in_tr = False
            self.cur_row = None
        elif tag == 'a' and self.cur_a is not None:
            if self.cur_cell is not None and self.cur_a['text'].strip():
                self.cur_cell['links'].append(self.cur_a)
            self.cur_a = None

    def handle_data(self, data):
        if self.in_cell and self.cur_cell is not None:
            self.cur_cell['text'] += data
        if self.cur_a is not None:
            self.cur_a['text'] += data


def fetch_html(base, n):
    url = base if n <= 1 else f"{base}?page={n}"
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            time.sleep(1.5)
    raise RuntimeError(f"抓取第 {n} 页失败: {last}")


def get_max_page(html):
    nums = re.findall(r'href="\?page=(\d+)"', html)
    nums = [int(x) for x in nums]
    return max(nums) if nums else 1


def parse_row(cells):
    # 注意: 城市与剧院链接可能同在"一个 td"内, 也可能分属两个 td。
    # 因此遍历每个 cell 内的全部链接, 分别捕获, 避免 if/elif 截断。
    res = {'date': None, 'time': None, 'musical': None, 'musical_id': None,
           'role': None, 'city': None, 'city_id': None, 'stage': None, 'stage_id': None}
    for cell in cells:
        links = cell['links']
        text = cell['text'].strip()
        if links:
            for l in links:
                href = l['href']
                if '/yyj/musical/' in href:
                    res['musical'] = l['text'].strip()
                    m = re.search(r'/yyj/musical/(\d+)/', href)
                    res['musical_id'] = int(m.group(1)) if m else None
                elif '/yyj/city/' in href:
                    res['city'] = l['text'].strip()
                    m = re.search(r'/yyj/city/(\d+)/', href)
                    res['city_id'] = int(m.group(1)) if m else None
                elif '/yyj/stage/' in href:
                    res['stage'] = l['text'].strip()
                    m = re.search(r'/yyj/stage/(\d+)/', href)
                    res['stage_id'] = int(m.group(1)) if m else None
        else:
            # 纯文本 cell: 时间列(含日期/时间) 或 角色列
            dm = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
            tm = re.search(r'(\d{1,2}):(\d{2})', text)
            if dm:
                res['date'] = f"{int(dm.group(1)):04d}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
            if tm:
                res['time'] = f"{int(tm.group(1)):02d}:{tm.group(2)}"
            elif text:
                res['role'] = text
    return res


def parse_html(html):
    p = RowParser()
    p.feed(html)
    shows = []
    prev_date = None
    for cells in p.rows:
        r = parse_row(cells)
        if not r['musical']:           # 跳过表头/空行
            continue
        if r['date'] is None:          # 同日多场: 日期行缺失 -> 继承上一条
            r['date'] = prev_date
        if not r['date']:
            continue
        r['datetime'] = f"{r['date']}T{r['time']}" if r['time'] else r['date']
        shows.append(r)
        prev_date = r['date']
    return shows


def show_key(s):
    """统一去重键: 优先用 ID, 缺失时回退到名称, 兼容手工补充数据。"""
    mid = s.get('musical_id') if s.get('musical_id') is not None else s.get('musical')
    sid = s.get('stage_id') if s.get('stage_id') is not None else s.get('stage')
    return (s.get('datetime'), mid, sid)


def parse_tour(html, artist_id):
    """解析 saoju 巡演页: 页面按 [城市标题 -> 场馆标题 -> 该城场次表] 分组。
    每个场次表: 首行为角色名(<th>), 之后每行为 日期 + 各角色当场演员(<td>)。
    仅保留含有目标演员(artist_id)的场次。"""
    class TourParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.shows = []
            self.cur_city = None
            self.cur_stage = None
            self.in_table = False
            self.header = []
            self.cur_row = None
            self.cur_cell = None
            self.in_cell = False
            self.cur_a = None

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            if tag == 'table':
                self.in_table = True
                self.header = []
            elif tag == 'tr' and self.in_table:
                self.cur_row = []
            elif tag in ('td', 'th') and self.in_table and self.cur_row is not None:
                self.in_cell = True
                self.cur_cell = {'text': '', 'links': []}
            elif tag == 'a':
                self.cur_a = {'href': d.get('href', ''), 'text': ''}

        def handle_endtag(self, tag):
            if tag in ('td', 'th') and self.in_cell:
                self.cur_row.append(self.cur_cell)
                self.cur_cell = None
                self.in_cell = False
                self.cur_a = None
            elif tag == 'tr' and self.in_table and self.cur_row is not None:
                self._row(self.cur_row)
                self.cur_row = None
            elif tag == 'table':
                self.in_table = False
            elif tag == 'a' and self.cur_a is not None:
                href = self.cur_a['href']
                txt = self.cur_a['text'].strip()
                if '/yyj/city/' in href:
                    self.cur_city = txt
                elif '/yyj/stage/' in href:
                    self.cur_stage = txt
                elif self.in_cell and self.cur_cell is not None and txt:
                    self.cur_cell['links'].append(self.cur_a)
                self.cur_a = None

        def handle_data(self, data):
            if self.in_cell and self.cur_cell is not None:
                self.cur_cell['text'] += data
            if self.cur_a is not None:
                self.cur_a['text'] += data

        def _row(self, row):
            if not row:
                return
            texts = [c['text'].strip() for c in row]
            has_date = any(re.search(r'(\d{1,2})月(\d{1,2})日', t) or '年' in t for t in texts)
            has_actor = any(f'/yyj/artist/{artist_id}/' in l['href']
                            for c in row for l in c['links'])
            if not has_date and not has_actor and not self.header:
                self.header = texts          # 角色名表头行
                return
            if not has_date or not has_actor:
                return
            date_text = texts[0]
            dm = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_text)
            if dm:
                y, mo, da = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
            else:
                mm = re.search(r'(\d{1,2})月(\d{1,2})日', date_text)
                y, mo, da = time.localtime().tm_year, int(mm.group(1)), int(mm.group(2))
            tm = re.search(r'(\d{1,2}):(\d{2})', date_text)
            time_s = f"{int(tm.group(1)):02d}:{tm.group(2)}" if tm else None
            date_s = f"{y:04d}-{mo:02d}-{da:02d}"
            for i in range(1, len(row)):
                if any(f'/yyj/artist/{artist_id}/' in l['href'] for l in row[i]['links']):
                    role = self.header[i] if i < len(self.header) else None
                    self.shows.append({
                        'date': date_s, 'time': time_s,
                        'datetime': f"{date_s}T{time_s}" if time_s else date_s,
                        'musical': None, 'musical_id': None,
                        'role': role, 'city': self.cur_city, 'city_id': None,
                        'stage': self.cur_stage, 'stage_id': None,
                        'source': 'saoju-tour',
                    })

    p = TourParser()
    p.feed(html)
    return p.shows


def load_prev(here):
    """读取上一次生成的 shows.json, 作为增量对比基准。"""
    p = os.path.join(here, "shows.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f).get("shows", [])
        except Exception:
            return []
    return []


def load_supplement(here):
    """读取手工补充场次 (未来场 / 其它来源)。"""
    p = os.path.join(here, "supplement.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f).get("supplement", [])
        except Exception:
            return []
    return []


def main():
    import argparse
    ap = argparse.ArgumentParser(description="抓取 saoju.net 演员演出数据并生成离线展示页")
    ap.add_argument("--artist-id", type=int, default=1538, help="saoju 演员 ID（页面 URL 里的数字）")
    ap.add_argument("--name", default="党韫葳", help="演员姓名（用于展示页标题）")
    ap.add_argument("--out", default=None, help="输出目录（默认脚本所在目录）")
    args = ap.parse_args()

    artist_id = args.artist_id
    ARTIST = args.name
    BASE = f"https://y.saoju.net/yyj/artist/{artist_id}/show"
    here = args.out or os.path.dirname(os.path.abspath(__file__))
    print(f"[*] 抓取 {ARTIST} 演出数据 (saoju.net, id={artist_id}) ...")
    html1 = fetch_html(BASE, 1)
    maxp = get_max_page(html1)
    print(f"[*] 发现 {maxp} 页")

    all_shows = []
    for n in range(1, maxp + 1):
        html = html1 if n == 1 else fetch_html(BASE, n)
        rows = parse_html(html)
        all_shows.extend(rows)
        print(f"    - 第 {n}/{maxp} 页: {len(rows)} 场")
        if n < maxp:
            time.sleep(0.6)            # 礼貌延迟, 避免给站点压力

    # ---- 巡演页抓取 (未来场/分城场次; saoju tour 页, 零风控, 可自动化) ----
    for tid in TOUR_SEEDS:
        try:
            th = fetch_url(f"https://y.saoju.net/yyj/tour/{tid}")
            title = get_tour_title(th)
            rows = parse_tour(th, artist_id)
            for s in rows:
                s['musical'] = title
                all_shows.append(s)
            print(f"    - 巡演页 tour/{tid}《{title}》: {len(rows)} 场含{ARTIST}")
        except Exception as e:
            print(f"[!] 巡演页 tour/{tid} 抓取失败: {e}")

    # ---- 增量检测: 读取上次存档, 作为"新增"对比基准 ----
    prev = load_prev(here)
    prev_keys = {show_key(s) for s in prev}

    # 去重: 同一 日期时间 + 剧目 + 剧院 视为同一场
    seen, uniq = set(), []
    for s in all_shows:
        k = show_key(s)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(s)

    # ---- 合并手工补充 (未来场 / 其它来源) ----
    # supplement.json 中的场次不会被重抓覆盖; 若 saoju 已收录同场则跳过避免重复
    supp = load_supplement(here)
    existing_ns = {(s.get('date'), s.get('musical'), s.get('stage')) for s in uniq}
    for s in supp:
        if (s.get('date'), s.get('musical'), s.get('stage')) in existing_ns:
            continue
        k = show_key(s)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(s)

    uniq.sort(key=lambda x: x['datetime'], reverse=True)

    # ---- 更新提醒: 列出相较上次新增的场次 ----
    added = [s for s in uniq if show_key(s) not in prev_keys]
    if added:
        print(f"[+] 相较上次存档, 新增 {len(added)} 场:")
        for s in sorted(added, key=lambda x: x['datetime']):
            print(f"      {s['datetime']}  {s['musical']} · {s.get('role') or '-'} · {s['city']} {s['stage']}")
    else:
        print("[*] 无新增场次 (与上次一致)")

    data = {
        "artist": ARTIST,
        "artist_id": artist_id,
        "source": BASE,
        "updated_at": time.strftime("%Y-%m-%d"),
        "total": len(uniq),
        "shows": uniq,
    }

    json_path = os.path.join(here, "shows.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[*] 写出 shows.json ({len(uniq)} 场)")

    tpl_path = os.path.join(here, "template.html")
    out_path = os.path.join(here, "index.html")
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl = f.read()
        payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
        html_out = tpl.replace("/*SHOWS_JSON*/ null", payload)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print("[*] 生成 index.html (自包含展示页, 双击即用)")
    else:
        print("[!] 未找到 template.html, 仅生成 shows.json")

    print("[done] 完成。")


if __name__ == "__main__":
    main()
