import re
import pandas as pd
import openpyxl
from datetime import datetime
import pymysql
# Reutilizamos tu función de conexión guardada
# from conexion import conectar_db 

def procesar_e_importar_ventas(ruta_excel, sucursal_id, db_config):
    """
    Lee el reporte de Profit, extrae la fecha de A6, detecta la tabla dinámicamente,
    limpia los datos y los inserta en la base de datos MySQL de manera óptima.
    """
    try:
        # 1. Extraer la fecha del informe desde la celda A6 usando openpyxl
        wb = openpyxl.load_workbook(ruta_excel, read_only=True)
        sheet = wb.active
        celda_a6 = str(sheet['A6'].value or '')
        wb.close()
        
        match_fecha = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', celda_a6)
        if not match_fecha:
            raise ValueError("No se encontró una fecha válida en la celda A6 del reporte.")
        
        fecha_informe = datetime.strptime(match_fecha.group(1), '%d/%m/%Y').strftime('%Y-%m-%d')
        print(f"📅 Fecha del informe detectada: {fecha_informe}")

        # 2. Buscar la fila del encabezado ('CODIGO') dinámicamente
        fila_encabezado = None
        for i in range(1, 21):
            df_check = pd.read_excel(ruta_excel, nrows=1, skiprows=i-1, header=None)
            if not df_check.empty and str(df_check.iloc[0, 0]).strip().upper() == 'CODIGO':
                fila_encabezado = i - 1
                break
                
        if fila_encabezado is None:
            raise ValueError("No se localizó la columna principal 'CODIGO' en las primeras 20 filas.")

        # 3. Cargar los datos con Pandas desde la fila correcta
        df = pd.read_excel(ruta_excel, skiprows=fila_encabezado)
        
        # Estandarizar nombres de columnas a Mayúsculas y sin espacios extras
        df.columns = df.columns.str.strip().str.upper()
        
        # Eliminar filas donde el código esté vacío
        df = df.dropna(subset=['CODIGO'])
        
        # 4. Limpieza de datos (Reglas de negocio de Cesar)
        df['CODIGO'] = df['CODIGO'].astype(str).str.strip()
        # Quitar comilla simple inicial si existe
        df['CODIGO'] = df['CODIGO'].apply(lambda x: x[1:] if x.startswith("'") else x)
        
        # Filtrar repuestos que contengan "- *" en el artículo (comentarios de Profit)
        if 'ARTICULO' in df.columns:
            df = df[~df['ARTICULO'].astype(str).str.contains(r'-\s*\*')]

        # Normalizar nombres de columnas alternativas (Stock)
        if 'STOCK ACT' in df.columns and 'STOCK' not in df.columns:
            df['STOCK'] = df['STOCK ACT']
            
        # 5. Conectar e insertar a la Base de Datos usando transacciones limpias
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # --- NUEVA VALIDACIÓN: Evitar duplicados por sucursal y fecha ---
        sql_check = "SELECT COUNT(*) AS conteo FROM ventas_importadas WHERE sucursal_id = %s AND fecha_informe = %s"
        cursor.execute(sql_check, (sucursal_id, fecha_informe))
        if cursor.fetchone()['conteo'] > 0:
            connection.close()
            raise Exception(f"Ya existen ventas registradas para esta sucursal en la fecha {fecha_informe}. Operación cancelada.")

        # Query de inserción masiva
        sql_insert = """
            INSERT INTO ventas_importadas 
            (sucursal_id, fecha_informe, codigo, articulo, factura, almacen, cantidad, categoria, 
             costodolar, total_costo, precio_real, precio_vendido, descuentos, neto, stock_act, tres_meses)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        registros = []
        for _, fila in df.iterrows():
            # Cálculos automáticos si el formato viene incompleto (espejo de la lógica de tu PHP)
            is_completo = 'TOTAL COSTO' in df.columns
            cantidad = float(fila.get('CANTIDAD', 0) or 0)
            costo_dolar = float(fila.get('COSTODOLAR', 0) or 0)
            precio_vendido = float(fila.get('PRECIO VENDIDO', 0) or 0)
            precio_real = float(fila.get('PRECIO REAL', 0) or 0)
            
            total_costo = float(fila.get('TOTAL COSTO', 0) or 0) if is_completo else (cantidad * costo_dolar)
            descuentos = float(fila.get('DESCUENTOS', 0) or 0) if is_completo else (precio_vendido - precio_real)

            registro = (
                sucursal_id,
                fecha_informe,
                fila.get('CODIGO'),
                fila.get('ARTICULO'),
                fila.get('FACTURA'),
                fila.get('ALMACEN'),
                cantidad,
                fila.get('CATEGORIA'),
                costo_dolar,
                total_costo,
                precio_real,
                precio_vendido,
                descuentos,
                fila.get('NETO'),
                fila.get('STOCK'),
                fila.get('TRES MESES')
            )
            registros.append(registro)

        # Inserción en bloque (Ultra veloz)
        cursor.executemany(sql_insert, registros)
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"🚀 ¡Éxito! Se importaron {len(registros)} artículos correctamente a la sucursal {sucursal_id}.")
        return True, len(registros)

    except Exception as e:
        print(f"❌ Error al procesar la carga: {e}")
        return False, str(e)