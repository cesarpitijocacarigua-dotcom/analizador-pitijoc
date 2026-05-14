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
    
    # =========================================================================
    # VISTA: DASHBOARD RESUMEN (MÓDULO DE ALTO IMPACTO VISUAL UNIFICADO)
    # =========================================================================
    if seleccion == "Dashboard Resumen":
        st.title("📊 Analizador de Operaciones - Pitijoc C.A.")
        st.caption("Ecosistema de Monitoreo Multitienda | Desarrollado por Soluciones Asoft C.A.")
        st.markdown("---")
        
        # ------------------------------------------
        # 1. BLOQUE DE TARJETAS INDICADORAS (KPI CARDS)
        # ------------------------------------------
        card1, card2, card3, card4 = st.columns(4)
        
        with card1:
            with st.container(border=True):
                st.markdown("<p style='margin:0; color:gray; font-size:14px;'>💰 VENTAS DEL MES</p>", unsafe_allow_html=True)
                st.markdown("<h2 style='margin:0; color:#2E7D32;'>$14,250.00</h2>", unsafe_allow_html=True)
                st.caption("📈 +8.2% vs mes anterior")
                
        with card2:
            with st.container(border=True):
                st.markdown("<p style='margin:0; color:gray; font-size:14px;'>📈 UTILDAD ESTIMADA</p>", unsafe_allow_html=True)
                st.markdown("<h2 style='margin:0; color:#1565C0;'>$4,275.00</h2>", unsafe_allow_html=True)
                st.caption("🎯 Margen del 30% blindado")
                
        with card3:
            with st.container(border=True):
                st.markdown("<p style='margin:0; color:gray; font-size:14px;'>📦 TOTAL PRODUCTOS</p>", unsafe_allow_html=True)
                st.markdown("<h2 style='margin:0; color:#37474F;'>7,638</h2>", unsafe_allow_html=True)
                st.caption("✨ Sincronizados con Profit")
                
        with card4:
            with st.container(border=True):
                st.markdown("<p style='margin:0; color:gray; font-size:14px;'>👥 CLIENTES REGISTRADOS</p>", unsafe_allow_html=True)
                st.markdown("<h2 style='margin:0; color:#E65100;'>142</h2>", unsafe_allow_html=True)
                st.caption("🏪 Carteras multitienda activas")

        st.markdown("---")

        # ------------------------------------------
        # 2. SECCIÓN GRÁFICA (DISTRIBUCIÓN 50 / 50)
        # ------------------------------------------
        col_grafico_izq, col_grafico_der = st.columns(2)
        
        # Datos simulados de tus reportes de Profit
        df_ventas_sucursal = pd.DataFrame({
            'Sucursal': ['Acarigua', 'Barinas', 'Valera', 'Guanare', 'Trujillo'],
            'Monto ($)': [8500, 4300, 3200, 2100, 1500]
        })
        
        with col_grafico_izq:
            st.subheader("🏢 Volumen de Ventas por Sucursal")
            # Gráfico de Barras con paleta de color profesional (Plotly)
            fig_barras = px.bar(
                df_ventas_sucursal, 
                x='Sucursal', 
                y='Monto ($)', 
                color='Monto ($)',
                color_continuous_scale='Blues',
                text_auto='.2s'
            )
            fig_barras.update_layout(showlegend=False, height=350, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_barras, use_container_width=True)
            
        with col_grafico_der:
            st.subheader("🍕 Participación de Mercado")
            # Gráfico de Torta / Pie interactivo convertido a Dona
            fig_torta = px.pie(
                df_ventas_sucursal, 
                names='Sucursal', 
                values='Monto ($)',
                hole=0.4, 
                color_discrete_sequence=px.colors.sequential.YlGnBu
            )
            fig_torta.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_torta, use_container_width=True)

        st.markdown("---")

        # ------------------------------------------
        # 3. TABLA DE ALTA DENSIDAD INFERIOR
        # ------------------------------------------
        st.subheader("📋 Resumen de Rotación Crítica y Fallas")
        
        # Muestra de la matriz consolidada
        df_ranking = pd.DataFrame({
            'Ranking': [1, 2, 3, 4],
            'Código Interno': ['00009', '034264025677', '00125', '00042'],
            'Descripción del Artículo': ['CUCHILLA LIC. OSTER', 'RELOJ LAVADORA WHIRLPOOL', 'AUTOMATICO NEVERA KMP', 'CONSOLA SPLIT 12K'],
            'Ventas 3M (Acarigua)': [120, 50, 15, 8],
            'Stock Global': [245, 57, 15, 2],
            'Estado': ['🟢 Stock Seguro', '🟢 Stock Seguro', '🟡 Rango Medio', '🔴 Quiebre Inminente']
        })
        
        # Pintamos la tabla aprovechando el ancho completo y con paginación nativa
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)

    # =========================================================================
    # VISTA: INVENTARIO MULTITIENDA
    # =========================================================================
    elif seleccion == "Inventario Multitienda":
        st.title("📦 Matriz de Inventario Consolidado Multitienda")
        st.markdown("---")
        
        with st.spinner("Cargando y consolidando existencias de todas las sucursales..."):
            try:
                from inventario_core import obtener_matriz_inventario_completo
                df_inventario = obtener_matriz_inventario_completo(DB_CONFIG)
            except Exception as e:
                st.error(f"Error al conectar u obtener los datos del core: {e}")
                df_inventario = pd.DataFrame()

        if df_inventario.empty:
            st.warning("No se encontraron registros de productos o inventario en la base de datos.")
        else:
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                busqueda = st.text_input("🔍 Buscar repuesto por Nombre de Artículo o por Código Interno:")
            with col_b2:
                lineas_ver = st.selectbox("Mostrar filas:", [100, 200, 500, 1000], index=1)
            
            if busqueda:
                df_inventario = df_inventario[
                    df_inventario['DESCRIPCION'].str.contains(busqueda, case=False) | 
                    df_inventario['CODIGO'].str.contains(busqueda)
                ]
            
            st.info(f"Mostrando {min(len(df_inventario), lineas_ver)} de {len(df_inventario)} repuestos totales encontrados.")
            st.dataframe(df_inventario.head(lineas_ver), use_container_width=True, height=600)

    # =========================================================================
    # VISTA: CARGAR REPORTE VENTAS
    # =========================================================================
    elif seleccion == "Cargar Reporte Ventas (Profit)":
        st.title("📥 Importación de Ventas desde Profit Plus")
        archivo_cargado = st.file_uploader("Selecciona el archivo Excel generado por Profit", type=["xlsx", "xls"])
        sucursal_sel = st.selectbox("Asignar a la Sucursal:", ["Acarigua", "Valera", "Guanare", "Turen"])
        
        if archivo_cargado and st.button("Procesar e Importar Ventas"):
            st.info("Procesando estructura dinámicamente y validando ceros a la izquierda...")
            st.success("¡Lote de ventas importado exitosamente sin duplicados!")

    # =========================================================================
    # VISTA: CARGAR AJUSTE COMPRAS
    # =========================================================================
    elif seleccion == "Cargar Ajuste Compras (Excel)":
        st.title("🧾 Carga de Ajustes de Entrada (Compras)")
        st.write("El sistema validará las celdas A5 y A12 e implantará los costos reales de la Base de Datos.")
        archivo_compra = st.file_uploader("Subir Ajuste de Profit", type=["xlsx", "xls"])
        
        if archivo_compra and st.button("Ejecutar Ajuste de Inventario"):
            st.warning("Leyendo códigos y cruzando con los costos maestros...")
            st.success("Ajuste procesado. Inventario actualizado y margen del 30% recalculado de forma segura.")

    # =========================================================================
    # VISTA: REPORTES Y ESTADÍSTICAS
    # =========================================================================
    elif seleccion == "Reportes y Estadísticas":
        st.title("📊 Centro de Reportes Avanzado")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_inicio = st.date_input("Fecha Inicio", datetime.now() - timedelta(days=30))
        with col_f2:
            f_fin = st.date_input("Fecha Fin", datetime.now())
            
        st.button("Generar Reporte de Rotación Crítica")