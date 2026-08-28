#!/usr/bin/env python3
"""Pull openings from public ATS JSON endpoints (Greenhouse / Lever / Ashby).

These are documented public job-board APIs meant for consumption. No login,
no scraping, no ToS problem.

Usage:  python3 fetch_ats.py greenhouse:stripe lever:netflix ashby:openai
"""
import json, sys, urllib.request
UA = {"User-Agent": "jobhunt/1.0"}

def _get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as f:
            return json.load(f)
    except Exception:
        return None

def greenhouse(c):
    d = _get(f"https://boards-api.greenhouse.io/v1/boards/{c}/jobs") or {}
    return [(c, "greenhouse", j.get("title",""),
             (j.get("location") or {}).get("name",""), j.get("absolute_url","")) for j in d.get("jobs",[])]

def lever(c):
    d = _get(f"https://api.lever.co/v0/postings/{c}?mode=json")
    return [] if not isinstance(d, list) else [
        (c,"lever", j.get("text",""), (j.get("categories") or {}).get("location",""), j.get("hostedUrl","")) for j in d]

def ashby(c):
    d = _get(f"https://api.ashbyhq.com/posting-api/job-board/{c}") or {}
    return [(c,"ashby", j.get("title",""), j.get("location",""), j.get("jobUrl","")) for j in d.get("jobs",[])]

BOARDS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}

if __name__ == "__main__":
    rows = []
    for arg in sys.argv[1:]:
        board, _, company = arg.partition(":")
        fn = BOARDS.get(board)
        if not fn:
            print(f"unknown board: {board}"); continue
        r = fn(company)
        print(f"  {board:11s} {company:22s} {len(r):4d} postings")
        rows += r
    for c, b, t, l, u in rows:
        print(f"{c}\t{t}\t{l}\t{u}")
