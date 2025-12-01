import psycopg2
from db import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    
    # Obtener estructura de la tabla tickets
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'tickets'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    print("Estructura de la tabla 'tickets':")
    print("-" * 60)
    for col in columns:
        col_name, data_type, max_length = col
        length_info = f"({max_length})" if max_length else ""
        print(f"  {col_name}: {data_type}{length_info}")
    
    print("\n" + "-" * 60)
    
    # Obtener algunos registros de ejemplo
    cur.execute("SELECT * FROM tickets LIMIT 5")
    rows = cur.fetchall()
    
    print(f"\nRegistros de ejemplo ({len(rows)} encontrados):")
    print("-" * 60)
    
    if rows:
        # Obtener nombres de columnas
        col_names = [desc[0] for desc in cur.description]
        print("Columnas:", ", ".join(col_names))
        print()
        for i, row in enumerate(rows, 1):
            print(f"Registro {i}:")
            for col_name, value in zip(col_names, row):
                print(f"  {col_name}: {value}")
            print()
    else:
        print("No hay registros en la tabla")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
