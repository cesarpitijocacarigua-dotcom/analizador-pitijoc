import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Pitijoc Pro - Gestión de Inventario", layout="wide")

# Definición de credenciales
USUARIOS = {
    "Cesarpitijoc": {"clave": "cesar1043*", "rol": "admin"},
    "VentaPitijoc": {"clave": "123v456*", "rol": "ventas"}
}

def login():
    if "autenticado" not in st.session_state:
        st.title("🔐 Acceso al Sistema Pitijoc")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar"):
            if usuario in USUARIOS and USUARIOS[usuario]["clave"] == clave:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["rol"] = USUARIOS[usuario]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
        return False
    return True

if login():
    rol = st.session_state["rol"]
    
    # BARRA LATERAL
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/762/762666.png", width=100)
    st.sidebar.title(f"Bienvenido, {st.session_state['usuario']}")
    
    # Solo el Admin puede subir archivos
    df = None
    if rol == "admin":
        archivo = st.sidebar.file_uploader("Actualizar Inventario (Excel)", type=["xlsx"])
        if archivo:
            df = pd.read_excel(archivo)
    else:
        st.sidebar.info("Modo consulta: Solo búsqueda disponible.")
        # Aquí cargamos el archivo por defecto si existe en el repo
        try:
            df = pd.read_excel("BDPITIJOC.xlsx")
        except:
            st.warning("Esperando que el administrador cargue la base de datos...")

    # CUERPO PRINCIPAL
    st.title("📊 Panel de Control de Inventario")

    if df is not None:
        # Si es Admin, mostrar métricas financieras
        if rol == "admin":
            c1, c2, c3 = st.columns(3)
            total_usd = (df['STOCK'] * df['COSTOS']).sum()
            c1.metric("Valor Total (USD)", f"${total_usd:,.2f}")
            c2.metric("Variedad de Items", f"{len(df):,}")
            c3.metric("Existencia Total", f"{df['STOCK'].sum():,} unds")

        # Buscador (Disponible para todos)
        busqueda = st.text_input("🔍 Buscador inteligente (Código o Descripción)")
        
        if busqueda:
            resultado = df[df.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
            # Si es ventas, podemos filtrar qué columnas mostrar (Ej. ocultar costos si quieres)
            st.dataframe(resultado, use_container_width=True)
        else:
            st.dataframe(df.head(20), use_container_width=True)

    if st.sidebar.button("Cerrar Sesión"):
        del st.session_state["autenticado"]
        st.rerun()