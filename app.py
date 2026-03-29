import streamlit as st
import pandas as pd
from thefuzz import process

# 1. Configuración visual de la página (Ancha y con ícono)
st.set_page_config(page_title="Historial de Compras", page_icon="🛍️", layout="centered")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    .titulo-principal {
        text-align: center;
        color: #1E3A8A;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .subtitulo {
        text-align: center;
        color: #6B7280;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='titulo-principal'>🛍️ Asistente de Compras</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitulo'>Consultá tu historial de precios y proveedores al instante.</p>", unsafe_allow_html=True)
st.divider()

# 2. Cargar los datos
# REEMPLAZÁ ESTE LINK POR EL TUYO DE GOOGLE SHEETS
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWOB_6N4gok52hpQG5yjMJjXSlQt4wUsRDoydUf5MZtY9nXZ_A6GHDcUta9VA1vtB64d6pPh7FIRvX/pub?output=csv"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# 3. La inteligencia del buscador con diseño mejorado
def buscar_historial(query, df):
    if df.empty:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return
    
    df_clean = df.dropna(subset=['Descripcion'])
    productos_unicos = df_clean['Descripcion'].unique()
    
    # Extraemos las 3 mejores coincidencias
    mejores_coincidencias = process.extract(query, productos_unicos, limit=3)
    coincidencias_validas = [match[0] for match in mejores_coincidencias if match[1] >= 55]
    
    if not coincidencias_validas:
        st.warning(f"🤔 No encontré nada parecido a **'{query}'**. ¿Podrías intentar con otro nombre?")
        return
    
    st.success(f"🔎 Encontré estas opciones para **'{query}'**:")
    
    # Crear un diseño de "Acordeón" para cada producto encontrado
    for producto in coincidencias_validas:
        with st.expander(f"📦 {producto}"):
            resultados = df_clean[df_clean['Descripcion'] == producto]
            ultimas_compras = resultados.sort_values(by='Fecha', ascending=False).head(3)
            
            # Mostrar cada compra en columnas para que se vea más ordenado
            for i, row in ultimas_compras.iterrows():
                fecha_str = row['Fecha'].strftime('%d/%m/%Y')
                
                # Crear 4 columnas visuales
                col1, col2, col3, col4 = st.columns([1.5, 1, 1, 2])
                
                with col1:
                    st.caption("📅 Fecha")
                    st.write(fecha_str)
                with col2:
                    st.caption("⚖️ Cantidad")
                    st.write(f"**{row['Cantidad']}**")
                with col3:
                    st.caption("💵 Precio Unit.")
                    st.write(f"**${row['Precio Unitario']}**")
                with col4:
                    st.caption("🏭 Proveedor")
                    st.write(row['Nombre'])
                
                # Una línea suave para separar compras del mismo producto
                st.markdown("<hr style='margin: 10px 0px; border-top: 1px dashed #E5E7EB;'>", unsafe_allow_html=True)

# 4. Diseño de la Interfaz de Chat
# Inicializar el historial de chat
if "mensajes" not in st.session_state:
    # Mensaje de bienvenida inicial
    st.session_state.mensajes = [{"rol": "assistant", "contenido": "¡Hola! Decime qué producto buscás y te busco las últimas 3 compras."}]

# Mostrar el historial
for mensaje in st.session_state.mensajes:
    if mensaje["rol"] == "assistant":
        # Usamos markdown para el asistente, pero la función de búsqueda la ejecutamos por separado
        with st.chat_message("assistant", avatar="🤖"):
            if mensaje["contenido"] != "":
                 st.markdown(mensaje["contenido"])
    else:
        with st.chat_message("user", avatar="👤"):
            st.markdown(mensaje["contenido"])

# Input del usuario
if prompt := st.chat_input("Escribí el nombre de un producto..."):
    # Agregar y mostrar el mensaje del usuario
    st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # El asistente responde
    with st.chat_message("assistant", avatar="🤖"):
        buscar_historial(prompt, df)
    
    # Guardamos un mensaje vacío en el historial del asistente para mantener el orden, 
    # ya que Streamlit dibuja los expansores directamente en la pantalla
    st.session_state.mensajes.append({"rol": "assistant", "contenido": ""})
