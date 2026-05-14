import os
import openpyxl
import pandas as pd
from datetime import datetime
import pymysql

def procesar_e_importar_compras(ruta_excel, usuario_id, sucursal_id_defecto, db_config):
    """
    Procesa el formato de Ajuste de Compras de Profit, valida celdas críticas,
    cruza los artículos con los costos reales de la BD y actualiza el stock de inventario.
    """
    connection = None
    try:
        # 1. VALIDACIÓN DE ESTRUCTURA Y CABECERA (Celdas fijas con openpyxl)
        wb = openpyxl.load_workbook(ruta_excel, data_only=True)
        sheet = wb.active
        
        valA5 = str(sheet['A5'].value or '').strip()
        valA12 = str(sheet['A12'].value or '').strip()
        
        # Validación estricta contra formatos corruptos o equivocados
        if valA5 not in ['FORMATO DE AJUSTE DE ENTRADA Y SALIDAD', 'FORMATO DE AJUSTE DE ENTRADA Y SAL LA', 'FORMATO DE AJUSTE DE ENTRADA Y SALIDA']:
            raise ValueError(f"Validación fallida: Celda A5 inválida. Encontrado: '{valA5}'")
            
        if valA12 != 'NUMERO DE AJUSTE':
            raise ValueError(f"Validación fallida: Celda A12 debe ser 'NUMERO DE AJUSTE'. Encontrado: '{valA12}'")
            
        # Extraer datos de la cabecera
        numfac = str(sheet['B12'].value or '').strip()
        fecha_raw = sheet['B13'].value
        compra_concepto = str(sheet['B14'].value or '').strip()
        
        if not numfac:
            raise ValueError("El número de ajuste (celda B12) está vacío.")
            
        # Procesar la fecha del ajuste
        if isinstance(fecha_raw, datetime):
            fecha_ajuste = fecha_raw.strftime('%Y-%m-%d')
        elif fecha_raw:
            try:
                fecha_ajuste = pd.to_datetime(fecha_raw).strftime('%Y-%m-%d')
            except:
                fecha_ajuste = datetime.now().strftime('%Y-%m-%d')
        else:
            fecha_ajuste = datetime.now().strftime('%Y-%m-%d')
            
        wb.close() # Cerramos el lector de celdas fijas

        # 2. PROCESAR DATOS DE DETALLES CON PANDAS (Desde la fila 16)
        # Saltamos las primeras 15 filas (índice 14 en Python) para que la fila 16 sea el encabezado
        df = pd.read_excel(ruta_excel, skiprows=15)
        
        # Limpiar nombres de columnas limpiando espacios y asegurando mayúsculas
        df.columns = df.columns.str.strip().str.upper()
        
        # Renombrar columnas clave basándonos en la estructura original (C=CÓDIGO, D=UBICACIÓN, E=DESCRIPCIÓN, G=CANTIDAD)
        # Si el Excel no tiene nombres legibles en la fila 16, mapeamos por posición:
        columnas_esperadas = {df.columns[2]: 'CODIGO', df.columns[3]: 'UBICACION', df.columns[4]: 'DESCRIPCION', df.columns[6]: 'CANTIDAD'}
        df = df.rename(columns=columnas_esperadas)
        
        # Eliminar filas donde el código esté vacío
        df = df.dropna(subset=['CODIGO'])
        
        if df.empty:
            raise ValueError("No se encontraron productos válidos para cargar desde la fila 16.")

        # 3. CONECTAR A LA BASE DE DATOS PARA CRUCE DE COSTOS
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Cargar todos los costos actuales del inventario a un diccionario de Python {codigo_interno: costo}
        # Esto evita hacer miles de consultas individuales "SELECT" a la BD, haciéndolo instantáneo
        cursor.execute("SELECT codigo_interno, costo FROM productos")
        dict_costos = {row['codigo_interno']: float(row['costo'] or 0) for row in cursor.fetchall()}
        
        detalles_finales = []
        total_acumulado_compra = 0.0
        codigos_no_existentes = []
        
        # 4. LIMPIEZA Y CÁLCULO DE FILAS CON TU NUEVA REGLA DE NEGOCIO
        for _, fila in df.iterrows():
            codigo = str(fila.get('CODIGO', '')).strip()
            if codigo.startswith("'"):
                codigo = codigo[1:]
                
            # Formatear con ceros a la izquierda si el código de repuesto es numérico corto
            if codigo.isdigit() and len(codigo) < 5:
                codigo = codigo.zfill(5)
                
            cantidad = float(str(fila.get('CANTIDAD', 0)).replace('.', '').replace(',', '.') if isinstance(fila.get('CANTIDAD'), str) else (fila.get('CANTIDAD', 0) or 0))
            
            if cantidad <= 0:
                continue
                
            ubicacion = str(fila.get('UBICACION', '')).strip()
            descripcion = str(fila.get('DESCRIPCION', '')).strip()
            
            # --- TU MEJORA AQUÍ: El costo unitario sale de la base de datos, NO del Excel ---
            if codigo in dict_costos:
                costo_unitario = dict_costos[codigo]
            else:
                costo_unitario = 0.0
                codigos_no_existentes.append(codigo)
                
            costo_total_fila = cantidad * costo_unitario
            total_acumulado_compra += costo_total_fila
            
            detalles_finales.append({
                'codigo': codigo,
                'ubicacion': ubicacion,
                'descripcion': descripcion,
                'cantidad': cantidad,
                'costo_uni': costo_unitario,
                'costo_tot': costo_total_fila
            })

        # 5. GUARDAR TRANSACCIONALMENTE EN LA BASE DE DATOS
        cursor.execute("SET AUTOCOMMIT=0")
        
        # Insertar Cabecera de la Compra/Ajuste
        sql_compra = """
            INSERT INTO compras (numfac, fecha, compra, total, fk_usuario, fk_sucursal) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_compra, (numfac, fecha_ajuste, compra_concepto, total_acumulado_compra, usuario_id, sucursal_id_defecto))
        compra_id = cursor.lastrowid
        
        # Insertar Detalles y Actualizar Stock Masivamente
        sql_detalle = """
            INSERT INTO compras_detalles (fk_compras, fk_numfac, codigo, ubicacion, descripcion, cantidad, costo_uni, costo_tot) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for det in detalles_finales:
            # 1. Guardar detalle de compra
            cursor.execute(sql_detalle, (
                compra_id, numfac, det['codigo'], det['ubicacion'], 
                det['descripcion'], det['cantidad'], det['costo_uni'], det['costo_tot']
            ))
            
            # 2. Actualizar Stock en la sucursal correspondiente
            # Buscamos el ID del producto real
            cursor.execute("SELECT id FROM productos WHERE codigo_interno = %s", (det['codigo'],))
            prod = cursor.fetchone()
            
            if prod:
                producto_id = prod['id']
                
                # Buscar ID de la sucursal según el texto de la columna 'ubicacion' del Excel
                cursor.execute("SELECT id FROM sucursales WHERE nombre = %s OR codigo_excel = %s", (det['ubicacion'], det['ubicacion']))
                suc = cursor.fetchone()
                sucursal_id = suc['id'] if suc else sucursal_id_defecto
                
                # Modificar o Insertar Stock acumulado e implantar margen sugerido del 30% basado en tu costo real
                precio_sugerido = det['costo_uni'] * 1.30
                sql_stock = """
                    INSERT INTO producto_stock (producto_id, sucursal_id, stock, precio) 
                    VALUES (%s, %s, %s, %s) 
                    ON DUPLICATE KEY UPDATE stock = stock + VALUES(stock), precio = VALUES(precio)
                """
                cursor.execute(sql_stock, (producto_id, sucursal_id, det['cantidad'], precio_sugerido))

        # Confirmar todos los cambios si no hubo fallos
        connection.commit()
        
        print(f"🚀 ¡Ajuste {numfac} importado con éxito! Total Compra calculado con costos de BD: ${total_acumulado_compra:,.2f}")
        if codigos_no_existentes:
            print(f"⚠️ Aviso: Los siguientes códigos no existen en el inventario actual y se guardaron con costo 0: {set(codigos_no_existentes)}")
            
        return True, numfac, len(detalles_finales), list(set(codigos_no_existentes))

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"❌ Error crítico procesando compras: {e}")
        return False, None, str(e), []
        
    finally:
        if connection:
            connection.close()