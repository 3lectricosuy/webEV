import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
# --- TÍTULO CON LOGO ---
col_logo, col_titulo = st.columns([1, 8]) # Ajusta los números para el tamaño

with col_logo:
    # Asegúrate de que el nombre del archivo coincida (ej: logo.png)
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=80) 
    else:
        st.write("🚗") # Emoji de respaldo por si el logo no carga

with col_titulo:
    st.title("EléctricosUy")

# --- ESTILO CSS (Simple y Profesional: Degradado Azul) ---
st.markdown("""
    <style>
    /* 1. Fondo Degradado Azul "Noche Eléctrica" en toda la App */
    .stApp {
        background: linear-gradient(135deg, #dbeafe 0%, #60a5fa 100%);
        background-attachment: fixed;
    }
    
    /* 2. Contenedor Principal con Semitransparencia Blanca */
    .main { 
        background-color: rgba(255, 255, 255, 0.88); /* Blanco al 88% de opacidad */
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* 3. Fuentes Negras/Oscuras para Máxima Legibilidad */
    h1, h2, h3, h4, p, label { color: #1a1a1a !important; font-family: 'Source Sans Pro', sans-serif; }
    
    /* 4. Recuadros de Métricas Blancos y Limpios */
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    
    /* 5. Estilo de las tarjetas de vehículos */
    .vehicle-card { border-bottom: 2px solid #e6e9ef; padding: 20px 0; }
    </style>
    """, unsafe_allow_html=True)
# --- RUTAS ---
# Así debe quedar tu código:
BASE_PATH = os.getcwd()  # Esto detecta automáticamente dónde está la carpeta del proyecto
VEHICULOS_PATH = "VEHICULOS"

@st.cache_data
def cargar_base_de_datos():
    lista_vehiculos = []
    
    # 1. Verificación de carpeta
    if not os.path.exists("VEHICULOS"):
        st.error("🚨 La carpeta 'VEHICULOS' no se encuentra en el servidor.")
        return pd.DataFrame()

    carpetas = [f for f in os.listdir("VEHICULOS") if os.path.isdir(os.path.join("VEHICULOS", f))]
    
    if not carpetas:
        st.warning("📂 Se encontró la carpeta 'VEHICULOS', pero está vacía.")
        return pd.DataFrame()

    for folder_name in carpetas:
        folder_path = os.path.join("VEHICULOS", folder_name)
        csv_path = os.path.join(folder_path, "datos.csv")
        
        if os.path.exists(csv_path):
            try:
                # 2. Intento de lectura robusto (detecta si es , o ;)
                try:
                    df_item = pd.read_csv(csv_path, sep=",", encoding='utf-8')
                    if df_item.shape[1] <= 1: # Si leyó mal, probamos con ;
                        df_item = pd.read_csv(csv_path, sep=";", encoding='utf-8')
                except:
                    df_item = pd.read_csv(csv_path, sep=";", encoding='latin-1')

                df_item['Ruta_Carpeta'] = folder_path
                lista_vehiculos.append(df_item)
            except Exception as e:
                st.sidebar.error(f"Error leyendo {folder_name}: {e}")
        else:
            # Esto nos dirá si falta el archivo en alguna carpeta
            st.sidebar.write(f"⚠️ No se halló datos.csv en: {folder_name}")

    if not lista_vehiculos: 
        return pd.DataFrame()
        
    df_total = pd.concat(lista_vehiculos, ignore_index=True)
    return df_total

df = cargar_base_de_datos()

# --- TÍTULO ---
st.title("🚗EléctricosUy")

if df.empty:
    st.warning("⚠️ No se encontraron datos en 'VEHICULOS'.")
else:
    # --- BARRA SUPERIOR DE FILTROS ---
    with st.expander("🔍 FILTROS Y BÚSQUEDA", expanded=True):
        # Fila 1: Buscador y Filtros de Categoría
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        
        with c1:
            search = st.text_input("Nombre del vehículo", placeholder="Buscar...")
        with c2:
            tipos = ["Todos"] + sorted(df['Tipo'].unique().tolist())
            tipo_sel = st.selectbox("Tipo", tipos)
        with c3:
            # Filtro por rango de Potencia (simplificado a opciones comunes)
            potencias = ["Todos"] + sorted([int(x) for x in df['Potencia_CV'].unique() if x > 0])
            pot_sel = st.selectbox("Potencia (CV)", potencias)
        with c4:
            autonomias = ["Todos"] + sorted([int(x) for x in df['Autonomia_km'].unique() if x > 0])
            aut_sel = st.selectbox("Autonomía (km)", autonomias)
        with c5:
            baterias = ["Todos"] + sorted([float(x) for x in df['Bateria_kWh'].unique() if x > 0])
            bat_sel = st.selectbox("Batería (kWh)", baterias)

    # --- BARRA DE ORDENAMIENTO (A la derecha) ---
    st.write("") # Espaciador
    o1, o2, o3 = st.columns([3, 1, 1])
    
    with o2:
        col_ordenar = st.selectbox("Ordenar por:", 
                                  ["Precio_USD", "Autonomia_km", "Bateria_kWh", "Potencia_CV"],
                                  format_func=lambda x: x.replace('_', ' '))
    with o3:
        sentido = st.selectbox("Orden:", ["Menor a Mayor", "Mayor a Menor"])

    # --- LÓGICA DE FILTRADO ---
    df_f = df.copy()
    if search:
        df_f = df_f[df_f['Vehículo'].str.contains(search, case=False)]
    if tipo_sel != "Todos":
        df_f = df_f[df_f['Tipo'] == tipo_sel]
    if pot_sel != "Todos":
        df_f = df_f[df_f['Potencia_CV'] == pot_sel]
    if aut_sel != "Todos":
        df_f = df_f[df_f['Autonomia_km'] == aut_sel]
    if bat_sel != "Todos":
        df_f = df_f[df_f['Bateria_kWh'] == bat_sel]

    # --- LÓGICA DE ORDENAMIENTO ---
    es_ascendente = True if sentido == "Menor a Mayor" else False
    df_f = df_f.sort_values(by=col_ordenar, ascending=es_ascendente)

    st.info(f"Mostrando {len(df_f)} vehículos según tus criterios.")
    st.markdown("---")

    # --- LISTADO DE VEHÍCULOS ---
    for auto in df_f.itertuples():
        with st.container():
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                foto_path = os.path.join(auto.Ruta_Carpeta, "foto_1.jpg")
                if os.path.exists(foto_path):
                    st.image(foto_path, use_container_width=True)
                else:
                    st.info("📷 Sin foto")

            with col_info:
                st.header(auto.Vehículo)
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Precio", f"U$S {int(auto.Precio_USD):,}")
                m2.metric("Autonomía", f"{int(auto.Autonomia_km)} km")
                m3.metric("Batería", f"{auto.Bateria_kWh} kWh")
                m4.metric("Potencia", f"{int(auto.Potencia_CV)} CV")
                
                st.write(f"**Categoría:** {auto.Tipo} | **Torque:** {auto.Torque_Nm} Nm")
                
                # Miniaturas
                cols_fotos = st.columns(4)
                for i in range(2, 5):
                    sub_foto = os.path.join(auto.Ruta_Carpeta, f"foto_{i}.jpg")
                    if os.path.exists(sub_foto):
                        cols_fotos[i-2].image(sub_foto, use_container_width=True)
                
                st.link_button("🌐 Ver Nota en Autoblog", auto.Link)
            
            st.markdown("<div class='vehicle-card'></div>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("Administración")
    if st.button("🔄 Refrescar Catálogo"):
        st.cache_data.clear()
        st.rerun()