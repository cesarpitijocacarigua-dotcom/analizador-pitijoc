import streamlit as st
import pandas as pd

# Configuración de página con estilo amigable
st.set_page_config(page_title="Pitijoc Pro - Gestión de Inventario", layout="wide", page_icon="⚙️")

# Estilo personalizado para las métricas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1f77b4; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Credenciales
USUARIOS = {
    "Cesarpitijoc": {"clave": "cesar1043*", "rol": "admin"},
    "VentaPitijoc": {"clave": "123v456*", "rol": "ventas"}
}

def login():
    if "autenticado" not in st.session_state:
        st.title("🔐 Acceso al Sistema Pitijoc")
        with st.container():
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión"):
                if usuario in USUARIOS and USUARIOS[usuario]["clave"] == clave:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = usuario
                    st.session_state["rol"] = USUARIOS[usuario]["rol"]
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        return False
    return True

if login():
    rol = st.session_state["rol"]
    
    # BARRA LATERAL (Procesos visibles)
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/762/762666.png", width=80)
    st.sidebar.title(f"Hola, {st.session_state['usuario']}")
    
    tasa_cambio = st.sidebar.number_input("Tasa de Cambio (BS/USD):", value=690.0, step=1.0, format="%.2f")
    
    df = None
    # Intento de cargar la base de datos por defecto (el archivo en el servidor)
    try:
        df = pd.read_excel("BDPITIJOC.xlsx")
    except:
        pass

    if rol == "admin":
        st.sidebar.divider()
        st.sidebar.subheader("⚙️ Panel de Control")
        nuevo_archivo = st.sidebar.file_uploader("Actualizar Inventario (Excel)", type=["xlsx"])
        if nuevo_archivo:
            df = pd.read_excel(nuevo_archivo)
    
    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["autenticado"]
        st.rerun()

    # CUERPO PRINCIPAL
    st.title("📦 Panel de Control de Inventario - Pitijoc CA")
    
    if df is not None:
        # Aseguramos que las columnas necesarias existan
        df['COSTO_BS'] = df['COSTOS'] * tasa_cambio
        
        # MÉTRICAS (Visibles solo para Admin)
        if rol == "admin":
            m1, m2, m3, m4 = st.columns(4)
            total_usd = (df['STOCK'] * df['COSTOS']).sum()
            total_bs = total_usd * tasa_cambio
            m1.metric("Inventario (USD)", f"${total_usd:,.2f}")
            m2.metric("Inventario (BS)", f"Bs. {total_bs:,.2f}")
            m3.metric("Variedad de Items", f"{len(df):,}")
            m4.metric("Existencia Total", f"{df['STOCK'].sum():,} unds")
            st.divider()

        # BUSCADOR (Para todos)
        busqueda = st.text_input("🔍 Buscador inteligente (Código, Descripción o Categoría):", placeholder="Ej. Compresor, 00120...")
        
        if busqueda:
            # Búsqueda flexible en todo el texto del archivo
            mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            resultado = df[mask]
        else:
            resultado = df.head(50)

        st.subheader("📋 Detalle de Productos")
        # Mostramos la tabla con las columnas de costos
        st.dataframe(resultado, use_container_width=True, hide_index=True)
    else:
        st.info("Por favor, sube el archivo 'BDPITIJOC.xlsx' en la barra lateral para comenzar.")