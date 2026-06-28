"""LLM explainer for EDA outputs — turn a table or chart into plain English via OpenAI.

    from explain import show
    show(eda.overview(), "per-feature overview")     # displays the table + prints an LLM explanation
    show(eda.plot_corr(), "correlation heatmap")     # explains the chart (vision)

stdlib-only (urllib) — no `openai` dep. Reads OPENAI_API_KEY from the env or the gitignored .env.
Tables use a cheap text model; charts auto-switch to a vision model.
"""
from __future__ import annotations
import base64, io, json, os, urllib.request, urllib.error
from pathlib import Path

_ENV = Path(__file__).resolve().parent.parent / ".env"
ENDPOINT = "https://api.openai.com/v1/chat/completions"
TEXT_MODEL = "gpt-4o-mini"      # cheap, fine for explaining tables
VISION_MODEL = "gpt-4o"        # needed for charts (images)

SYSTEM = (
    "You explain data-analysis outputs to a student team in plain, concise English. "
    "Project context: we rank 500,000 American Express Premier cardmembers by profitability to the "
    "issuer — there is NO label, we design an interpretable revenue-minus-cost score, and we are "
    "graded on how well our top-20% overlaps the true top-20%. Given a table or chart, respond with "
    "3-6 short bullets: what it shows and why it matters for the scoring framework. Be specific and "
    "skip the fluff; do not restate every number."
)


def _key() -> str:
    k = os.environ.get("OPENAI_API_KEY")
    if not k and _ENV.exists():
        for line in _ENV.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                k = line.split("=", 1)[1].strip()
    if not k:
        raise RuntimeError("OPENAI_API_KEY not found (set it in the environment or .env)")
    return k


def _post(payload: dict, timeout: int = 90) -> str:
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"[explain failed: HTTP {e.code} — {e.read().decode()[:300]}]"
    except Exception as e:  # noqa: BLE001 — surface any error inline, never crash the notebook
        return f"[explain failed: {type(e).__name__}: {e}]"


def _is_fig(obj) -> bool:
    try:
        import matplotlib.figure
        return isinstance(obj, matplotlib.figure.Figure)
    except Exception:
        return False


def explain(obj, what: str = "", model: str | None = None, max_chars: int = 6000) -> str:
    """Return a plain-English explanation of a DataFrame/Series/str/Figure via OpenAI."""
    import pandas as pd
    if _is_fig(obj):
        buf = io.BytesIO(); obj.savefig(buf, format="png", dpi=90, bbox_inches="tight")
        b64 = base64.b64encode(buf.getvalue()).decode()
        content = [{"type": "text", "text": f"Explain this chart: {what}".strip()},
                   {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]
        payload = {"model": model or VISION_MODEL, "temperature": 0.2,
                   "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]}
        return _post(payload)
    body = (obj.to_string() if isinstance(obj, (pd.DataFrame, pd.Series)) else str(obj))[:max_chars]
    user = (f"What this is: {what}\n\n" if what else "") + "Output:\n" + body
    payload = {"model": model or TEXT_MODEL, "temperature": 0.2,
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
    return _post(payload)


def show(obj, what: str = "", model: str | None = None):
    """Display the table (charts already render inline) AND print the LLM explanation. Returns obj."""
    try:
        from IPython.display import Markdown, display
        if not _is_fig(obj):
            display(obj)
        display(Markdown("**🧠 LLM:** " + explain(obj, what, model)))
    except ImportError:
        print(explain(obj, what, model))
    return obj
