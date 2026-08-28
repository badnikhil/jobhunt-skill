#!/usr/bin/env python3
"""Query Workday's public CXS JSON API, used by most large enterprise careers sites.

Tenant and site come from the careers URL:
  https://acme.wd5.myworkdayjobs.com/AcmeExternalCareers
  -> host=acme.wd5.myworkdayjobs.com  tenant=acme  site=AcmeExternalCareers
A wrong site slug returns HTTP 422 - try the exact casing from the URL.

Usage:  python3 fetch_workday.py https://acme.wd5.myworkdayjobs.com acme AcmeExternalCareers intern
"""
import json, sys, time, urllib.request

def query(base, tenant, site, text="", limit=20, offset=0):
    req = urllib.request.Request(
        f"{base}/wday/cxs/{tenant}/{site}/jobs",
        data=json.dumps({"appliedFacets":{}, "limit":limit, "offset":offset, "searchText":text}).encode(),
        headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as f:
            return json.load(f)
    except Exception as e:
        return {"_err": str(e)[:80]}

if __name__ == "__main__":
    base, tenant, site = sys.argv[1], sys.argv[2], sys.argv[3]
    text = sys.argv[4] if len(sys.argv) > 4 else ""
    for off in range(0, 100, 20):
        d = query(base, tenant, site, text, offset=off)
        if "_err" in d:
            print("ERROR:", d["_err"]); break
        posts = d.get("jobPostings", [])
        if not posts: break
        for p in posts:
            print(f"{p.get('title','')}\t{p.get('locationsText','')}\t{base}/en-US/{site}{p.get('externalPath','')}")
        time.sleep(0.4)
