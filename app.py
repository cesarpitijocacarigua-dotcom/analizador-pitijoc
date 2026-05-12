import streamlit as st
import pandas as pd
import os

# Configuración de alto rendimiento
st.set_page_config(page_title="Pitijoc Pro", layout="wide", page_icon="📦")

# 1. FUNCIÓN DE CARGA ULTRA-RÁPIDA (Solo se ejecuta una vez)
@st.cache_data(ttl=3600) # Guarda los datos por 1 hora en memoria
def cargar_datos(ruta):
    if os.path.exists(ruta):
        df = pd.read_excel(ruta)
        df.columns = df.columns.str.strip().str.upper()
        # Pre-procesamiento de números para evitar lentitud en el buscador
        df['COSTOS'] = pd.to_numeric(df['COSTOS'], errors='coerce').fillna(0)
        df['CATEGORIA'] = pd.to_numeric(df['CATEGORIA'], errors='coerce').fillna(1)
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)
        return df
    return None

# Credenciales
USUARIOS = {
    "Cesarpitijoc": {"clave": "cesar1043*", "rol": "admin"},
    "VentaPitijoc": {"clave": "123v456*", "rol": "ventas"}
}

def login():
    if "autenticado" not in st.session_state:
        st.title("🔐 Acceso Pitijoc CA")
        u = st.text_input("Usuario")
        c = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if u in USUARIOS and USUARIOS[u]["clave"] == c:
                st.session_state.update({"autenticado": True, "usuario": u, "rol": USUARIOS[u]["rol"]})
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

if login():
    rol = st.session_state["rol"]
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    tasa = st.sidebar.number_input("Tasa USD/BS", value=690.0)

    # Carga optimizada
    df = cargar_datos("BDPITIJOCPRO.xlsx")

    if df is not None:
        # Cálculo rápido (Vectorizado)
        df['PRECIO VENTA (BS)'] = df['COSTOS'] * tasa * df['CATEGORIA']
        
        st.title("📦 Inventario Pitijoc")

        if rol == "admin":
            c1, c2, c3 = st.columns(3)
            c1.metric("Total ($)", f"${(df['STOCK'] * df['COSTOS']).sum():,.2f}")
            c2.metric("Items", f"{len(df):,}")
            c3.metric("Existencia", f"{df['STOCK'].sum():,.0f}")
        
        # BUSCADOR OPTIMIZADO
        busq = st.text_input("🔍 Buscar Código, Descripción o Ubicación...", placeholder="Escribe para filtrar...")
        
        if busq:
            # Buscamos solo en columnas específicas para ganar velocidad
            busq = busq.lower()
            df_display = df[
                df['CODIGO'].astype(str).str.lower().str.contains(busq) | 
                df['DESCRIPCION'].astype(str).str.lower().str.contains(busq) |
                df['UBICACIÓN'].astype(str).str.lower().str.contains(busq)
            ]
        else:
            df_display = df.head(50)

        # Selección de columnas por Rol
        if rol == "ventas":
            cols = ['CODIGO', 'DESCRIPCION', 'STOCK', 'UBICACIÓN', 'PRECIO VENTA (BS)']
        else:
            cols = df_display.columns.tolist()

        # Renderizado de tabla eficiente
        st.dataframe(df_display[cols], use_container_width=True, hide_index=True)
    
    if st.sidebar.button("Cerrar Sesión"):
        st.cache_data.clear() # Limpia memoria al salir
        del st.session_state["autenticado"]
        st.rerun()