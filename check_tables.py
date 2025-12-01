import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="hotel_db",
        user="postgres",
        password="admin",
        port="5432"
    )
    cur = conn.cursor()
    
    # Obtener todas las tablas
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public'
    """)
    
    tables = cur.fetchall()
    print("Tablas en la base de datos:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Verificar si existe tabla de tickets
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'tickets'
        )
    """)
    
    exists = cur.fetchone()[0]
    if exists:
        print("\n✅ La tabla 'tickets' existe")
        cur.execute("SELECT * FROM tickets LIMIT 5")
        rows = cur.fetchall()
        print(f"Registros encontrados: {len(rows)}")
    else:
        print("\n❌ La tabla 'tickets' NO existe")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
