from anomaly import detector
from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import threading, time, os

from database import init_db, save_stats, get_history
from capture import start_capture
from processor import get_stats

app = Flask(__name__, static_folder="../frontend")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

init_db()

@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("../frontend", path)

@app.route("/api/history")
def history():
    minutes = int(request.args.get("minutes", 60))
    rows = get_history(minutes)
    data = [{
        "timestamp": r[0], "mbps": r[1], "pps": r[2],
        "active_hosts": r[3], "tcp": r[4], "udp": r[5],
        "icmp": r[6], "other": r[7]
    } for r in rows]
    return jsonify({"history": data})

def broadcast_loop():
    while True:
        stats = get_stats(window_seconds=2)
        save_stats(stats)
        detector.add(stats["mbps"], stats["pps"])
        ml_alerts = detector.check(stats["mbps"], stats["pps"])
        stats["ml_alerts"] = ml_alerts
        socketio.emit("traffic_update", stats)
        time.sleep(1)

if __name__ == "__main__":
    start_capture(interface="Wi-Fi")
    t = threading.Thread(target=broadcast_loop, daemon=True)
    t.start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)