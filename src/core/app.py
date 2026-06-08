import os
import time
import threading
from flask import Flask, render_template, jsonify, request

# Importación corregida según tu estructura de carpetas
from src.core.models import get_db_connection, init_db

# Ajuste dinámico de paths: sube un nivel desde 'core' para encontrar 'templates'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'templates'))

app = Flask(__name__, template_folder=TEMPLATE_DIR)

metrics = {
    "backup_status": "IDLE",
    "active_connections": 0,
    "successful_writes": 0,
    "failed_writes": 0,
    "avg_latency_ms": 12.0
}
lock = threading.Lock()
stop_traffic = threading.Event()

def simulate_background_traffic():
    while not stop_traffic.is_set():
        start_time = time.time()
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SET statement_timeout = 2000;")
            
            with lock:
                metrics["active_connections"] += 1
                
            cur.execute("INSERT INTO transacciones (monto, estado) VALUES (random() * 500, 'PENDIENTE');")
            cur.execute("UPDATE transacciones SET estado = 'PROCESADO' WHERE estado = 'PENDIENTE';")
            conn.commit()
            
            latency = (time.time() - start_time) * 1000
            with lock:
                metrics["successful_writes"] += 1
                metrics["avg_latency_ms"] = (metrics["avg_latency_ms"] * 0.95) + (latency * 0.05)
                
            cur.close()
            conn.close()
        except Exception:
            with lock:
                metrics["failed_writes"] += 1
        finally:
            with lock:
                if metrics["active_connections"] > 0:
                    metrics["active_connections"] -= 1
        time.sleep(0.05)

@app.route('/')
def index():
    # Cambiado a 'base.html' para coincidir con tu archivo de la imagen
    return render_template('base.html')

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify(metrics)

@app.route('/api/action', methods=['POST'])
def trigger_action():
    action = request.json.get("action")
    if action == "VSS":
        threading.Thread(target=run_vss_lock).start()
    elif action == "SNAPSHOT":
        threading.Thread(target=run_snapshot).start()
    elif action == "RESET":
        with lock:
            metrics["successful_writes"] = 0
            metrics["failed_writes"] = 0
            metrics["avg_latency_ms"] = 12.0
    return jsonify({"status": "initiated"})

def run_vss_lock():
    global metrics
    with lock:
        metrics["backup_status"] = "🛑 VSS FREEZE (I/O bloqueado en Base de Datos)"
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("BEGIN;")
        cur.execute("LOCK TABLE transacciones IN ACCESS EXCLUSIVE MODE;")
        time.sleep(6)
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass
    with lock:
        metrics["backup_status"] = "IDLE"

def run_snapshot():
    global metrics
    with lock:
        metrics["backup_status"] = "⚡ SNAPSHOT DE INFRAESTRUCTURA (Cisco EVPN-VXLAN sin bloqueos)"
    time.sleep(1.0)
    with lock:
        metrics["backup_status"] = "IDLE"

try:
    init_db()
except Exception as e:
    print(f"Advertencia en inicialización DDL de BD: {e}")

threading.Thread(target=simulate_background_traffic, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
