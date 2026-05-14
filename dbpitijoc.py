import pymysql
import streamlit as st

# Configuración equivalente a tu cnx/db.php
db_config = {
    "host": "localhost",       # Cambiar por la IP del servidor si no corre local
    "user": "asoft",
    "password": "csm123*",     # Tu clave del archivo de configuración
    "database": "tienda_pitijoc",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor # Para recibir los datos como diccionarios (igual que PDO::FETCH_ASSOC)
}

def conectar_db():
    try:
        connection = pymysql.connect(**db_config)
        return connection
    except pymysql.MySQLError as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return None

# Prueba rápida de conexión en el Dashboard
# conn = conectar_db()
# if conn:
#     st.success("Conexión exitosa al ecosistema de datos Pitijoc!")
#     conn.close()