from db import get_connection

try:
    conn = get_connection()
    print("✅ Conectado a PostgreSQL correctamente")
    conn.close()
except Exception as e:
    print("❌ Error de conexión:", e)