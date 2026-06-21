import pathlib

p = pathlib.Path(r'C:/Users/prabh/taxos-ai/index.html')

lead = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>TAXOS AI — Intelligent Finance Platform</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root{--bg:#09090b;--surface:#111114;--border:#232329;--primary:#5e6ad2;--text:#ededed;--muted:#888892}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{background:var(--bg);color:var(--text);font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow:hidden}
input,select,textarea,button{font-family:inherit}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-thumb{background:#22222a;border-radius:4px}
#app{display:flex;flex-direction:column;height:100%;position:relative}
.sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;padding:14px 10px;transition:width .22s ease}
.sidebar.collapsed{width:64px}
.sidebar .logo{display:flex;align-items:center;gap:10px;padding:6px 10px;margin-bottom:10px;font-weight:700;font-size:16px;white-space:nowrap;overflow:hidden}
.sidebar nav{flex:1;overflow-y:auto;overflow-x:hidden}
.sidebar nav section{margin-bottom:6px}
.sidebar .section-title{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;padding:10px 10px 4px;user-select:none}
.sidebar .nav-link{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:6px;color:var(--muted);text-decoration:none;font-size:13px;font-weight:500;transition:all .12s;white-space:nowrap}
.sidebar .nav-link:hover{background:#16161b;color:var(--text)}
.sidebar .nav-link.active{background:#18181f;color:var(--text)}
.sidebar .nav-link .icon{font-size:16px;width:22px;text-align:center;flex-shrink:0}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.topbar{height:52px;border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 18px;gap:10px;background:rgba(9,9,11,.65);backdrop-filter:blur(10px)}
.topbar input.search{background:#14141a;border:1px solid var(--border);border-radius:6px;padding:6px 10px;color:var(--text);font-size:13px;width:280px;outline:none}
.topbar input.search:focus{border-color:var(--primary)}
.page{flex:1;overflow-y:auto;padding:22px 24px 36px}

.auth-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px;background:radial-gradient(circle at top,#15151b,#09090b 55%)}
.auth-card{background:#111114;border:1px solid var(--border);border-radius:14px;padding:28px;width:min(420px,100%)}
.auth-card h1{font-size:19px;font-weight:700;margin-bottom:4px}
.auth-card p{color:var(--muted);font-size:12px;margin-bottom:18px}
.form-group{margin-bottom:14px}
.form-label{font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;display:block}
.form-input{width:100%;background:#0c0c10;border:1px solid var(--border);border-radius:6px;padding:9px 10px;color:var(--text);font-size:13px;outline:none}
.form-input:focus{border-color:var(--primary)}
select.form-input{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);background-position:calc(100% - 18px) 50%,calc(100% - 12px) 50%;background-size:6px 6px;background-repeat:no-repeat}
.btn-primary{width:100%;background:var(--primary);color:#fff;border:0;border-radius:6px;padding:10px;font-weight:700;font-size:13px;cursor:pointer;transition:filter .1s}
.btn-primary:hover{filter:brightness(1.08)}
.btn{background:var(--primary);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-weight:600;font-size:13px;cursor:pointer}
.btn-secondary{background:#1a1a21;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px 14px;font-weight:600;font-size:13px;cursor:pointer}
.btn-ghost{background:transparent;color:var(--muted);border:1px solid transparent;border-radius:6px;padding:8px 14px;font-size:13px;cursor:pointer}
.btn-ghost:hover{background:#16161b;color:var(--text)}

.card{background:#111114;border:1px solid var(--border);border-radius:10px;padding:18px}
.kpi-grid{display:grid;gap:14px}
.kpi{background:#0e0e12;border:1px solid var(--border);border-radius:10px;padding:14px;min-width:0}
.kpi .label{font-size:11px;color:var(--muted);text-transform:uppercase;font-weight:700;letter-spacing:.06em}
.kpi .value{font-size:22px;font-weight:700;margin-top:6px;font-variant-numeric:tabular-nums}
.kpi .change{font-size:11px;margin-top:6px;font-weight:600;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}
table th{text-align:left;padding:10px 12px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--border);font-weight:600}
table td{padding:10px 12px;border-bottom:1px solid #16161d}
.badge{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.02em}
.badge-green{background:rgba(74,222,128,.12);color:#4ade80}
.badge-yellow{background:rgba(250,204,21,.12);color:#facc15}
.badge-red{background:rgba(248,113,113,.12);color:#f87171}
.badge-muted{background:#26272e;color:var(--muted)}
.toast-bar{position:fixed;bottom:18px;right:18px;z-index:100;display:flex;flex-direction:column;gap:8px}
.toast{background:#16161d;border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;font-size:13px;box-shadow:0 10px 30px rgba(0,0,0,.35);animation:in .18s ease}
@keyframes in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:50;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .12s}
.modal-backdrop.open{opacity:1;pointer-events:auto}
.modal{background:#111114;border:1px solid var(--border);border-radius:12px;width:min(440px,92vw);max-height:80vh;overflow-y:auto;padding:20px}
.skeleton{background:#0e0e12;border-radius:6px;animation:pulse 1.2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.45}50%{opacity:.85}}
.cmdk{position:fixed;inset:0;z-index:60;background:rgba(0,0,0,.55);display:flex;align-items:flex-start;justify-content:center;padding-top:14vh;opacity:0;pointer-events:none;transition:opacity .1s}
.cmdk.open{opacity:1;pointer-events:auto}
.cmdk .panel{background:#13131a;border:1px solid var(--border);border-radius:10px;width:min(560px,92vw);max-height:420px;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,.45)}
.cmdk .row{display:flex;align-items:center;gap:10px;padding:10px 12px;cursor:pointer;font-size:13px}
.cmdk .row:hover,.cmdk .row.sel{background:#1c1c24}
.cmdk .row .icon{width:20px;text-align:center}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 0;color:var(--muted);gap:6px}
.empty h3{color:var(--text);font-weight:600;font-size:14px}
</style>
</head>
<body>
<div id="app"></div>
'''

p.write_text(lead, encoding='utf-8')
