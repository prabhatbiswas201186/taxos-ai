from pathlib import Path

path = Path(r'C:/Users/prabh/taxos-ai/index.html')
text = path.read_text(encoding='utf-8', errors='ignore')

lead = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>TAXOS AI — Intelligent Finance Platform</title>
<script src="https://cdn.tailwindcss.com"><\/script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"><\/script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root{--bg:#09090b;--surface:#111114;--border:#232329;--primary:#5e6ad2;--text:#ededed;--muted:#888892}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{background:var(--bg);color:var(--text);font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow:hidden}
input,select,textarea,button{font-family:inherit}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-thumb{background:#22222a;border-radius:4px}
#app-shell{display:flex;flex-direction:column;height:100%}
.sidebar{width:256px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;padding:14px 10px;transition:width .22s}
.sidebar.collapsed{width:64px}
.sidebar .logo{display:flex;align-items:center;gap:10px;padding:6px 10px;margin-bottom:10px;font-weight:700;font-size:16px;white-space:nowrap;overflow:hidden}
.sidebar nav{flex:1;overflow-y:auto;overflow-x:hidden}
.sidebar section{margin-bottom:8px}
.sidebar .section-title{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;padding:8px 10px 4px;user-select:none}
.sidebar nav a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:6px;color:var(--muted);text-decoration:none;font-size:13px;font-weight:500;transition:all .12s;white-space:nowrap}
.sidebar nav a:hover{background:#16161b;color:var(--text)}
.sidebar nav a.active{background:#18181f;color:var(--text)}
.sidebar nav a .icon{font-size:16px;width:20px;text-align:center}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.topbar{height:52px;border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 18px;gap:10px;background:rgba(9,9,11,.65);backdrop-filter:blur(10px)}
.topbar input.search{background:#14141a;border:1px solid var(--border);border-radius:6px;padding:6px 10px;color:var(--text);font-size:13px;width:280px;outline:none}
.topbar input.search:focus{border-color:var(--primary)}
.content{flex:1;overflow-y:auto;padding:22px 22px 40px}
.card{background:#111114;border:1px solid var(--border);border-radius:10px;padding:18px}
.kpi-grid{display:grid;gap:14px}
.kpi{background:#0e0e12;border:1px solid var(--border);border-radius:10px;padding:14px;min-width:0}
.kpi .label{font-size:11px;color:var(--muted);text-transform:uppercase;font-weight:700;letter-spacing:.06em}
.kpi .value{font-size:22px;font-weight:700;margin-top:6px;font-variant-numeric:tabular-nums}
.kpi .change{font-size:11px;margin-top:6px;font-weight:600;color:var(--muted)}
.btn{background:var(--primary);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-weight:600;font-size:13px;cursor:pointer}
.btn-secondary{background:#1a1a21;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px 14px;font-weight:600;font-size:13px;cursor:pointer}
.btn-ghost{background:transparent;color:var(--muted);border:1px solid transparent;border-radius:6px;padding:8px 14px;font-size:13px;cursor:pointer}
.btn-ghost:hover{background:#16161b;color:var(--text)}
table{width:100%;border-collapse:collapse;font-size:13px}
table th{text-align:left;padding:10px 12px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--border);font-weight:600}
table td{padding:10px 12px;border-bottom:1px solid #16161d}
.badge{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.02em}
.badge-green{background:rgba(74,222,128,.12);color:#4ade80}
.badge-yellow{background:rgba(250,204,21,.12);color:#facc15}
.badge-red{background:rgba(248,113,113,.12);color:#f87171}
.badge-muted{background:#26272e;color:var(--muted)}
.skeleton{background:#0e0e12;border-radius:6px;animation:pulse 1.2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.45}50%{opacity:.85}}
</style>
</head>
<body>
<div id="app-shell"></div>
'''

# Remove leading noise that got injected and then collapse to the original script section.
idx = text.find('const ROUTES')
if idx == -1:
    raise SystemExit('Could not find original script start')
body_text = text[idx:]
path.write_text(lead + body_text, encoding='utf-8')
