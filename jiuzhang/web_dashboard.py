"""JiuZhang Web Dashboard — FastAPI + htmx research monitoring interface.

Provides live experiment feed, research history, metrics, controls, and export.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(
    title="JiuZhang Research Dashboard",
    description="World-Class Autonomous Mathematical Research Platform",
    version="3.0.0",
)

STATIC_DIR = Path(__file__).parent / "static" / "web"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_research_state = {
    "running": False, "question": "", "experiments": [],
    "metrics": {}, "activity": [],
}
_websocket_clients: list[WebSocket] = []


# ── Dashboard HTML ───────────────────────────────────────────────────

def _render_dashboard() -> str:
    q = _research_state["question"] or "No active research"
    dot = "running" if _research_state["running"] else "idle"
    exps = _research_state["experiments"][-10:]
    activity = "\n".join(
        f'<div class="line">{line}</div>'
        for line in _research_state["activity"][-20:]
    ) or '<div class="line" style="color:var(--dim)">Waiting for experiments...</div>'

    exp_rows = ""
    for i, exp in enumerate(reversed(exps)):
        s = exp.get("status", "-")
        strength = f'{exp.get("conjecture_strength", 0):.3f}' if exp.get("conjecture_strength") is not None else "-"
        conf = f'{exp.get("proof_confidence", 0):.3f}' if exp.get("proof_confidence") is not None else "-"
        desc = (exp.get("description", "-") or "-")[:80]
        ts = (exp.get("timestamp", "-") or "-")[:16]
        exp_rows += f'<tr><td>{i+1}</td><td><span class="badge {s}">{s}</span></td><td>{strength}</td><td>{conf}</td><td>{desc}</td><td>{ts}</td></tr>'

    m = _research_state.get("metrics", {})
    n_exp = len(_research_state["experiments"])
    kept = sum(1 for e in _research_state["experiments"] if e.get("status") == "keep")
    sr = f"{kept/max(n_exp,1)*100:.0f}%" if n_exp > 0 else "N/A"

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>JiuZhang Research Dashboard</title>
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#c9d1d9;--dim:#8b949e;--accent:#58a6ff;--success:#3fb950;--danger:#f85149;--warning:#d2991d;}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,monospace;min-height:100vh}}
.header{{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 24px;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:1.2rem;color:var(--accent)}}
.status-dot{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:8px}}
.status-dot.running{{background:var(--success);animation:pulse 2s infinite}}
.status-dot.idle{{background:var(--dim)}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.grid{{display:grid;grid-template-columns:2fr 1fr;gap:16px;padding:16px 24px;max-width:1400px;margin:0 auto}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px}}
.card h2{{font-size:.95rem;color:var(--accent);margin-bottom:12px}}
.activity-log{{max-height:400px;overflow-y:auto;font-family:'SF Mono','Fira Code',monospace;font-size:.82rem}}
.activity-log .line{{padding:4px 0;border-bottom:1px solid var(--border);color:var(--dim);font-size:.77rem}}
.metrics-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.metric{{text-align:center;padding:8px;background:var(--bg);border-radius:4px}}
.metric .value{{font-size:1.5rem;font-weight:bold;color:var(--accent)}}
.metric .label{{font-size:.7rem;color:var(--dim);text-transform:uppercase}}
.btn{{padding:8px 16px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);cursor:pointer;font-size:.85rem;transition:all .2s}}
.btn:hover{{background:var(--border)}}
.btn.primary{{background:var(--accent);color:#000;border-color:var(--accent)}}
.btn.danger{{border-color:var(--danger);color:var(--danger)}}
.btn.small{{padding:4px 10px;font-size:.75rem}}
.controls{{display:flex;gap:8px;margin-top:12px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th,td{{text-align:left;padding:8px;border-bottom:1px solid var(--border)}}
th{{color:var(--dim);font-weight:normal;text-transform:uppercase;font-size:.7rem}}
.badge{{padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:bold}}
.badge.keep{{background:var(--success);color:#000}}
.badge.discard{{background:var(--warning);color:#000}}
.badge.crash{{background:var(--danger)}}
.badge.pass,.badge.warn{{background:var(--success);color:#000}}
.chart-container{{height:200px}}
input[type="text"]{{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px;color:var(--text);width:100%}}
@media(max-width:768px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="header">
<div><h1><span class="status-dot {dot}" id="status-dot"></span>JiuZhang Research</h1></div>
<div style="color:var(--dim)" id="question-display">{q}</div>
</div>
<div class="grid">
<div>
<div class="card"><h2>Activity Log</h2>
<div class="activity-log" id="activity-log" hx-get="/api/activity" hx-trigger="every 2s">{activity}</div></div>
<div class="card" style="margin-top:16px"><h2>Experiment History</h2>
<div id="experiments-table" hx-get="/api/experiments" hx-trigger="every 3s">
<table><thead><tr><th>#</th><th>Status</th><th>Strength</th><th>Confidence</th><th>Description</th><th>Time</th></tr></thead><tbody>{exp_rows}</tbody></table></div></div>
<div class="card" style="margin-top:16px"><h2>Controls</h2>
<div class="controls">
<button class="btn primary" hx-post="/api/start" hx-swap="none">Start</button>
<button class="btn" hx-post="/api/pause" hx-swap="none">Pause</button>
<button class="btn" hx-post="/api/resume" hx-swap="none">Resume</button>
<button class="btn danger" hx-post="/api/stop" hx-swap="none">Stop</button>
<input type="text" id="inject-input" placeholder="Inject correction..."/>
<button class="btn small" onclick="inject()">Send</button>
</div></div></div>
<div>
<div class="card"><h2>Metrics</h2>
<div class="metrics-grid" id="metrics-grid" hx-get="/api/metrics" hx-trigger="every 3s">
<div class="metric"><div class="value">{n_exp}</div><div class="label">Experiments</div></div>
<div class="metric"><div class="value">{sr}</div><div class="label">Success Rate</div></div>
<div class="metric"><div class="value">{m.get('tokens','0')}</div><div class="label">Tokens</div></div>
<div class="metric"><div class="value">{m.get('best_score','-')}</div><div class="label">Best Score</div></div>
<div class="metric"><div class="value">{m.get('provider','-')}</div><div class="label">Provider</div></div>
<div class="metric"><div class="value">{m.get('uptime','-')}</div><div class="label">Uptime</div></div>
</div></div>
<div class="card" style="margin-top:16px"><h2>Progress</h2><div class="chart-container"><canvas id="progress-chart"></canvas></div></div>
<div class="card" style="margin-top:16px"><h2>Export</h2>
<div class="controls">
<a href="/api/export/json" class="btn small">JSON</a>
<a href="/api/export/markdown" class="btn small">Markdown</a>
<a href="/api/export/notebook" class="btn small">Notebook</a>
</div></div></div></div>
<script>
function inject(){{var t=document.getElementById('inject-input').value.trim();if(!t)return;fetch('/api/inject',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{content:t}})}});document.getElementById('inject-input').value=''}}
var ctx=document.getElementById('progress-chart').getContext('2d');
new Chart(ctx,{{type:'line',data:{{labels:[],datasets:[{{label:'Strength',data:[],borderColor:'#58a6ff',backgroundColor:'rgba(88,166,255,0.1)',tension:.3,fill:true}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{x:{{display:false}},y:{{min:0,max:1,ticks:{{color:'#8b949e'}},grid:{{color:'#30363d'}}}}}}}}}});
var ws=new WebSocket('ws://'+window.location.host+'/ws');
ws.onmessage=function(e){{var d=JSON.parse(e.data);if(d.type==='activity'){{var log=document.getElementById('activity-log');var div=document.createElement('div');div.className='line';div.innerHTML=d.message;log.insertBefore(div,log.firstChild);if(log.children.length>50)log.removeChild(log.lastChild)}}}};
</script>
</body></html>"""


