import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establece conexión con el motor relacional PostgreSQL."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "vss_infra"),
        user=os.getenv("DB_USER", "javier"),
        password=os.getenv("DB_PASSWORD", "1234"),
        port=int(os.getenv("DB_PORT", 5432))
    )

def init_db():
    """Ejecuta el DDL para inicializar el esquema de alta transaccionalidad."""
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("DROP TABLE IF EXISTS transacciones;")
    cur.execute("""
        CREATE TABLE transacciones (
            id SERIAL PRIMARY KEY,
            monto NUMERIC,
            estado VARCHAR(20),
            creado_en TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Simulación de volumen inicial masivo para inducir congestión de tablas
    cur.execute("""
        INSERT INTO transacciones (monto, estado)
        SELECT random() * 1000, 'PROCESADO'
        FROM generate_series(1, 10000);
    """)
    
    cur.close()
    conn.close()
