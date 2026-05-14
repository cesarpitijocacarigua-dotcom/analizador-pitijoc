import flet as ft
import pymysql
import pandas as pd

# 1. CONFIGURACIÓN MAESTRA DE TU BASE DE DATOS (Navicat Dump)
DB_CONFIG = {
    "host": "localhost",
    "user": "asoft",
    "password": "csm123*",
    "database": "tienda_pitijoc",
    "cursorclass": pymysql.cursors.DictCursor
}

def obtener_metricas_reales():
    """Consulta la base de datos real sin inventar datos simulados."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # Productos Totales
            cursor.execute("SELECT COUNT(*) AS total FROM productos")
            total_prod = cursor.fetchone()['total']
            
            # Clientes registrados (Rol cliente)
            cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'cliente'")
            total_clientes = cursor.fetchone()['total']
            
            # Ventas Totales históricas cargadas
            cursor.execute("SELECT SUM(total_costo) AS total FROM ventas_importadas")
            res_ventas = cursor.fetchone()['total']
            total_ventas = float(res_ventas) if res_ventas else 0.0
            
        return total_prod, total_clientes, total_ventas
    except Exception as e:
        print(f"Error de conexión: {e}")
        return 0, 0, 0.0

def main(page: ft.Page):
    page.title = "Soluciones Asoft - Control de Inventario Pitijoc C.A."
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Cargar la data real de entrada
    total_prod, total_clientes, total_ventas = obtener_metricas_reales()

    # ==========================================
    # VISTA 1: DASHBOARD RESUMEN REAL
    # ==========================================
    def crear_kpi_card(titulo, valor, color_borde):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=12, color=ft.colors.GREY_700, weight=ft.FontWeight.BOLD),
                ft.Text(valor, size=28, color=ft.colors.BLACK, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=15,
            border=ft.border.all(1, color_borde),
            border_radius=8,
            expand=True,
            height=100
        )

    dashboard_view = ft.Column([
        ft.Text("📊 Analizador de Operaciones en Tiempo Real", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Monitoreo basado estrictamente en registros de base de datos MySQL", size=14, color=ft.colors.GREY_600),
        ft.Divider(),
        
        # Fila de KPI Cards Reales
        ft.Row([
            crear_kpi_card("💰 VENTAS MAESTRAS TOTALES", f"$ {total_ventas:,.2f}", ft.colors.GREEN_700),
            crear_kpi_card("📦 ARTÍCULOS EN CATÁLOGO", str(total_prod), ft.colors.BLUE_700),
            crear_kpi_card("👥 CLIENTES ACTIVOS", str(total_clientes), ft.colors.ORANGE_700),
        ], spacing=15),
        
        ft.Divider(),
        ft.Text("🏢 Estado Operativo de Sucursales", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("Las gráficas de volúmenes e importaciones se activarán al detectar registros en ventas_importadas.", size=12, italic=True)
    ], scroll=ft.ScrollMode.ALWAYS)

    # ==========================================
    # VISTA 2: NÚCLEO DE IMPORTACIÓN (BOTONES DE CARGA)
    # ==========================================
    import_view = ft.Column([
        ft.Text("📥 Consolidación de Datos (Profit Plus)", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Cargar Reporte de Ventas", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Seleccionar Archivo de Ventas", icon=ft.icons.UPLOAD_FILE),
                ]), padding=20
            )
        ),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Cargar Ajuste de Entrada (Compras)", size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Seleccionar Archivo de Ajuste", icon=ft.icons.FILE_PRESENT_ROUNDED),
                ]), padding=20
            )
        )
    ])

    # ==========================================
    # ENRUTADOR POR PESTAÑAS (TABS INTERNOS PRO)
    # ==========================================
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Resumen Ejecutivo", icon=ft.icons.DASHBOARD, content=ft.Container(content=dashboard_view, padding=20)),
            ft.Tab(text="Matriz Multitienda", icon=ft.icons.CHAIR_ALT, content=ft.Container(content=ft.Text("Espacio reservado para la súper matriz consolidada"), padding=20)),
            ft.Tab(text="Motores de Carga", icon=ft.icons.CLOUD_UPLOAD, content=ft.Container(content=import_view, padding=20)),
        ],
        expand=1
    )

    page.add(tabs)

# Ejecutar aplicación en modo Escritorio Pro
if __name__ == "__main__":
    ft.app(target=main)