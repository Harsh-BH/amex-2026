"""Leaderboard poller — snapshot the public API every 15 min until the deadline.

Appends one row per (tick, team) for the top-90 board to scratchpad/lb_poll.csv, and logs
any CHANGED best-score events to scratchpad/lb_events.csv (team, old->new, implied count
delta, timestamp). Restart-safe: dedupes by (team_id, score).

Run:  nohup .venv/bin/python scratchpad/lb_poller.py >> scratchpad/lb_poller.log 2>&1 &
"""
import csv
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLL = ROOT / "lb_poll.csv"
EVENTS = ROOT / "lb_events.csv"
URL = ("https://unstop.com/api/public/live-leaderboard/290112/CodeContest"
       "?page={page}&per_page=30&filterName=timestamp&filterValue=0&undefined=true")
INTERVAL = 900
PAGES = 3            # top 90 covers the pack + our primary (rank ~69)

last_best: dict[int, str] = {}
if POLL.exists():
    with POLL.open() as fh:
        for row in csv.DictReader(fh):
            last_best[int(row["team_id"])] = row["score"]

for p in (POLL, EVENTS):
    if not p.exists():
        p.write_text("ts,team_id,rank,score,team,org,finish_time\n" if p is POLL
                     else "ts,team_id,team,old_score,new_score,delta_counts,finish_time\n")

while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        rows = []
        for page in range(1, PAGES + 1):
            req = urllib.request.Request(URL.format(page=page),
                                         headers={"Accept": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=30))
            rows.extend(d["data"]["data"])
            time.sleep(2)
        with POLL.open("a", newline="") as fh, EVENTS.open("a", newline="") as ev:
            w, we = csv.writer(fh), csv.writer(ev)
            for r in rows:
                team = r.get("team") or {}
                org = ((team.get("players") or [{}])[0].get("organisation") or "")[:60]
                tid = int(r["team_id"])
                sc = str(r["score"])
                prev = last_best.get(tid)
                if prev != sc:
                    w.writerow([ts, tid, r["rank"], sc, team.get("team_name", ""), org,
                                r.get("finish_time", "")])
                    if prev is not None:
                        dc = round((float(sc) - float(prev)) * 70000)
                        we.writerow([ts, tid, team.get("team_name", ""), prev, sc, dc,
                                     r.get("finish_time", "")])
                    last_best[tid] = sc
        print(f"{ts} tick ok ({len(rows)} rows)", flush=True)
    except Exception as e:                       # transient API failures must not kill the watch
        print(f"{ts} tick failed: {e}", flush=True)
    time.sleep(INTERVAL)
