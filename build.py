#!/usr/bin/env python3
"""Obsidianのレシピ帳.md からレシピ部分だけを抜き出し、docs/index.html を生成する。"""
import hashlib, json, re, sys, datetime
from pathlib import Path

SRC = Path("/Users/user1/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/自炊/レシピ帳.md")
ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template.html"
OUT = ROOT / "docs" / "index.html"
SW_SRC = ROOT / "sw.template.js"
SW_OUT = ROOT / "docs" / "sw.js"

# 取り込む ## 見出し → (id, 短い表示名)
CATEGORIES = {
    "白米のおかず": ("gohan", "ごはん"),
    "鶏むね肉": ("tori", "鶏むね"),
    "茄子": ("nasu", "茄子"),
    "魚": ("sakana", "魚"),
    "パスタ": ("pasta", "パスタ"),
    "うどん（冷凍うどん）": ("udon", "うどん"),
    "一人鍋": ("nabe", "鍋"),
    "味噌汁の具ローテーション": ("miso", "味噌汁"),
    "冷凍・解凍と保存期限": ("hozon", "保存"),
}
TAGS = ["豚こま", "鶏むね", "ツナ", "サバ缶", "鮭", "シーフード", "にんじん", "玉ねぎ", "長ねぎ",
        "ほうれん草", "ブロッコリー", "ピーマン", "茄子", "豆腐", "油揚げ",
        "切り干し大根", "トマト缶", "うどん", "パスタ", "わかめ", "じゃがいも"]
TAG_ALIASES = {"鶏むね": ["鶏むね", "むね肉", "茹で鶏"], "サバ缶": ["サバ水煮缶", "サバ缶", "サバ味噌煮缶"],
               "長ねぎ": ["長ねぎ", "ねぎ"], "ツナ": ["ツナ"], "鮭": ["鮭"]}


def parse_blocks(lines):
    """Markdown の一部(段落・箇条書き・番号付き・表)をブロック配列にする。"""
    blocks, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append({"t": "table", "head": rows[0], "rows": rows[1:]})
            continue
        if re.match(r"^- ", ln):
            items = []
            while i < len(lines) and re.match(r"^- ", lines[i]):
                items.append(lines[i][2:].strip()); i += 1
            blocks.append({"t": "ul", "items": items}); continue
        if re.match(r"^\d+\. ", ln):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]).strip()); i += 1
            blocks.append({"t": "ol", "items": items}); continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(- |\d+\. |\|)", lines[i]):
            para.append(lines[i].strip()); i += 1
        blocks.append({"t": "p", "text": " ".join(para)})
    return blocks


def split_title(raw):
    """'1. 鶏むねの照り焼き（15分・常備菜）' → ('鶏むねの照り焼き', '15分', ['常備菜'])"""
    raw = re.sub(r"^\d+\. ", "", raw).strip()
    time, badges = None, []
    m = re.search(r"（([^）]*)）$", raw)
    if m:
        for part in m.group(1).split("・"):
            if re.fullmatch(r"\d+分", part): time = part
            elif part: badges.append(part)
        raw = raw[: m.start()].strip()
    return raw, time, badges


def detect_tags(text):
    found = []
    for tag in TAGS:
        for alias in TAG_ALIASES.get(tag, [tag]):
            if alias in text:
                found.append(tag); break
    return found


def block_text(blocks):
    out = []
    for b in blocks:
        if b["t"] == "p": out.append(b["text"])
        elif b["t"] in ("ul", "ol"): out += b["items"]
        else: out += [" ".join(r) for r in [b["head"]] + b["rows"]]
    return " ".join(out)


def parse(md):
    lines = md.splitlines()
    sections, cur = [], None
    for ln in lines:
        if ln.startswith("## "):
            cur = {"name": ln[3:].strip(), "lines": []}; sections.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)
    cats = []
    for sec in sections:
        if sec["name"] not in CATEGORIES: continue
        cid, short = CATEGORIES[sec["name"]]
        # ### で分割
        intro, subs, sub = [], [], None
        for ln in sec["lines"]:
            if ln.startswith("### "):
                sub = {"title": ln[4:].strip(), "lines": []}; subs.append(sub)
            elif sub is None: intro.append(ln)
            else: sub["lines"].append(ln)
        intro_blocks = parse_blocks(intro)
        recipes = []
        if cid == "miso":
            # 番号付きリストの各項目を1枚のカードにする
            rest = []
            for b in intro_blocks:
                if b["t"] == "ol":
                    for n, item in enumerate(b["items"], 1):
                        m = re.match(r"^(.*?)（(.*)）$", item)
                        title, note = (m.group(1), m.group(2)) if m else (item, "")
                        blocks = [{"t": "p", "text": note}] if note else []
                        recipes.append({"id": f"{cid}-{n}", "title": title.strip(), "time": None,
                                        "badges": [], "tags": detect_tags(item), "blocks": blocks})
                else: rest.append(b)
            intro_blocks = rest
        for n, s in enumerate(subs, 1):
            title, time, badges = split_title(s["title"])
            blocks = parse_blocks(s["lines"])
            recipes.append({"id": f"{cid}-{n}", "title": title, "time": time, "badges": badges,
                            "tags": detect_tags(title + " " + block_text(blocks)), "blocks": blocks})
        cats.append({"id": cid, "name": sec["name"], "short": short,
                     "reference": cid == "hozon", "intro": intro_blocks, "recipes": recipes})
    return cats


def main():
    md = SRC.read_text(encoding="utf-8")
    updated = re.search(r"^updated:\s*(\S+)", md, re.M)
    data = {"source_updated": updated.group(1) if updated else "",
            "built": datetime.date.today().isoformat(),
            "tags": TAGS, "categories": parse(md)}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    ver = hashlib.sha1(html.encode()).hexdigest()[:10]
    html = html.replace("__VER__", ver)
    OUT.write_text(html, encoding="utf-8")
    SW_OUT.write_text(SW_SRC.read_text(encoding="utf-8").replace("__VER__", ver), encoding="utf-8")
    n = sum(len(c["recipes"]) for c in data["categories"])
    print(f"built {OUT} ver={ver} categories={len(data['categories'])} recipes={n}")
    for c in data["categories"]:
        print(f"  {c['short']:4s} {len(c['recipes']):2d}  " + " / ".join(r['title'] for r in c['recipes'])[:110])


if __name__ == "__main__":
    main()