# ── Routes ───────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return HTMLResponse(content=_render_dashboard())


@app.get("/api/activity")
async def get_activity():
    lines = []
    for line in _research_state["activity"][-20:]:
        lines.append(f'<div class="line">{line}</div>')
    return HTMLResponse(content="\n".join(lines))


@app.get("/api/experiments")
async def get_experiments():
    exps = _research_state["experiments"][-10:]
    rows = []
    for i, exp in enumerate(reversed(exps)):
        s = exp.get("status", "-")
        strength = f'{exp.get("conjecture_strength", 0):.3f}' if isinstance(exp.get("conjecture_strength"), (int, float)) else "-"
        conf = f'{exp.get("proof_confidence", 0):.3f}' if isinstance(exp.get("proof_confidence"), (int, float)) else "-"
        desc = (exp.get("description", "-") or "-")[:80]
        ts = (exp.get("timestamp", "-") or "-")[:16]
        rows.append(
            f'<tr><td>{i+1}</td><td><span class="badge {s}">{s}</span></td>'
            f'<td>{strength}</td><td>{conf}</td><td>{desc}</td><td>{ts}</td></tr>'
        )
    table = (
        '<table><thead><tr><th>#</th><th>Status</th><th>Strength</th>'
        '<th>Confidence</th><th>Description</th><th>Time</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )
    return HTMLResponse(content=table)


@app.get("/api/metrics")
async def get_metrics():
    m = _research_state.get("metrics", {})
    n_exp = len(_research_state["experiments"])
    kept = sum(1 for e in _research_state["experiments"] if e.get("status") == "keep")
    sr = f"{kept/max(n_exp,1)*100:.0f}%" if n_exp > 0 else "N/A"
    return HTMLResponse(content=f"""
    <div class="metric"><div class="value">{n_exp}</div><div class="label">Experiments</div></div>
    <div class="metric"><div class="value">{sr}</div><div class="label">Success Rate</div></div>
    <div class="metric"><div class="value">{m.get('tokens','0')}</div><div class="label">Tokens</div></div>
    <div class="metric"><div class="value">{m.get('best_score','-')}</div><div class="label">Best Score</div></div>
    <div class="metric"><div class="value">{m.get('provider','-')}</div><div class="label">Provider</div></div>
    <div class="metric"><div class="value">{m.get('uptime','-')}</div><div class="label">Uptime</div></div>
    """)


@app.post("/api/start")
async def start_research():
    _research_state["running"] = True
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] Research started"
    _research_state["activity"].append(msg)
    await broadcast({"type": "activity", "message": msg})
    return JSONResponse({"status": "started"})


