import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="hotel_db",
        user="postgres",
        password="admin",
        port="5432"
    )