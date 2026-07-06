"""Parse an Unstop get-user-ml-submissions JSON dump -> public/private score table.
Usage: read_subs.py <dump.json>   (never handles the bearer token; only the score response)."""
import json, sys

d = json.load(open(sys.argv[1]))
rows = d.get("data", d if isinstance(d, list) else [])
if not rows:
    print("no rows / unexpected payload:", str(d)[:300]); sys.exit(1)
rows.sort(key=lambda r: r.get("created_at", ""))
best = None
print(f"{len(rows)} submissions:")
for r in rows:
    pub, prv = r.get("score"), r.get("private_score")
    print(f"  {str(r.get('created_at'))[:16]}  pub {pub}   priv {prv}")
    try:
        f = float(prv)
        best = f if best is None else max(best, f)
    except (TypeError, ValueError):
        pass
print(f"best private on this account: {best}")
