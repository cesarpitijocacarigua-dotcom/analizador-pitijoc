import streamlit as st
import pandas as pd
import os

# Configuración profesional
st.set_page_config(page_title="Pitijoc Pro - Inventario", layout="wide", page_icon="📦")

# Credenciales de acceso
USUARIOS = {
    "Cesarpitijoc": {"clave": "cesar1043*", "rol": "admin"},
    "VentaPitijoc": {"clave": "123v456*", "rol": "ventas"}
}

def login():
    if "autenticado" not in st.session_state:
        st.title("🔐 Acceso Pitijoc CA")
        col1, col2 = st.columns(2)
        with col1:
            u = st.text_input("Usuario")
            c = st.text_input("Contraseña", type="password")
            if st.button("Entrar"):
                if u in USUARIOS and USUARIOS[u]["clave"] == c:
                    st.session_state.update({"autenticado": True, "usuario": u, "rol": USUARIOS[u]["rol"]})
                    st.rerun()
                else:
                    st.error("Datos incorrectos")
        return False
    return True

if login():
    rol = st.session_state["rol"]
    st.sidebar.title(f"👤 {st.session_state['usuario']}")
    tasa = st.sidebar.number_input("Tasa USD/BS", value=690.0, format="%.2f")

    # Carga de archivo
    file_path = "BDPITIJOCPRO.xlsx"
    df = None
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)

    if df is not None:
        # Lógica de cálculo inteligente
        # Precio Venta = COSTO * Tasa * CATEGORIA
        df['PRECIO VENTA (BS)'] = df['COSTO'] * tasa * df['CATEGORIA']
        
        st.title("📦 Control de Inventario Pitijoc")

        if rol == "admin":
            m1, m2, m3 = st.columns(3)
            inv_usd = (df['STOCK'] * df['COSTO']).sum()
            m1.metric("Inventario Total ($)", f"${inv_usd:,.2f}")
            m2.metric("Items en Sistema", f"{len(df):,}")
            m3.metric("Stock Total", f"{df['STOCK'].sum():,.0f} unds")
            st.divider()
        
        # Buscador
        busq = st.text_input("🔍 Buscar por Código, Descripción o Ubicación...")
        
        # Filtrado
        if busq:
            df_display = df[df.apply(lambda r: busq.lower() in str(r).lower(), axis=1)]
        else:
            df_display = df.head(100)

        # Selección de columnas por Rol (Seguridad)
        if rol == "ventas":
            # Ventas no ve el costo de compra ni el margen (categoría)
            cols_mostrar = ['CODIGO', 'DESCRIPCION', 'STOCK', 'UBICACIÓN', 'PRECIO VENTA (BS)']
        else:
            # Admin ve todo
            cols_mostrar = df_display.columns.tolist()

        st.dataframe(df_display[cols_mostrar], use_container_width=True, hide_index=True)
    else:
        st.error(f"Archivo {file_path} no encontrado en la carpeta.")

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["autenticado"]
        st.rerun()