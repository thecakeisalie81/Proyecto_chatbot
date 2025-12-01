from db import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    
    # Verificar si existe la tabla
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'habitaciones'
        )
    """)
    
    exists = cur.fetchone()[0]
    
    if exists:
        print("✅ La tabla 'habitaciones' existe\n")
        
        # Obtener estructura
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'habitaciones'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print("Estructura de la tabla 'habitaciones':")
        print("-" * 60)
        for col in columns:
            col_name, data_type, max_length = col
            length_info = f"({max_length})" if max_length else ""
            print(f"  {col_name}: {data_type}{length_info}")
        
        # Obtener algunos registros
        cur.execute("SELECT * FROM habitaciones LIMIT 5")
        rows = cur.fetchall()
        
        print(f"\n{len(rows)} registros de ejemplo:")
        print("-" * 60)
        
        if rows:
            col_names = [desc[0] for desc in cur.description]
            for i, row in enumerate(rows, 1):
                print(f"\nRegistro {i}:")
                for col_name, value in zip(col_names, row):
                    print(f"  {col_name}: {value}")
        else:
            print("No hay registros en la tabla")
    else:
        print("❌ La tabla 'habitaciones' NO existe")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
