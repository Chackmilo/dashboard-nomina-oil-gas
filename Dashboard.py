import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Nómina Oil & Gas",
    page_icon="📊",
    layout="wide"
)

# Función optimizada para limpiar datos monetarios
def clean_money_optimized(series):
    """
    Limpia una serie de pandas que contiene datos monetarios.
    Elimina símbolos de moneda, separadores de miles y convierte a tipo numérico.
    Utiliza operaciones vectorizadas para mayor eficiencia.

    Args:
        series (pd.Series): Serie de pandas con datos monetarios.

    Returns:
        pd.Series: Serie de pandas con datos numéricos limpios, NaN donde no se pudo convertir.
    """
    return series.astype(str).str.replace(r'[$,]', '', regex=True).str.strip().replace('', np.nan).astype(float)


# Cargar datos
@st.cache_data
def load_data_optimized():
    """
    Carga los datos desde el archivo CSV 'Planta.csv', realiza limpieza y conversión de tipos.
    Utiliza pandas para operaciones eficientes y manejo de errores.

    Returns:
        pd.DataFrame: DataFrame con los datos cargados y limpios.
                      None si ocurre un error al cargar los datos.
    """
    try:
        df = pd.read_csv("D:\Python\Planta.csv")

        # Lista de columnas monetarias
        monetary_columns = [
            'SALARIO MENSUAL INDIVIDUAL', 'Prestaciones AVG',
            'Prestaciones Ajustado', 'Prima Servicios',
            'Cesantías', 'Intereses Cesantias', 'Vacaciones',
            'SENA', 'ICBF', 'Caja de Compensación',
            'Salud', 'Pensión', 'ARL (2% avg)',
            'Total Mensual (COP)', 'Anual (COP)',
            'Mensual (USD)', 'Anual (USD)'
        ]

        # Limpieza vectorizada de columnas monetarias
        for col in monetary_columns:
            if col in df.columns:
                df[col] = clean_money_optimized(df[col])


        # Convertir 'CANTIDAD' a numérico, errores a NaN y llenar NaN con 1
        df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce').fillna(1)

        # Llenar valores NaN en columnas monetarias con 0 de forma vectorizada
        df[monetary_columns] = df[monetary_columns].fillna(0)

        return df
    except FileNotFoundError:
        st.error("Error: El archivo Planta.csv no fue encontrado. Por favor, verifica la ruta y el nombre del archivo.")
        return None
    except pd.errors.ParserError as e:
        st.error(f"Error al parsear el archivo CSV: {str(e)}. Verifica que el archivo tenga el formato correcto.")
        return None
    except Exception as e:
        st.error(f"Error inesperado al cargar los datos: {str(e)}")
        return None


# Cargar datos optimizado
df = load_data_optimized()

if df is not None:
    # Título principal
    st.title("📊 Dashboard de Análisis de Nómina Oil & Gas")

    # Sidebar con filtros
    st.sidebar.header("Filtros")
    departamento = st.sidebar.multiselect(
        "Seleccionar Departamento",
        options=df["DEPARTAMENTO"].unique(),
        default=df["DEPARTAMENTO"].unique()
    )

    nivel = st.sidebar.multiselect(
        "Seleccionar Nivel",
        options=df["Nivel"].unique(),
        default=df["Nivel"].unique()
    )

    # Filtrar DataFrame
    df_filtered = df[
        df["DEPARTAMENTO"].isin(departamento) &
        df["Nivel"].isin(nivel)
    ].copy() # Usar .copy() para evitar SettingWithCopyWarning


    # Layout de 2 columnas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribución de Salarios por Departamento")
        fig_box = px.box(
            df_filtered,
            x="DEPARTAMENTO",
            y="SALARIO MENSUAL INDIVIDUAL",
            title="Distribución de Salarios por Departamento",
            height=500
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with col2:
        st.subheader("Cantidad de Empleados por Nivel")
        nivel_cantidad = df_filtered.groupby("Nivel")["CANTIDAD"].sum().reset_index() # Calcular la serie primero
        fig_bar = px.bar(
            nivel_cantidad, # Usar el DataFrame pre-calculado
            x="Nivel",
            y="CANTIDAD",
            title="Distribución de Personal por Nivel",
            height=500
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Nueva fila
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Costos Totales Mensuales por Departamento")
        dept_costs = df_filtered.groupby("DEPARTAMENTO")["Total Mensual (COP)"].sum().sort_values(ascending=True)
        fig_bar2 = px.bar(
            dept_costs, # Directamente la serie agrupada
            orientation='h',
            title="Costos Totales Mensuales por Departamento",
            height=500
        )
        st.plotly_chart(fig_bar2, use_container_width=True)

    with col4:
        st.subheader("Distribución de Prestaciones por Nivel")
        # No es necesario volver a convertir a numérico si load_data_optimized lo hace correctamente
        fig_scatter = px.scatter(
            df_filtered,
            x="SALARIO MENSUAL INDIVIDUAL",
            y="Prestaciones AVG",
            color="Nivel",
            size="CANTIDAD",
            size_max=50,
            title="Relación Salario vs Prestaciones",
            height=500
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Análisis de componentes salariales
    st.subheader("Desglose de Componentes Salariales")
    componentes = ['Salud', 'Pensión', 'ARL (2% avg)', 'SENA', 'ICBF', 'Caja de Compensación']
    df_componentes = df_filtered[componentes].mean()

    fig_pie = px.pie(
        values=df_componentes.values,
        names=df_componentes.index,
        title="Distribución Promedio de Componentes Salariales",
        height=500
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Métricas clave
    st.subheader("Métricas Clave")
    col5, col6, col7 = st.columns(3)

    with col5:
        total_empleados = df_filtered["CANTIDAD"].sum()
        st.metric("Total Empleados", f"{total_empleados:,.0f}")

    with col6:
        costo_mensual = df_filtered["Total Mensual (COP)"].sum()
        st.metric("Costo Mensual Total", f"${costo_mensual:,.0f} COP")

    with col7:
        promedio_salario = df_filtered["SALARIO MENSUAL INDIVIDUAL"].mean()
        st.metric("Salario Promedio", f"${promedio_salario:,.0f} COP")

    # Tabla de resumen
    st.subheader("Tabla de Resumen por Departamento")
    resumen_dept = df_filtered.groupby("DEPARTAMENTO").agg(
        Cantidad_de_Empleados=("CANTIDAD", "sum"), # Renombrar columnas directamente en agg
        Salario_Promedio=("SALARIO MENSUAL INDIVIDUAL", "mean"),
        Costo_Total_Mensual=("Total Mensual (COP)", "sum")
    ).round(2)

    st.dataframe(resumen_dept)
else:
    st.error("No se pudieron cargar los datos. Por favor, verifica que el archivo CSV existe y tiene el formato correcto.")
