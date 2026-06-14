import psycopg2, os

# Limpia variables de entorno antes de conectar
for var in ["PGUSER", "PGPASSWORD", "PGDATABASE", "PGSERVICE", "PGSERVICEFILE"]:
    os.environ.pop(var, None)

conn = psycopg2.connect(
    dbname="hvac_db",
    user="postgres",
    password="admin",
    host="localhost",
    port="5432"
)
print("Conexión OK")
conn.close()
