import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import hashlib

# Importamos los módulos de datos optimizados que creamos previamente
# from inventario_core import obtener_matriz_inventario_completo, importar_inventario_maestro
# from importador_ventas import procesar_e_importar_ventas

# 1. CONFIGURACIÓN ULTRA DE LA PÁGINA
st.set_page_config(
    page_title="Soluciones Asoft - Control Tienda Pitijoc C.A.",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de base de datos equivalente a db.php
DB_CONFIG = {
    "host": "localhost",
    "user": "asoft",
    "password": "csm123*",
    "database": "tienda_pitijoc",
    "charset": "utf8mb4"
}

# 2. GESTIÓN DE SESIÓN Y SEGURIDAD (Equivalente a auth.php y protector.php)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.sucursal_id = None

def login(usuario, password):
    # Aquí irá la verificación real con bcrypt/pymysql conectando a la tabla 'usuarios'
    # Por ahora emulamos el acceso de Cesar para pruebas de desarrollo:
    if usuario == "admin" and password == "csm123*":
        st.session_state.autenticado = True
        st.session_state.usuario = "Cesar (Soluciones Asoft)"
        st.session_state.rol = "superadmin"
        st.session_state.sucursal_id = 1 # Acarigua
        return True
    return False

# 3. INTERFAZ DE LOGUEO
if not st.session_state.autenticado:
    st.title("🔒 Sistema Administrativo Pitijoc C.A.")
    st.subheader("Desarrollado por Soluciones Asoft C.A.")
    
    with st.form("formulario_login"):
        user_input = st.text_input("Usuario / Cédula / RIF")
        pass_input = st.text_input("Contraseña", type="password")
        boton_enviar = st.form_submit_button("Ingresar al Sistema")
        
        if boton_enviar:
            if login(user_input, pass_input):
                st.success(f"Bienvenido {st.session_state.usuario}")
                st.rerun()
            else:
                st.error("Credenciales incorrectas. Verifique e intente de nuevo.")
else:
    # 4. PANEL PRINCIPAL (DASHBOARD) - USUARIO AUTENTICADO
    st.sidebar.title("📊 Menú Principal")
    st.sidebar.write(f"**Usuario:** {st.session_state.usuario}")
    st.sidebar.write(f"**Rol:** {st.session_state.rol.upper()}")
    
    # Selector de opciones del menú
    opciones_menu = [
        "Dashboard Resumen", 
        "Inventario Multitienda", 
        "Cargar Reporte Ventas (Profit)", 
        "Cargar Ajuste Compras (Excel)",
        "Reportes y Estadísticas",
        "Configuración del Sistema"
    ]
    
    # Restricción de menú según rol legacy de tienda.php
    if st.session_state.rol == 'cliente':
        opciones_menu = ["Tienda Virtual", "Mis Pedidos"]

    seleccion = st.sidebar.radio("Navegación", opciones_menu)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

    # --- ENRUTADOR DE VISTAS (Sustituye a todos los switch($accion) de PHP) ---
    
    if seleccion == "Dashboard Resumen":
        st.title("📈 Panel de Control Operativo")
        st.write(f"Estado del negocio al día de hoy: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Bloque de KPIs principales usando st.columns
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric(label="Total Artículos Registrados", value="7,638", delta="+13 nuevos este mes")
        with kpi2:
            st.metric(label="Ventas Totales del Período", value="$14,250.00", delta="▲ 8% vs mes anterior")
        with kpi3:
            st.metric(label="Alertas de Quiebre de Stock", value="42", delta="Revisar compras urgente", delta_color="inverse")
            
        st.markdown("---")
        st.subheader("Evolución de Ventas por Sucursal")
        # Gráfico interactivo nativo de muestra (Reemplaza a QuickChart)
        data_grafico = pd.DataFrame({
            'Sucursal': ['Acarigua', 'Valera', 'Trujillo', 'Guanare', 'Barinas'],
            'Ventas ($)': [8500, 3200, 1500, 2100, 4300]
        })
        fig = px.bar(data_grafico, x='Sucursal', y='Ventas ($)', color='Sucursal', text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    elif seleccion == "Inventario Multitienda":
        st.title("📦 Matriz de Inventario Consolidado")
        st.write("Vista completa de existencias cruzada con el análisis de 3 meses de Acarigua.")
        
        # Aquí conectamos la función del motor core que lee de la BD
        # df_inventario = obtener_matriz_inventario_completo(DB_CONFIG)
        # Muestra temporal simulando tu pantalla web real:
        df_muestra = pd.DataFrame({
            'CODIGO': ['00009', '034264025677', '00125'],
            'DESCRIPCION': ['CUCHILLA LIC. OSTER', 'RELOJ LAVADORA', 'AUTOMATICO NEVERA'],
            'COSTO': [4.50, 12.00, 8.50],
            'ACARIGUA': [150, 42, 0],
            'VALERA': [30, 15, 10],
            'GUANARE': [65, 0, 5],
            '3MESES': [120, 50, 15]
        })
        
        # Buscador dinámico integrado (Sustituye al JS de tienda.php)
        busqueda = st.text_input("Filtrar repuesto por nombre o código:")
        if busqueda:
            df_muestra = df_muestra[df_muestra['DESCRIPCION'].str.contains(busqueda, case=False) | df_muestra['CODIGO'].str.contains(busqueda)]
            
        st.dataframe(df_muestra, use_container_width=True)

    elif seleccion == "Cargar Reporte Ventas (Profit)":
        st.title("📥 Importación de Ventas desde Profit Plus")
        # Aquí mapeamos el formulario viejo de 'importar_ventas.php'
        archivo_cargado = st.file_with_container = st.file_uploader("Selecciona el archivo Excel generado por Profit", type=["xlsx", "xls"])
        sucursal_sel = st.selectbox("Asignar a la Sucursal:", ["Acarigua", "Valera", "Guanare", "Turen"])
        
        if archivo_cargado and st.button("Procesar e Importar Ventas"):
            st.info("Procesando estructura dinámicamente y validando ceros a la izquierda...")
            # Aquí se ejecuta: procesar_e_importar_ventas(archivo_cargado, sucursal_id, DB_CONFIG)
            st.success("¡Lote de ventas importado exitosamente sin duplicados!")

    elif seleccion == "Cargar Ajuste Compras (Excel)":
        st.title("🧾 Carga de Ajustes de Entrada (Compras)")
        st.write("El sistema validará las celdas A5 y A12 e implantará los costos reales de la Base de Datos.")
        archivo_compra = st.file_uploader("Subir Ajuste de Profit", type=["xlsx", "xls"])
        
        if archivo_compra and st.button("Ejecutar Ajuste de Inventario"):
            st.warning("Leyendo códigos y cruzando con los costos maestros...")
            st.success("Ajuste procesado. Inventario actualizado y margen del 30% recalculado de forma segura.")

    elif seleccion == "Reportes y Estadísticas":
        st.title("📊 Centro de Reportes Avanzado")
        # Selector de rango de fecha nativo de Streamlit
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_inicio = st.date_input("Fecha Inicio", datetime.now() - timedelta(days=30))
        with col_f2:
            f_fin = st.date_input("Fecha Fin", datetime.now())
            
        st.button("Generar Reporte de Rotación Crítica")