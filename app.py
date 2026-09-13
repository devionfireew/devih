from flask import Flask, render_template_string, request, jsonify
import threading
import os
import time
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from instagrapi import Client

app = Flask(__name__)

# Global storage for tasks and logs
tasks = {}
task_id_counter = 1
IST = ZoneInfo("Asia/Kolkata")

# HTML Frontend Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devi OnFire - Instagram DM Bot</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&display=swap');

        :root {
            --bg1: #0b0b0f; --bg2: #180008; --bg3: #2b0008; 
            --glow: #ff2b4a; --neon: #ff0033; --text: #e6e6e6;
            --ok: #00e676; --warn: #ffea00; --err: #ff5252; --info: #00e5ff;
        }
        
        * { box-sizing: border-box; }
        
        body {
            margin: 0; color: var(--text); font-family: 'Orbitron', system-ui, sans-serif;
            background: radial-gradient(1200px 600px at 20% 10%, #21000a 0%, transparent 60%),
                        radial-gradient(900px 500px at 80% 30%, #12000a 0%, transparent 60%),
                        linear-gradient(135deg, var(--bg1), var(--bg2), var(--bg3));
            min-height: 100vh; padding: 24px;
            display: flex; flex-direction: column; gap: 22px; align-items: center;
        }

        .title {
            font-size: clamp(28px, 4vw, 56px);
            letter-spacing: 2px;
            text-shadow: 0 0 18px var(--neon), 0 0 36px #ff5577;
            color: #fff; margin: 4px 0 0;
        }
        
        .subtitle {
            margin: -6px 0 12px; opacity: .9; font-size: clamp(12px, 2vw, 14px);
        }

        .board {
            width: min(1200px, 95vw);
            display: grid; grid-template-columns: 1.1fr .9fr; gap: 18px;
        }
        
        @media (max-width: 980px) { .board { grid-template-columns: 1fr; } }

        .card {
            background: rgba(0, 0, 0, .55);
            border: 1px solid rgba(255, 64, 96, .35);
            box-shadow: 0 0 24px rgba(255, 0, 51, .25);
            border-radius: 18px; padding: 16px;
            backdrop-filter: blur(6px);
        }
        
        .card h3 {
            margin: 0 0 14px; font-size: 18px; letter-spacing: 1px;
            color: #fff; text-shadow: 0 0 10px var(--neon);
        }

        .field {
            display: flex; flex-direction: column; gap: 8px; margin: 10px 0;
        }
        
        .label {
            font-size: 12px; opacity: .85;
        }
        
        .inp {
            width: 100%; padding: 12px 14px; border: none; border-radius: 12px;
            background: #0f0f14; color: #e9f9ff; outline: none; font-size: 14px;
            box-shadow: inset 0 0 0 2px #222;
        }
        
        .file {
            padding: 12px; border-radius: 12px; background: #0f0f14; color: #bbb;
            box-shadow: inset 0 0 0 2px #222;
        }

        .btn {
            width: 100%; margin-top: 8px; padding: 12px 14px; border: none; border-radius: 12px;
            font-weight: 800; letter-spacing: .5px; cursor: pointer;
            background: linear-gradient(90deg, #b30024, #ff0033, #b30024);
            color: #fff; box-shadow: 0 8px 24px rgba(255, 0, 51, .35);
        }

        .btn-stop {
            background: linear-gradient(90deg, #2c0a0a, #b40000, #2c0a0a);
        }

        .console {
            height: 420px; overflow-y: auto; padding: 12px; border-radius: 12px;
            background: #000; color: #9aff9a; font-family: monospace;
            box-shadow: inset 0 0 0 2px #0d2410;
            line-height: 1.35;
        }
        
        .log-line { white-space: pre-wrap; }
        .ok { color: var(--ok); }
        .err { color: var(--err); }
        .info { color: var(--info); }
        .warn { color: var(--warn); }

        .stats {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;
        }
        
        .tile {
            padding: 12px; background: #101015; border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, .06);
            display: flex; flex-direction: column; gap: 4px;
        }
        
        .kv { font-size: 12px; opacity: .75; }
        .vv { font-size: 16px; font-weight: 800; }
        .footer { opacity: .75; font-size: 12px; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="title">DEVI ONFIRE</div>
    <div class="subtitle">Instagram Inbox DM Automation System</div>

    <div class="board">
        <div class="card">
            <h3>Start New Instagram Task</h3>
            <form id="mainForm" method="POST" enctype="multipart/form-data">
                <div class="field">
                    <div class="label"><span>Instagram Session IDs / Cookies File (.txt)</span></div>
                    <input class="file inp" type="file" name="token_file" required />
                </div>

                <div class="field">
                    <div class="label"><span>Message File (.txt)</span></div>
                    <input class="file inp" type="file" name="message_file" required />
                </div>

                <div class="field">
                    <div class="label"><span>Instagram Target Thread ID or User ID</span></div>
                    <input class="inp" type="text" name="thread_id" placeholder="Enter Thread ID / User ID" required />
                </div>

                <div class="field">
                    <div class="label"><span>Hater Name / Prefix</span></div>
                    <input class="inp" type="text" name="prefix" placeholder="Enter prefix" required />
                </div>

                <div class="field">
                    <div class="label"><span>Speed (Delay in seconds)</span></div>
                    <input class="inp" type="number" min="1" name="delay" placeholder="Enter delay" required />
                </div>

                <button class="btn" type="submit">START DM TASK</button>
            </form>

            <div style="margin-top:14px;">
                <button class="btn btn-stop" id="btnStop">STOP CURRENT TASK</button>
            </div>

            <div style="margin-top:14px">
                <h3>Live Logs</h3>
                <div id="console" class="console"></div>
            </div>
        </div>

        <div class="card">
            <h3>Task Stats</h3>
            <div class="stats">
                <div class="tile"><div class="kv">Task ID</div><div class="vv" id="st_task"></div></div>
                <div class="tile"><div class="kv">Target ID</div><div class="vv" id="st_thread"></div></div>
                <div class="tile"><div class="kv">Status</div><div class="vv" id="st_status"></div></div>
                <div class="tile"><div class="kv">Started Time</div><div class="vv" id="st_started"></div></div>
                <div class="tile"><div class="kv">Uptime</div><div class="vv" id="st_uptime"></div></div>
                <div class="tile"><div class="kv">Accounts Total</div><div class="vv" id="st_t_total"></div></div>
                <div class="tile"><div class="kv">Messages Sent</div><div class="vv" id="st_sent_ok"></div></div>
                <div class="tile"><div class="kv">Messages Failed</div><div class="vv" id="st_sent_fail"></div></div>
                <div class="tile"><div class="kv">Delay (sec)</div><div class="vv" id="st_delay"></div></div>
            </div>
        </div>
    </div>

    <div class="footer">Made By Devi OnFire</div>

    <script>
        const consoleDiv = document.getElementById("console");
        let currentTaskId = null;
        let pollTimerLogs = null;
        let pollTimerStats = null;

        function appendConsole(lines) {
            if (!lines || !lines.length) return;
            consoleDiv.innerHTML = lines.map(l => {
                let css = "log-line";
                if (l.includes("✅")) css += " ok";
                else if (l.includes("❌")) css += " err";
                else if (l.includes("⚠️")) css += " warn";
                else css += " info";
                return `<div class="${css}">${l}</div>`;
            }).join("");
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        }

        async function pollLogs() {
            if (!currentTaskId) return;
            try {
                const res = await fetch("/logs/" + currentTaskId);
                const data = await res.json();
                appendConsole(data.logs || []);
            } catch (e) {}
            pollTimerLogs = setTimeout(pollLogs, 1200);
        }

        async function pollStats() {
            if (!currentTaskId) return;
            try {
                const res = await fetch("/stats/" + currentTaskId);
                const s = await res.json();
                document.getElementById("st_task").textContent = s.task_id || "";
                document.getElementById("st_thread").textContent = s.thread_id || "";
                document.getElementById("st_status").textContent = s.running ? "RUNNING" : "STOPPED";
                document.getElementById("st_started").textContent = s.started_ist || "";
                document.getElementById("st_uptime").textContent = s.uptime || "";
                document.getElementById("st_t_total").textContent = s.tokens_total ?? "";
                document.getElementById("st_sent_ok").textContent = s.sent_ok ?? "";
                document.getElementById("st_sent_fail").textContent = s.sent_fail ?? "";
                document.getElementById("st_delay").textContent = s.delay ?? "";
            } catch (e) {}
            pollTimerStats = setTimeout(pollStats, 1500);
        }

        document.getElementById("mainForm").onsubmit = async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            const res = await fetch("/", { method: "POST", body: fd });
            const data = await res.json();
            currentTaskId = data.task_id;
            consoleDiv.innerHTML = `<div class="log-line info">Task Started (ID: ${currentTaskId})…</div>`;
            clearTimeout(pollTimerLogs);
            clearTimeout(pollTimerStats);
            pollLogs();
            pollStats();
        };

        document.getElementById("btnStop").onclick = async () => {
            if (!currentTaskId) return;
            await fetch("/stop/" + currentTaskId, { method: "POST" });
            consoleDiv.innerHTML += `<div class="log-line err">🛑 Stopped Task: ${currentTaskId}</div>`;
        };
    </script>
</body>
</html>
"""

def human_uptime(start_dt_ist: datetime) -> str:
    delta = datetime.now(IST) - start_dt_ist
    secs = int(delta.total_seconds())
    days, rem = divmod(secs, 86400)
    hrs, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hrs: parts.append(f"{hrs}h")
    if mins: parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)

# ================== INSTAGRAM SENDING LOOP ==================
def send_loop(task_id: str):
    t = tasks[task_id]
    session_ids = t["tokens"] # Ye cookies / session ids hain
    messages = t["messages"]
    target_id = t["thread_id"].strip()
    delay = t["delay"]
    prefix = t["prefix"]
    emojis = [" 3:)", " :)", " :3", " ^_^", " :D", " ;)", " :P"]
    msg_index = 0

    t["logs"].append(f"[{datetime.now(IST).strftime('%H:%M:%S')}] Instagram Inbox DM task started.")

    while t["running"]:
        for session_id in session_ids:
            if not t["running"]:
                break
            
            message_text = messages[msg_index % len(messages)]
            composed = f"{prefix} {message_text} {random.choice(emojis)}"
            now_ist = datetime.now(IST).strftime("%H:%M:%S")

            try:
                cl = Client()
                # Instagram session ID login via cookies
                cl.login_by_sessionid(session_id.strip())
                
                target_int = int(target_id)
                try:
                    # Pehle thread ID par bhejny ki koshish karega
                    cl.direct_send(composed, thread_ids=[target_int])
                except Exception:
                    # Agar thread ID fail ho toh user ID par bhej dega
                    cl.direct_send(composed, user_ids=[target_int])

                t["sent_ok"] += 1
                t["logs"].append(f"[{now_ist}] ✅ DM Sent: {composed}")
            except Exception as e:
                t["sent_fail"] += 1
                t["logs"].append(f"[{now_ist}] ❌ Error/Failed → {str(e)[:150]}")

            time.sleep(delay)
        msg_index += 1

    t["logs"].append(f"[{datetime.now(IST).strftime('%H:%M:%S')}] 🔴 Task stopped.")

# ================== FLASK ROUTES ==================
@app.route("/", methods=["GET", "POST"])
def home():
    global task_id_counter
    if request.method == "POST":
        token_file = request.files["token_file"]
        message_file = request.files["message_file"]
        thread_id = request.form["thread_id"].strip()
        prefix = request.form["prefix"].strip()
        delay = int(request.form["delay"])

        tokens = []
        for raw in token_file.stream.readlines():
            line = raw.decode("utf-8", errors="ignore").strip()
            if line:
                tokens.append(line)

        messages = []
        for raw in message_file.stream.readlines():
            line = raw.decode("utf-8", errors="ignore").strip()
            if line:
                messages.append(line)

        if not tokens or not messages:
            return jsonify({"error": "Empty tokens/messages"}), 400

        task_id = str(task_id_counter)
        task_id_counter += 1
        tasks[task_id] = {
            "running": True,
            "logs": [],
            "sent_ok": 0,
            "sent_fail": 0,
            "start_ts": datetime.now(IST),
            "thread_id": thread_id,
            "tokens": tokens,
            "messages": messages,
            "delay": delay,
            "prefix": prefix
        }

        th = threading.Thread(target=send_loop, args=(task_id,), daemon=True)
        th.start()
        return jsonify({"task_id": task_id})

    return render_template_string(HTML_TEMPLATE)

@app.route("/logs/<task_id>")
def logs(task_id):
    t = tasks.get(task_id)
    if not t:
        return jsonify({"logs": ["Invalid Task ID"]})
    last = t["logs"][-800:]
    return jsonify({"logs": last})

@app.route("/stats/<task_id>")
def stats(task_id):
    t = tasks.get(task_id)
    if not t:
        return jsonify({"error": "Invalid Task ID"}), 404
    tokens_total = len(t["tokens"])
    return jsonify({
        "task_id": task_id,
        "running": t["running"],
        "thread_id": t["thread_id"],
        "started_ist": t["start_ts"].strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": human_uptime(t["start_ts"]),
        "tokens_total": tokens_total,
        "sent_ok": t["sent_ok"],
        "sent_fail": t["sent_fail"],
        "delay": t["delay"]
    })

@app.route("/stop/<task_id>", methods=["POST"])
def stop(task_id):
    t = tasks.get(task_id)
    if not t:
        return "Invalid Task ID", 404
    t["running"] = False
    return "Stopped"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=21889)
