import os
import threading
import time
from flask import Flask, render_template, jsonify, request
from src.apps.core_service.app import VSSCoordinatorService
from src.core.models import get_db_connection, init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'templates'))

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Inicializar Base de Datos de forma limpia al arrancar
init_db()

# ESTRUCTURA DE ALTA VELOCIDAD EN MEMORIA RAM
infra_ram_cache = {
    "volumenes": [],
    "datos": [],
    "snapshots": []
}

def cargar_cache_inicial():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id_volumen, letra_unidad, sistema_archivos, capacidad_total_gb, health FROM tabla_volumenes ORDER BY id_volumen;")
    infra_ram_cache["volumenes"] = [{"id_volumen": r[0], "letra_unidad": r[1], "sistema_archivos": r[2], "capacidad_total_gb": r[3], "health": r[4]} for r in cur.fetchall()]
    
    cur.execute("SELECT id_dato, id_volumen, ruta_archivo, contenido_bloque, CAST(ultima_modificacion AS VARCHAR) FROM tabla_datos ORDER BY id_dato;")
    infra_ram_cache["datos"] = [{"id_dato": r[0], "id_volumen": r[1], "ruta_archivo": r[2], "contenido_bloque": r[3], "ultima_modificacion": r[4]} for r in cur.fetchall()]
    
    cur.execute("SELECT id_snapshot, id_dato, vss_provider_usado, contenido_congelado, CAST(fecha_captura AS VARCHAR) FROM tabla_snapshots ORDER BY id_snapshot;")
    infra_ram_cache["snapshots"] = [{"id_snapshot": r[0], "id_dato": r[1], "vss_provider_usado": r[2], "contenido_congelado": r[3], "fecha_captura": r[4]} for r in cur.fetchall()]
    
    cur.close()
    conn.close()

cargar_cache_inicial()
vss_kernel_service = VSSCoordinatorService()

# Envoltura segura para evitar pasar argumentos por hilos secundarios
def vss_worker_bridge(id_dato):
    vss_kernel_service.CVssCoordinator_StartSnapshotSet(id_dato, infra_ram_cache)

def app_writer_traffic():
    while True:
        if not vss_kernel_service.writer.is_frozen:
            now_time = time.strftime("%H:%M:%S")
            for d in infra_ram_cache["datos"]:
                if d["id_dato"] == 101:
                    d["ultima_modificacion"] = now_time
                    break
        time.sleep(0.5)

threading.Thread(target=app_writer_traffic, daemon=True).start()

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/api/get_vss_telemetry', methods=['GET'])
def get_vss_telemetry():
    return jsonify({
        "volumenes": infra_ram_cache["volumenes"],
        "datos": infra_ram_cache["datos"],
        "snapshots": infra_ram_cache["snapshots"],
        "telemetry": vss_kernel_service.get_telemetry()
    })

@app.route('/api/com_trigger_snapshot', methods=['POST'])
def com_trigger_snapshot():
    if vss_kernel_service.status != "IDLE":
        return jsonify({"status": "VSS_ERR_SNAPSHOT_SET_IN_PROGRESS"}), 400
    
    id_dato = request.json.get("id_dato", 101)
    
    # SOLUCIÓN DEFINITIVA: Llama a la envoltura sin pasar parámetros conflictivos
    threading.Thread(target=vss_worker_bridge, args=(id_dato,)).start()
    return jsonify({"status": "VSS_S_ASYNC_PENDING"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
