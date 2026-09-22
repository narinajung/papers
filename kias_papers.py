#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIAS 통계물리 최근 논문 — 내 기기에서 갱신하는 스크립트

사용법
  1) 처음 한 번:  pip install requests beautifulsoup4
  2) 실행:        python kias_papers.py
     → Google Scholar에서 다섯 분 프로필을 최신순으로 받아
       kias-papers.html 을 만들고 브라우저로 엽니다.
     → data.json 에 스냅샷을 저장해 두었다가, 다음 실행 때
       그 뒤에 새로 올라온 논문에 "새 논문" 표시를 붙입니다.

  --offline   : Scholar에 접속하지 않고 data.json 으로만 페이지를 다시 만듭니다.
  --no-open   : 브라우저를 열지 않습니다.
  --out FILE  : 결과 파일 이름 (기본 kias-papers.html; GitHub Pages에서는 index.html)

  "새 논문" 표시: data.json 에 각 논문을 처음 본 날짜(first_seen)를 적어 두고,
  처음 본 지 30일 이내인 논문에 붙입니다.

같은 폴더에 template.html, topics.json 이 있어야 합니다.
"""
import json, re, sys, time, datetime, pathlib, webbrowser

HERE = pathlib.Path(__file__).resolve().parent
PEOPLE = [  # (Scholar user id, 표시 이름) — 사람을 바꾸려면 여기만 고치면 됩니다
    ("LY4Izs0AAAAJ", "천현명 박사님"),
    ("XZIobAQAAAAJ", "이재성 교수님"),
    ("YqWzE9sAAAAJ", "권의준 박사님"),
    ("udklDnoAAAAJ", "샤쿨"),
    ("1eukyIoAAAAJ", "최재성 박사님"),
]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PAUSE = 3  # 요청 사이 쉬는 시간(초). Scholar 차단을 피하려면 줄이지 마세요.

def norm(s):
    return re.sub(r"[^a-z0-9가-힣]+", "", s.lower())

def fetch_profile(uid, label):
    import requests
    from bs4 import BeautifulSoup
    papers, name, aff, interests, cstart = [], "", "", [], 0
    while True:
        url = (f"https://scholar.google.com/citations?user={uid}&hl=en&sortby=pubdate"
               f"&view_op=list_works&cstart={cstart}&pagesize=100")
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"{label}: Scholar 응답 {r.status_code} (잠시 차단됐을 수 있음)")
        s = BeautifulSoup(r.text, "html.parser")
        if "gs_captcha" in r.text or s.select_one("#gs_captcha_ccl"):
            raise RuntimeError(f"{label}: Scholar가 로봇 확인(캡차)을 요구함")
        if not name:
            n = s.select_one("#gsc_prf_in"); name = n.get_text(strip=True) if n else label
            a = s.select_one(".gsc_prf_il"); aff = a.get_text(strip=True) if a else ""
            interests = [x.get_text(strip=True) for x in s.select("#gsc_prf_int a")]
        rows = s.select("tr.gsc_a_tr")
        for tr in rows:
            t = tr.select_one(".gsc_a_at"); grays = tr.select(".gs_gray")
            cited = tr.select_one(".gsc_a_c a"); year = tr.select_one(".gsc_a_y span")
            href = t.get("href") if t else ""
            papers.append({
                "title": t.get_text(strip=True) if t else "",
                "authors": grays[0].get_text(strip=True) if len(grays) > 0 else "",
                "venue": grays[1].get_text(strip=True) if len(grays) > 1 else "",
                "year": year.get_text(strip=True) if year else "",
                "cited": cited.get_text(strip=True) if cited else "",
                "url": ("https://scholar.google.com" + href) if href else "",
            })
        if len(rows) < 100:
            break
        cstart += 100; time.sleep(PAUSE)
    return {"id": uid, "label": label, "name": name, "affiliation": aff,
            "interests": interests, "papers": papers}

def build(data, previous, topics, snapshot, out):
    NEW_DAYS = 30
    prev_seen = {p["id"]: {norm(x["title"]): x.get("first_seen", "") for x in p["papers"]} for p in previous}
    today = datetime.date.fromisoformat(snapshot)
    n_new = 0
    for p in data:
        seen = prev_seen.get(p["id"])
        for x in p["papers"]:
            m = re.search(r"arXiv:(\d{4}\.\d{4,5})", x["venue"])
            x["arxiv"] = m.group(1) if m else ""
            x["preprint"] = bool(m) or "bioRxiv" in x["venue"] or "medRxiv" in x["venue"]
            k = norm(x["title"])
            if seen is None:                      # 첫 실행: 기준 날짜가 없으므로 표시 안 함
                x["first_seen"] = x.get("first_seen", "")
            elif k in seen:                       # 전에 본 논문: 날짜를 이어받음
                x["first_seen"] = seen[k]
            else:                                 # 이번에 처음 본 논문
                x["first_seen"] = snapshot
            fs = x["first_seen"]
            x["new"] = bool(fs) and (today - datetime.date.fromisoformat(fs)).days <= NEW_DAYS
            n_new += x["new"]
            x["topics"] = topics.get(k, ["un"])
    payload = json.dumps({"snapshot": snapshot, "people": data}, ensure_ascii=False).replace("</", "<\\/")
    footer = ("매일 아침 자동으로 Google Scholar에서 받아 만든 페이지입니다. '새 논문'은 처음 확인한 지 30일 이내인 논문, "
              "회색 '미분류'는 아직 주제를 붙이지 않은 논문입니다.")
    html = (HERE / "template.html").read_text(encoding="utf-8")
    html = html.replace("__FOOTER__", footer).replace("__DATA__", payload)
    out.write_text(html, encoding="utf-8")
    return n_new

def main():
    offline = "--offline" in sys.argv
    out = HERE / (sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "kias-papers.html")
    topics = json.loads((HERE / "topics.json").read_text(encoding="utf-8"))
    prev_path = HERE / "data.json"
    previous = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else []
    snapshot = datetime.date.today().isoformat()

    if offline:
        if not previous:
            sys.exit("data.json 이 없어 --offline 으로는 만들 수 없습니다. 먼저 한 번 온라인으로 실행하세요.")
        data, previous = previous, previous
    else:
        try:
            import requests, bs4  # noqa
        except ImportError:
            sys.exit("먼저 실행하세요:  pip install requests beautifulsoup4")
        data = []
        for uid, label in PEOPLE:
            try:
                p = fetch_profile(uid, label)
                print(f"  {label:8s} {p['name']:18s} {len(p['papers'])}편")
                data.append(p)
            except Exception as e:
                old = next((q for q in previous if q["id"] == uid), None)
                print(f"  {label}: 받기 실패 — {e}" + ("  (지난 스냅샷을 그대로 씀)" if old else ""))
                if old: data.append(old)
            time.sleep(PAUSE)
        if not data:
            sys.exit("아무것도 받지 못했습니다. 잠시 뒤 다시 시도하거나 --offline 으로 지난 페이지를 다시 만드세요.")

    n_new = build(data, previous, topics, snapshot, out)
    if not offline:
        prev_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(p["papers"]) for p in data)
    untagged = sum(1 for p in data for x in p["papers"] if x["topics"] == ["un"])
    print(f"\n완료: {total}편, 새 논문 {n_new}편, 미분류 {untagged}편 → {out.name}")
    if untagged:
        print("미분류 논문의 주제는 Claude에게 topics.json 갱신을 부탁하거나 직접 추가하면 됩니다.")
    if "--no-open" not in sys.argv:
        webbrowser.open(out.as_uri())

if __name__ == "__main__":
    main()
