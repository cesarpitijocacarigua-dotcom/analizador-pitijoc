import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración Profesional en Español
st.set_page_config(page_title="Pitijoc Pro - Gestión de Inventario", layout="wide", page_icon="📈")

# Estilos visuales
st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Panel de Control de Inventario - Pitijoc C.A.")
st.write("Herramienta de análisis financiero y de stock en tiempo real.")
st.markdown("---")

# --- BARRA LATERAL (HERRAMIENTAS DE AYUDA) ---
st.sidebar.header("🛠️ Configuración")

with st.sidebar.expander("❓ Ayuda e Instrucciones"):
    st.write("""
    1. **Carga:** Sube tu archivo .xlsx.
    2. **Tasa:** Ajusta el valor del dólar para actualizar costos en Bs.
    3. **Buscador:** Filtra por código o nombre del repuesto.
    4. **Exportar:** Descarga la lista filtrada con los precios del día.
    """)

archivo_subido = st.sidebar.file_uploader("Subir base de datos (Excel)", type=["xlsx"], help="Selecciona el archivo BDPITIJOC.xlsx")

tasa_cambio = st.sidebar.number_input(
    "Tasa de Cambio (BS/USD):", 
    min_value=1.0, 
    value=36.5, 
    step=0.1,
    help="Define el valor del dólar para los cálculos automáticos."
)

if archivo_subido:
    try:
        # Carga de datos
        df = pd.read_excel(archivo_subido, dtype={'CODIGO': str})
        df = df.dropna(how='all')
        
        # Cálculos de moneda
        df['COSTO_BS'] = df['COSTOS'] * tasa_cambio
        df['VALOR_TOTAL_USD'] = df['STOCK'] * df['COSTOS']
        df['VALOR_TOTAL_BS'] = df['VALOR_TOTAL_USD'] * tasa_cambio

        # --- MÉTRICAS ---
        val_usd = df['VALOR_TOTAL_USD'].sum()
        val_bs = val_usd * tasa_cambio

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Inventario (USD)", f"${val_usd:,.2f}")
        with c2:
            st.metric("Inventario (BS)", f"Bs. {val_bs:,.2f}")
        with c3:
            st.metric("Variedad de Items", f"{len(df):,}")
        with c4:
            stock_total = df['STOCK'].sum()
            st.metric("Existencia Total", f"{int(stock_total):,} unds")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BUSCADOR Y FILTROS ---
        col_bus, col_btn = st.columns([3, 1])
        
        with col_bus:
            busqueda = st.text_input("🔍 Buscador inteligente (Código, Descripción o Categoría):", 
                                     placeholder="Ejemplo: Compresor o 00120...")
        
        # Filtrado
        if busqueda:
            df_filtrado = df[
                df['CODIGO'].str.contains(busqueda, case=False, na=False) | 
                df['DESCRIPCION'].str.contains(busqueda, case=False, na=False)
            ]
        else:
            df_filtrado = df

        # --- BOTÓN DE DESCARGA ---
        # Creamos el archivo Excel en memoria para que sea rápido
        def convertir_a_excel(df_descarga):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_descarga.to_excel(writer, index=False, sheet_name='Precios_Hoy')
            return output.getvalue()

        excel_data = convertir_a_excel(df_filtrado[['CODIGO', 'DESCRIPCION', 'STOCK', 'COSTOS', 'COSTO_BS']])
        
        with col_btn:
            st.write("") # Espaciador
            st.download_button(
                label="📥 Descargar Lista Actualizada",
                data=excel_data,
                file_name=f"Lista_Precios_Pitijoc_{tasa_cambio}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Haz clic para descargar los resultados actuales en un archivo Excel."
            )

        # --- TABLA DE DATOS ---
        st.subheader("📋 Detalle de Productos")
        st.dataframe(
            df_filtrado[['CODIGO', 'DESCRIPCION', 'STOCK', 'COSTOS', 'COSTO_BS']].style.format({
                'COSTOS': '${:,.2f}',
                'COSTO_BS': 'Bs. {:,.2f}',
                'STOCK': '{:,.0f}'
            }), 
            use_container_width=True, 
            hide_index=True
        )

        # --- GRÁFICO ---
        st.markdown("---")
        st.subheader("📊 Análisis de Valor por Producto (Top 10)")
        top_10 = df.nlargest(10, 'VALOR_TOTAL_USD')
        
        fig = px.bar(top_10, 
                     x='VALOR_TOTAL_USD', 
                     y='DESCRIPCION', 
                     orientation='h',
                     title="Productos con Mayor Inversión de Capital (USD)",
                     labels={'VALOR_TOTAL_USD': 'Valorización en Almacén ($)', 'DESCRIPCION': 'Repuesto'},
                     color='VALOR_TOTAL_USD',
                     color_continuous_scale='Greens',
                     template="plotly_white")
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Se encontró un detalle en el archivo: {e}")
        st.info("Asegúrate de que tu Excel tenga las columnas: CODIGO, DESCRIPCION, STOCK y COSTOS.")
else:
    st.info("👋 ¡Hola! Por favor carga tu archivo de inventario en la izquierda para comenzar el análisis.")