@app.post("/api/pause")
async def pause_research():
    _research_state["running"] = False
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] Research paused"
    _research_state["activity"].append(msg)
    await broadcast({"type": "activity", "message": msg})
    return JSONResponse({"status": "paused"})


@app.post("/api/resume")
async def resume_research():
    _research_state["running"] = True
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] Research resumed"
    _research_state["activity"].append(msg)
    await broadcast({"type": "activity", "message": msg})
    return JSONResponse({"status": "resumed"})


@app.post("/api/stop")
async def stop_research():
    _research_state["running"] = False
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] Research stopped"
    _research_state["activity"].append(msg)
    await broadcast({"type": "activity", "message": msg})
    return JSONResponse({"status": "stopped"})


@app.post("/api/inject")
async def inject_correction(data: dict):
    content = data.get("content", "")
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] Human injection: {content[:100]}"
    _research_state["activity"].append(msg)
    await broadcast({"type": "activity", "message": msg})
    return JSONResponse({"status": "injected"})


@app.get("/api/export/{format}")
async def export_session(format: str):
    from jiuzhang.research_terminal import ResearchSession
    session = ResearchSession()
    for e in _research_state["experiments"]:
        session.record_result(e)
    try:
        path = session.export_session(format=format)
        return FileResponse(path, filename=path.name)
    except Exception:
        return JSONResponse({"error": f"Unknown format: {format}"}, status_code=400)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _websocket_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _websocket_clients.remove(websocket)


async def broadcast(message: dict):
    for client in list(_websocket_clients):
        try:
            await client.send_json(message)
        except Exception:
            pass


def start_web_server(host: str = "0.0.0.0", port: int = 8899, reload: bool = False):
    uvicorn.run(
        "jiuzhang.web_dashboard:app",
        host=host, port=port, reload=reload, log_level="info",
    )


if __name__ == "__main__":
    start_web_server()
