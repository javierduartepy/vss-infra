import os, psycopg2; from src.core.models import init_db
try: init_db(); print("--- MIGRACION EXITOSA POR PYTHON ---")
except Exception as e: print("\n--- ERROR REAL ---"); print(str(e).encode("raw_unicode_escape").decode("cp1252", errors="ignore"))
