import time
import random
from src.apps.writer.app import VSSWriter
from src.apps.provider.app import VSSProvider
from src.core.models import get_db_connection

class VSSCoordinatorService:
    def __init__(self):
        self.writer = VSSWriter()
        self.provider = VSSProvider()
        self.status = "IDLE"
        self.cpu_usage = 0.5
        self.message = "VSS Service (vssvc.exe) en modo de espera (Dormido)."

    def get_telemetry(self):
        if self.status == "IDLE":
            self.cpu_usage = random.uniform(0.1, 1.2)
        elif self.status == "FREEZE":
            self.cpu_usage = random.uniform(45.0, 55.0)
        elif self.status == "SNAPSHOT":
            self.cpu_usage = random.uniform(85.0, 98.0)
        elif self.status == "THAW":
            self.cpu_usage = random.uniform(20.0, 30.0)
        return {"cpu": round(self.cpu_usage, 2), "status": self.status, "message": self.message}

    def CVssCoordinator_StartSnapshotSet(self, id_dato_objetivo, cache_global):
        # MOMENTO 1: FREEZE (1 segundo de bloqueo para evidenciarlo rápido)
        self.status = "FREEZE"
        self.message = self.writer.freeze()
        time.sleep(1.0)
        
        # MOMENTO 2: SNAPSHOT (Procesamiento inmediato)
        self.status = "SNAPSHOT"
        self.message = "⚡ vssvc.exe invoca las estructuras del Kernel para la captura de bloques."
        
        contenido_actual = "Data Cruda"
        for d in cache_global["datos"]:
            if d["id_dato"] == id_dato_objetivo:
                contenido_actual = d["contenido_bloque"]
                break
        
        snap_data = self.provider.create_shadow_copy_set(id_dato_objetivo, contenido_actual)
        
        # Insertar en la lista de RAM asignando un ID secuencial temporal a prueba de fallas
        nuevo_id = len(cache_global["snapshots"]) + 1
        nuevo_snap = {
            "id_snapshot": nuevo_id,
            "id_dato": snap_data["id_dato"],
            "vss_provider_usado": snap_data["vss_provider"],
            "contenido_congelado": snap_data["contenido_congelado"],
            "fecha_captura": time.strftime("%H:%M:%S")
        }
        cache_global["snapshots"].append(nuevo_snap)
        
        # Guardar en la base de datos real PostgreSQL en un hilo aislado de fondo (No bloquea la interfaz)
        def guardar_en_disco_silenciosamente():
            conn = None
            try:
                conn = get_db_connection()
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO tabla_snapshots (id_dato, vss_provider_usado, contenido_congelado, fecha_captura) 
                    VALUES (%s, %s, %s, CURRENT_TIME);
                """, (snap_data["id_dato"], snap_data["vss_provider"], snap_data["contenido_congelado"]))
                cur.close()
            except Exception:
                pass
            finally:
                if conn: conn.close()
                
        import threading
        threading.Thread(target=guardar_en_disco_silenciosamente, daemon=True).start()
            
        time.sleep(1.0)
        
        # MOMENTO 3: THAW (Descongelamiento instantáneo)
        self.status = "THAW"
        self.message = self.writer.thaw()
        time.sleep(0.6)
        
        self.status = "IDLE"
        self.message = "VSS Service (vssvc.exe) volvió a modo de suspensión (Dormido)."


