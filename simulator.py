import os
import time
import random
import sys

# Asegurar que Python encuentre el módulo src
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.core.models import get_db_connection

def ejecutar_simulacion():
    print("=== INICIANDO SIMULADOR DE ALTA TRANSACCIONALIDAD ===")
    ciclo = 1
    
    try:
        while True:
            conn = get_db_connection()
            conn.autocommit = True
            cur = conn.cursor()
            
            # 1. Simular ráfaga de nuevas transacciones entrantes
            nuevas_tx = random.randint(5, 20)
            for _ in range(nuevas_tx):
                monto = round(random.uniform(10.0, 1500.0), 2)
                estado = random.choice(['PROCESADO', 'PENDIENTE', 'RECHAZADO'])
                cur.execute(
                    "INSERT INTO transacciones (monto, estado) VALUES (%s, %s);",
                    (monto, estado)
                )
            
            # 2. Simular consulta masiva pesada para inducir congestión de lecturas
            cur.execute("SELECT COUNT(*), AVG(monto) FROM transacciones WHERE estado = 'PROCESADO';")
            total, promedio = cur.fetchone()
            
            print(f"[Ciclo {ciclo}] Inyectadas {nuevas_tx} transacciones. Total en BD: {total} | Monto Promedio: ${promedio:.2f}")
            
            cur.close()
            conn.close()
            
            # Pausa de 1 segundo entre ráfagas de transacciones
            time.sleep(1)
            ciclo += 1
            
    except KeyboardInterrupt:
        print("\n=== SIMULACIÓN FINALIZADA POR EL USUARIO ===")
    except Exception as e:
        print(f"\n[ERROR EN SIMULACIÓN]: {e}")

if __name__ == "__main__":
    ejecutar_simulacion()
