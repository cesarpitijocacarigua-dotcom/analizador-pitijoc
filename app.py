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
        col1, _ = st.columns(2)
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

    file_path = "BDPITIJOCPRO.xlsx"
    df = None
    
    if os.path.exists(file_path):
        # Cargamos el Excel y limpiamos nombres de columnas inmediatamente
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip().str.upper() # Quita espacios y pone todo en MAYÚSCULAS

    if df is not None:
        st.title("📦 Control de Inventario Pitijoc")
        
        # Intentamos el cálculo con nombres limpios
        try:
            # Forzamos conversión a número por si acaso hay celdas vacías
            df['COSTOS'] = pd.to_numeric(df['COSTOS'], errors='coerce').fillna(0)
            df['CATEGORIA'] = pd.to_numeric(df['CATEGORIA'], errors='coerce').fillna(1)
            
            # CÁLCULO DEL PRECIO DE VENTA
            df['PRECIO VENTA (BS)'] = df['COSTOS'] * tasa * df['CATEGORIA']
            calculo_exitoso = True
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")
            calculo_exitoso = False

        if rol == "admin":
            m1, m2, m3 = st.columns(3)
            inv_usd = (df['STOCK'] * df['COSTOS']).sum()
            m1.metric("Inventario Total ($)", f"${inv_usd:,.2f}")
            m2.metric("Items en Sistema", f"{len(df):,}")
            m3.metric("Stock Total", f"{df['STOCK'].sum():,.0f} unds")
            st.divider()
        
        # Buscador
        busq = st.text_input("🔍 Buscar por Código, Descripción, Ubicación o Categoría...")
        
        if busq:
            mask = df.apply(lambda r: busq.lower() in str(r).lower(), axis=1)
            df_display = df[mask]
        else:
            df_display = df.head(100)

        # Seguridad de Roles
        if rol == "ventas":
            # Columnas para vendedores (ocultamos costos)
            columnas_finales = ['CODIGO', 'DESCRIPCION', 'STOCK', 'UBICACIÓN', 'PRECIO VENTA (BS)']
        else:
            # Admin ve todo
            columnas_finales = df_display.columns.tolist()

        # Mostrar tabla solo las columnas que existan para evitar errores visuales
        cols_a_mostrar = [c for c in columnas_finales if c in df_display.columns]
        st.dataframe(df_display[cols_a_mostrar], use_container_width=True, hide_index=True)
    else:
        st.error(f"No se encontró el archivo {file_path} en la carpeta raíz.")

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["autenticado"]
        st.rerun()