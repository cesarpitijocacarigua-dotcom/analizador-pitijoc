import pandas as pd
import pymysql

def normalizar_codigo(codigo_raw):
    """
    Sanea el código de repuesto eliminando comillas de texto,
    arreglando decimales flotantes de Excel y aplicando relleno de ceros
    ÚNICAMENTE a los códigos cortos de menos de 5 dígitos (Lapsus de Ángel solucionado).
    """
    if pd.isna(codigo_raw):
        return None
    
    codigo = str(codigo_raw).strip()
    
    # Si Excel lo leyó como flotante (ej: 9.0), le quitamos el decimal
    if codigo.endswith('.0'):
        codigo = codigo[:-2]
        
    # Quitar comilla simple inicial de Profit si existe
    if codigo.startswith("'"):
        codigo = codigo[1:]
        
    # Rellenar con ceros si es puramente numérico y corto, respetar si es largo
    if codigo.isdigit():
        if len(codigo) < 5:
            return codigo.zfill(5)  # Ej: 9 -> "00009"
        else:
            return codigo           # Ej: "034264025677" -> Se queda intacto
            
    return codigo

def obtener_matriz_inventario_completo(db_config):
    """
    Genera la súper matriz horizontal combinada cruzando productos con stock de cada 
    sucursal e integrando la columna de 3 meses extraída exclusivamente de ACARIGUA.
    """
    # Conectamos usando pymysql
    connection = pymysql.connect(**db_config)
    
    try:
        # 1. Obtener listado de todas las sucursales activas en orden alfabético
        df_sucursales = pd.read_sql("SELECT id, nombre FROM sucursales ORDER BY nombre ASC", connection)
        
        # 2. Obtener los productos maestros
        df_productos = pd.read_sql("""
            SELECT id, codigo_interno AS CODIGO, nombre AS DESCRIPCION, costo AS COSTO, cat AS CAT 
            FROM productos
        """, connection)
        
        if df_productos.empty:
            return pd.DataFrame() # Retorna tabla vacía si no hay productos
            
        # Normalizar los códigos de la base de datos para asegurar el cruce perfecto en memoria
        df_productos['CODIGO'] = df_productos['CODIGO'].apply(normalizar_codigo)
        
        # 3. EXTRAER ANALISIS DE 3 MESES FILTRADO EXCLUSIVAMENTE POR ACARIGUA
        # Buscamos de manera inteligente el ID de la sucursal de Acarigua
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM sucursales WHERE nombre LIKE '%Acarigua%' OR codigo_excel = 'ACA'")
        suc_aca = cursor.fetchone()
        aca_id = suc_aca[0] if suc_aca else None
        
        if aca_id:
            # Traemos el último registro de tres_meses para cada repuesto en Acarigua
            sql_3m = """
                SELECT codigo, tres_meses AS [3MESES] FROM (
                    SELECT codigo, tres_meses, ROW_NUMBER() OVER(PARTITION BY codigo ORDER BY id DESC) as rn
                    FROM ventas_importadas 
                    WHERE sucursal_id = %s AND codigo IS NOT NULL AND codigo != ''
                ) as sub WHERE rn = 1
            """
            df_3m = pd.read_sql(sql_3m, connection, params=(aca_id,))
        else:
            # Fallback de seguridad en caso de que aún no existan cargas de Acarigua
            sql_3m = pd.DataFrame(columns=['codigo', '3MESES'])
            
        # Normalizar códigos del reporte de 3 meses antes del cruce
        df_3m['codigo'] = df_3m['codigo'].apply(normalizar_codigo)
        
        # 4. TRAER TODO EL STOCK DE MANERA VERTICAL Y PIVOTEARLO HORIZONTALMENTE
        df_stock = pd.read_sql("SELECT producto_id, sucursal_id, stock FROM producto_stock", connection)
        
        if not df_stock.empty:
            # El truco mágico de Pandas: Cambia filas por columnas en un milisegundo
            df_stock_pivot = df_stock.pivot(index='producto_id', columns='sucursal_id', values='stock').fillna(0)
            
            # Reemplazar los IDs de las columnas por los nombres reales de las tiendas (Acarigua, Valera, Guanare...)
            id_a_nombre = dict(zip(df_sucursales['id'], df_sucursales['nombre']))
            df_stock_pivot = df_stock_pivot.rename(columns=id_a_nombre)
        else:
            # Si la tabla stock está vacía, preparamos las columnas vacías correspondientes
            df_stock_pivot = pd.DataFrame(columns=df_sucursales['nombre'].tolist())
            
        # 5. ENSAMBLAR LA GRAN MATRIZ USANDO MERGES DE PANDAS
        # Cruzamos productos con el stock horizontal por el ID de producto
        matriz = df_productos.merge(df_stock_pivot, left_on='id', right_index=True, how='left').fillna(0)
        
        # Cruzamos el resultado con los 3 meses de Acarigua usando la columna 'CODIGO'
        matriz = matriz.merge(df_3m, left_on='CODIGO', right_on='codigo', how='left').fillna(0)
        
        # Limpieza final de columnas técnicas usadas para los enlaces
        if 'codigo' in matriz.columns:
            matriz = matriz.drop(columns=['codigo'])
        matriz = matriz.drop(columns=['id'])
        
        # Ordenamos las columnas para la visualización definitiva en la web
        columnas_visibles = ['CODIGO', 'DESCRIPCION', 'COSTO', 'CAT'] + df_sucursales['nombre'].tolist() + ['3MESES']
        # Nos aseguramos de mapear solo las columnas que existan realmente para evitar caídas
        columnas_visibles = [col for col in columnas_visibles if col in matriz.columns]
        
        return matriz[columnas_visibles]
        
    finally:
        connection.close()