import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "vss_infra"),
        user=os.getenv("DB_USER", "javier"),
        password=os.getenv("DB_PASSWORD", "1234"),
        port=int(os.getenv("DB_PORT", 5432))
    )

def init_db():
    """Inicializa las 3 tablas hermanas del simulador VSS con datos de prueba idénticos a la maqueta."""
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    # Limpieza limpia de cascada
    cur.execute("DROP TABLE IF EXISTS tabla_snapshots CASCADE;")
    cur.execute("DROP TABLE IF EXISTS tabla_datos CASCADE;")
    cur.execute("DROP TABLE IF EXISTS tabla_volumenes CASCADE;")
    
    # 1. TABLA_VOLUMENES
    cur.execute("""
        CREATE TABLE tabla_volumenes (
            id_volumen SERIAL PRIMARY KEY,
            letra_unidad VARCHAR(5) NOT NULL,
            sistema_archivos VARCHAR(10) NOT NULL,
            capacidad_total_gb VARCHAR(15) NOT NULL,
            health VARCHAR(10) DEFAULT 'OK'
        );
    """)
    
    # 2. TABLA_DATOS
    cur.execute("""
        CREATE TABLE tabla_datos (
            id_dato SERIAL PRIMARY KEY,
            id_volumen INT REFERENCES tabla_volumenes(id_volumen),
            ruta_archivo VARCHAR(100) NOT NULL,
            contenido_bloque VARCHAR(100) NOT NULL,
            ultima_modificacion TIME NOT NULL
        );
    """)
    
    # 3. TABLA_SNAPSHOTS
    cur.execute("""
        CREATE TABLE tabla_snapshots (
            id_snapshot SERIAL PRIMARY KEY,
            id_dato INT REFERENCES tabla_datos(id_dato),
            vss_provider_usado VARCHAR(500) NOT NULL,
            contenido_congelado VARCHAR(100) NOT NULL,
            fecha_captura TIME NOT NULL
        );
    """)
    
    # Inyectar la data inicial fija que se muestra en tu diseño
    cur.execute("INSERT INTO tabla_volumenes VALUES (1, 'C:', 'NTFS', '500 GB', 'OK'), (2, 'D:', 'ReFS', '1000 GB', 'OK');")
    
    cur.execute("""
        INSERT INTO tabla_datos VALUES 
        (101, 1, '/users/doc.txt', 'Version 4.1.2 - Actual', '10:20:00'),
        (102, 1, '/db/logs.dat', '[Data Blobs]', '10:20:00'),
        (103, 2, '/config.cfg', '[Configuration Bits]', '10:20:00');
    """)
    
    cur.execute("""
        INSERT INTO tabla_snapshots (id_snapshot, id_dato, vss_provider_usado, contenido_congelado, fecha_captura) VALUES 
        (1, 101, 'Windows VSS Version 3.5.1 (S1)', 'Version 4.1.2', '10:00:15'),
        (2, 102, 'Dell HW', '[S2 Blob]', '10:15:30'),
        (3, 103, 'NetApp HW', '[S3 Config]', '10:18:45');
    """)
    
    cur.close()
    conn.close()
