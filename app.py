from flask import Flask, render_template_string, request, jsonify
import os
import time
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from instagrapi import Client

app = Flask(__name__)

IST = ZoneInfo("Asia/Kolkata")

# HTML Template with Delay Field
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
            --neon: #ff0033; --text: #e6e6e6;
            --ok: #00e676; --err: #ff5252; --info: #00e5ff;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0; color: var(--text); font-family: 'Orbitron', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--bg1), var(--bg2), var(--bg3));
            min-height: 100vh; padding: 24px;
            display: flex; flex-direction: column; gap: 22px; align-items: center;
        }
        .title { font-size: clamp(28px, 4vw, 56px); text-shadow: 0 0 18px var(--neon); color: #fff; margin: 0; }
        .card {
            background: rgba(0, 0, 0, .55); border: 1px solid rgba(255, 64, 96, .35);
            box-shadow: 0 0 24px rgba(255, 0, 51, .25); border-radius: 18px; padding: 16px;
            width: min(600px, 95vw);
        }
        .field { display: flex; flex-direction: column; gap: 8px; margin: 10px 0; }
        .inp, .file { width: 100%; padding: 12px; border: none; border-radius: 12px; background: #0f0f14; color: #fff; outline: none; }
        .btn {
            width: 100%; margin-top: 8px; padding: 12px; border: none; border-radius: 12px;
            font-weight: 800; cursor: pointer; background: linear-gradient(90deg, #b30024, #ff0033); color: #fff;
        }
        .console { height: 250px; overflow-y: auto; padding: 12px; border-radius: 12px; background: #000; color: #9aff9a; font-family: monospace; }
        .log-line { white-space: pre-wrap; font-size: 12px; }
    </style>
</head>
<body>
    <div class="title">DEVI ONFIRE</div>
    <div class="card">
        <h3>Instagram DM Automation</h3>
        <form id="mainForm">
            <div class="field">
                <span>Session IDs (Cookies) - One per line</span>
                <textarea class="inp" name="tokens" rows="3" placeholder="Paste session IDs here..." required></textarea>
            </div>
            <div class="field">
                <span>Messages - One per line</span>
                <textarea class="inp" name="messages" rows="3" placeholder="Paste messages here..." required></textarea>
            </div>
            <div class="field">
                <span>Target Thread / Username</span>
                <input class="inp" type="text" name="thread_id" placeholder="Enter ID or Username (e.g. devi_onfiire)" required />
            </div>
            <div class="field">
                <span>Hater Name / Prefix</span>
                <input class="inp" type="text" name="prefix" placeholder="Enter prefix" required />
            </div>
            <div class="field">
                <span>Delay Between Messages (Seconds)</span>
                <input class="inp" type="number" name="delay" value="3" min="1" max="15" required />
            </div>
            <button class="btn" type="submit">SEND MESSAGES</button>
        </form>
        <h3 style="margin-top:15px;">Logs</h3>
        <div id="console" class="console"></div>
    </div>

    <script>
        document.getElementById("mainForm").onsubmit = async (e) => {
            e.preventDefault();
            const consoleDiv = document.getElementById("console");
            consoleDiv.innerHTML = '<div class="log-line">Sending messages... Please wait...</div>';
            
            const formData = new FormData(e.target);
            const res = await fetch("/", { method: "POST", body: formData });
            const data = await res.json();
            
            if(data.logs) {
                consoleDiv.innerHTML = data.logs.map(l => `<div class="log-line">${l}</div>`).join("");
            } else {
                consoleDiv.innerHTML = `<div class="log-line">Error occurred!</div>`;
            }
        };
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        tokens_raw = request.form.get("tokens", "")
        messages_raw = request.form.get("messages", "")
        thread_id = request.form.get("thread_id", "").strip()
        prefix = request.form.get("prefix", "").strip()
        
        try:
            delay = int(request.form.get("delay", 3))
        except ValueError:
            delay = 3

        tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]
        messages = [m.strip() for m in messages_raw.splitlines() if m.strip()]

        if not tokens or not messages:
            return jsonify({"logs": ["❌ Error: Tokens or Messages are empty!"]})

        logs = []
        emojis = [" 3:)", " :)", " :3", " ^_^", " :D", " ;)", " :P"]

        # Target ID lookup
        target_user_id = None
        try:
            temp_cl = Client()
            temp_cl.login_by_sessionid(tokens[0].strip())
            if thread_id.isdigit():
                target_user_id = int(thread_id)
            else:
                target_user_id = temp_cl.user_id_from_username(thread_id)
        except Exception as e:
            return jsonify({"logs": [f"❌ Target Lookup Error: {str(e)[:80]}"]} )

        # Vercel time limit ki wajah se max 4 messages per request batch
        for i, msg in enumerate(messages[:4]):  
            session_id = tokens[i % len(tokens)]
            composed = f"{prefix} {msg} {random.choice(emojis)}"
            now_ist = datetime.now(IST).strftime("%H:%M:%S")

            try:
                cl = Client()
                cl.login_by_sessionid(session_id.strip())
                
                try:
                    cl.direct_send(composed, thread_ids=[target_user_id])
                except Exception:
                    cl.direct_send(composed, user_ids=[target_user_id])

                logs.append(f"[{now_ist}] ✅ Sent: {composed}")
            except Exception as e:
                logs.append(f"[{now_ist}] ❌ Failed: {str(e)[:80]}")

            # User ka diya hua delay yahan apply hoga
            if i < len(messages[:4]) - 1:
                time.sleep(delay)

        return jsonify({"logs": logs})

    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
