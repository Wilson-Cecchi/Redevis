# report.py — Redevis
import os
import json
from datetime import datetime

REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "reports")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "data", "history.json")

DEVICE_ICONS = {
    "router":   "🔀",
    "tv":       "📺",
    "apple":    "🍎",
    "computer": "💻",
    "server":   "🖥",
    "phone":    "📱",
    "unknown":  "❓",
}


def load_history_for_chart() -> list:
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        return [{"timestamp": s["timestamp"], "total": s["total"]} for s in history[-10:]]
    except Exception:
        return []


def generate_report(scan: dict, diff: dict | None = None) -> str:
    new_ips     = {d["ip"] for d in diff["new"]}     if diff else set()
    removed_ips = {d["ip"] for d in diff["removed"]} if diff else set()

    rows = ""
    for device in scan["devices"]:
        ip          = device["ip"]
        hostname    = device["hostname"]
        mac         = device.get("mac", "—")
        vendor      = device.get("vendor", "—")
        os_name     = device.get("os", "—")
        latency     = device.get("latency", "—")
        device_type = device.get("device_type", "unknown")
        ports       = ", ".join([f"{p['port']}/{p['name']}" for p in device["ports"]]) or "—"
        badge       = '<span class="badge new">novo</span>' if ip in new_ips else ""

        if device_type == "unknown":
            ports_hint = ", ".join([str(p["port"]) for p in device["ports"]]) or "nenhuma"
            icon = f'<span class="tooltip-wrap" style="cursor:help">❓<span class="tooltip-text">Tipo não identificado — portas: {ports_hint}</span></span>'
        else:
            icon = DEVICE_ICONS.get(device_type, "❓")

        # Barra de latência
        try:
            lat_ms = float(latency.replace(" ms", ""))
            if lat_ms < 5:
                lat_color = "#4a9bb5"
            elif lat_ms < 20:
                lat_color = "#c8a84b"
            else:
                lat_color = "#c0392b"
            lat_width = min(int(lat_ms * 4), 100)
            lat_html = f'''<span class="lat-text">{latency}</span>
              <div class="lat-bar"><div class="lat-fill" style="width:{lat_width}%;background:{lat_color}"></div></div>'''
        except Exception:
            lat_html = latency

        rows += f"""
        <tr>
          <td>{icon} {ip}</td>
          <td>{hostname}</td>
          <td class="mac">{mac}</td>
          <td class="vendor">{vendor}</td>
          <td class="os">{os_name}</td>
          <td class="latency">{lat_html}</td>
          <td class="ports">{ports}</td>
          <td><span class="status-up">● online</span> {badge}</td>
        </tr>"""

    removed_rows = ""
    for device in (diff["removed"] if diff else []):
        device_type = device.get("device_type", "unknown")
        icon = DEVICE_ICONS.get(device_type, "❓")
        removed_rows += f"""
        <tr class="removed">
          <td>{icon} {device["ip"]}</td>
          <td>{device["hostname"]}</td>
          <td>—</td><td>—</td><td>—</td><td>—</td>
          <td><span class="status-down">● offline</span></td>
        </tr>"""

    diff_section = ""
    if diff:
        diff_section = f"""
        <div class="diff-bar">
          <span class="diff-new">▲ {len(diff["new"])} novo(s)</span>
          <span class="diff-removed">▼ {len(diff["removed"])} removido(s)</span>
        </div>"""

    # Dados do gráfico
    history_data = load_history_for_chart()
    chart_labels = [h["timestamp"] for h in history_data]
    chart_values = [h["total"] for h in history_data]
    total_online  = len(scan["devices"])
    total_offline = len(diff["removed"]) if diff else 0

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Redevis — {scan["timestamp"]}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #000; color: #fff; font-family: 'Segoe UI', sans-serif; font-size: 14px; padding: 48px; }}
    header {{ border-bottom: 1px solid rgba(255,255,255,.08); padding-bottom: 32px; margin-bottom: 32px; }}
    .logo {{ font-size: 11px; letter-spacing: .3em; color: #4a9bb5; text-transform: uppercase; margin-bottom: 12px; }}
    h1 {{ font-size: 48px; font-weight: 700; letter-spacing: -.01em; }}
    h1 span {{ color: #c8a84b; }}
    .meta {{ margin-top: 16px; font-size: 12px; color: #888; display: flex; gap: 32px; flex-wrap: wrap; }}
    .meta strong {{ color: #aaa; }}
    .search-wrap {{ margin-bottom: 24px; }}
    #search {{
      width: 100%; padding: 12px 16px;
      background: rgba(255,255,255,.03);
      border: 1px solid rgba(255,255,255,.1);
      color: #fff; font-size: 13px;
      outline: none;
    }}
    #search::placeholder {{ color: #555; }}
    .diff-bar {{ display: flex; gap: 24px; margin-bottom: 24px; padding: 14px 20px; background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.07); }}
    .diff-new {{ color: #4a9bb5; font-size: 12px; letter-spacing: .1em; }}
    .diff-removed {{ color: #c8a84b; font-size: 12px; letter-spacing: .1em; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ text-align: left; font-size: 9px; letter-spacing: .25em; color: #555; text-transform: uppercase; padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,.07); }}
    td {{ padding: 14px 16px; border-bottom: 1px solid rgba(255,255,255,.04); color: #ccc; }}
    tr:hover td {{ background: rgba(255,255,255,.02); }}
    tr.removed td {{ opacity: .4; }}
    tr.hidden {{ display: none; }}
    .vendor {{ color: #4a9bb5; font-size: 12px; }}
    .os {{ color: #888; font-size: 11px; }}
    .latency {{ color: #c8a84b; font-size: 12px; font-family: monospace; }}
    .ports {{ font-family: monospace; font-size: 11px; color: #666; }}
    .status-up {{ color: #4a9bb5; }}
    .status-down {{ color: #555; }}
    .badge {{ display: inline-block; padding: 2px 8px; font-size: 9px; letter-spacing: .1em; text-transform: uppercase; margin-left: 8px; }}
    .badge.new {{ background: rgba(74,155,181,.15); color: #4a9bb5; border: 1px solid rgba(74,155,181,.3); }}
    .chart-wrap {{ margin: 40px 0; padding: 24px; background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.07); }}
    .chart-title {{ font-size: 9px; letter-spacing: .25em; color: #555; text-transform: uppercase; margin-bottom: 20px; }}
    canvas {{ width: 100% !important; height: 120px !important; }}
    footer {{ margin-top: 48px; font-size: 11px; color: #333; letter-spacing: .1em; }}
    span[title] {{ text-decoration: underline dotted rgba(255,255,255,.3); }}
    .tooltip-wrap {{ position: relative; display: inline-block; }}
    .tooltip-wrap .tooltip-text {{
    visibility: hidden; opacity: 0;
    background: #1a1a1a; color: #aaa;
    font-size: 11px; white-space: nowrap;
    padding: 6px 10px;
    border: 1px solid rgba(255,255,255,.1);
    position: absolute; top: 50%; left: 130%;
    transform: translateY(-50%);
    transition: opacity .2s;
    pointer-events: none;
    z-index: 99;
    }}
    .counters {{ display: flex; gap: 24px; margin-top: 12px; }}
    .count-online  {{ font-size: 12px; letter-spacing: .15em; color: #4a9bb5; }}
    .count-offline {{ font-size: 12px; letter-spacing: .15em; color: #555; }}
    .mac {{ font-family: monospace; font-size: 11px; color: #666; }}
    .lat-text {{ font-family: monospace; font-size: 12px; color: #c8a84b; }}
    .lat-bar {{ margin-top: 4px; height: 2px; background: rgba(255,255,255,.05); width: 80px; }}
    .lat-fill {{ height: 100%; transition: width .3s; }}
    th[data-col] {{ cursor: pointer; user-select: none; }}
    th[data-col]:hover {{ color: #aaa; }}
    th[data-col].asc::after  {{ content: " ↑"; }}
    th[data-col].desc::after {{ content: " ↓"; }}
    .tooltip-wrap:hover .tooltip-text {{ visibility: visible; opacity: 1; }}
  </style>
</head>
<body>
  <header>
    <p class="logo">Redevis · Network Scanner</p>
    <h1>REDE <span>SCAN</span></h1>
    <div class="counters">
      <span class="count-online">● {total_online} online</span>
      <span class="count-offline">● {total_offline} offline</span>
    </div>
  </header>

  {diff_section}

  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
    <div class="search-wrap" style="flex:1; margin:0; margin-right:16px;">
      <input type="text" id="search" placeholder="Buscar por IP, hostname ou fabricante...">
    </div>
    <button id="export-csv" style="padding:12px 20px; background:transparent; border:1px solid rgba(255,255,255,.1); color:#aaa; font-size:11px; letter-spacing:.15em; cursor:pointer; text-transform:uppercase; white-space:nowrap;">
      ↓ Exportar CSV
    </button>
  </div>

  <table id="devices-table">
    <thead>
      <tr>
        <th data-col="0">IP</th>
        <th data-col="1">Hostname</th>
        <th data-col="2">MAC</th>
        <th data-col="3">Fabricante</th>
        <th data-col="4">Sistema</th>
        <th data-col="5">Latência</th>
        <th data-col="6">Portas</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody id="devices-body">
      {rows}
      {removed_rows}
    </tbody>
  </table>

  <div class="chart-wrap">
    <p class="chart-title">Histórico — dispositivos online</p>
    <canvas id="chart"></canvas>
  </div>

  <footer>Gerado por Redevis · {scan["timestamp"]}</footer>

  <script>
    // ── Busca ──────────────────────────────────────────
    document.getElementById('search').addEventListener('input', function() {{
      const q = this.value.toLowerCase();
      document.querySelectorAll('#devices-body tr').forEach(row => {{
        row.classList.toggle('hidden', !row.textContent.toLowerCase().includes(q));
      }});
    }});

    // ── Ordenação por coluna ───────────────────────────
    let sortDir = {{}};
    document.querySelectorAll('th[data-col]').forEach(th => {{
      th.addEventListener('click', () => {{
        const col = parseInt(th.getAttribute('data-col'));
        const asc = !sortDir[col];
        sortDir = {{}};
        sortDir[col] = asc;

        document.querySelectorAll('th[data-col]').forEach(t => t.classList.remove('asc','desc'));
        th.classList.add(asc ? 'asc' : 'desc');

        const tbody = document.getElementById('devices-body');
        const rows  = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a, b) => {{
          const aText = a.cells[col]?.textContent.trim() || '';
          const bText = b.cells[col]?.textContent.trim() || '';
          return asc ? aText.localeCompare(bText) : bText.localeCompare(aText);
        }});
        rows.forEach(r => tbody.appendChild(r));
      }});
    }});

    // ── Exportar CSV ───────────────────────────────────
    document.getElementById('export-csv').addEventListener('click', () => {{
      const headers = ['IP','Hostname','MAC','Fabricante','Sistema','Latência','Portas','Status'];
      const rows = Array.from(document.querySelectorAll('#devices-body tr')).map(row => {{
        return Array.from(row.cells).map(td => `"${{td.textContent.trim().replace(/"/g,'""')}}"`);
      }});
      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const blob = new Blob([csv], {{type: 'text/csv'}});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'redevis-export.csv';
      a.click();
    }});

    // ── Gráfico ────────────────────────────────────────
    const labels = {chart_labels};
    const values = {chart_values};
    const canvas  = document.getElementById('chart');
    const ctx     = canvas.getContext('2d');
    canvas.width  = canvas.offsetWidth;
    canvas.height = 120;
    const w = canvas.width;
    const h = canvas.height;
    const pad = 20;
    const maxV = Math.max(...values, 1);
    ctx.strokeStyle = 'rgba(255,255,255,.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {{
      const y = pad + (h - pad * 2) * (1 - i / 4);
      ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke();
    }}
    if (values.length > 1) {{
      const stepX = (w - pad * 2) / (values.length - 1);
      ctx.beginPath();
      ctx.strokeStyle = '#4a9bb5';
      ctx.lineWidth = 2;
      values.forEach((v, i) => {{
        const x = pad + i * stepX;
        const y = pad + (h - pad * 2) * (1 - v / maxV);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }});
      ctx.stroke();
      values.forEach((v, i) => {{
        const x = pad + i * stepX;
        const y = pad + (h - pad * 2) * (1 - v / maxV);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#c8a84b';
        ctx.fill();
        ctx.fillStyle = '#888';
        ctx.font = '10px monospace';
        ctx.fillText(v, x - 4, y - 10);
      }});
    }}
  </script>
</body>
</html>"""

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


def open_report(filepath: str) -> None:
    import webbrowser
    webbrowser.open(f"file://{filepath}")