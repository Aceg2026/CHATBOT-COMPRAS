import streamlit as st
import pandas as pd
from thefuzz import process

# 1. Configuración visual de la página
st.set_page_config(page_title="Asistente de Compras", page_icon="🛒", layout="centered")
st.title("🛒 Chatbot de Historial de Compras")

# LINK DE TU GOOGLE SHEET (Reemplazá esto por tu link publicado como CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWOB_6N4gok52hpQG5yjMJjXSlQt4wUsRDoydUf5MZtY9nXZ_A6GHDcUta9VA1vtB64d6pPh7FIRvX/pub?output=csv"

# 2. Cargar los datos desde Google Sheets en tiempo real
@st.cache_data(ttl=600) # El bot refresca la info cada 10 minutos por si agregaste datos nuevos
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        st.error("Error al cargar la base de datos. Verificá el link de Google Sheets.")
        return pd.DataFrame()

df = load_data()

# 3. La inteligencia del buscador
def buscar_historial(query, df):
    if df.empty:
        return "La base de datos está vacía o no se pudo conectar."
    
    # Limpiar filas vacías y obtener nombres únicos
    df_clean = df.dropna(subset=['Descripcion'])
    productos_unicos = df_clean['Descripcion'].unique()
    
    # Búsqueda difusa (Fuzzy Matching)
    mejor_coincidencia, score = process.extractOne(query, productos_unicos)
    
    if score < 60:
        return f"Mmm, no encontré nada parecido a '{query}'. ¿Podrías intentar con otra palabra clave?"
    
    # Filtrar y ordenar
    resultados = df_clean[df_clean['Descripcion'] == mejor_coincidencia]
    ultimas_compras = resultados.sort_values(by='Fecha', ascending=False).head(3)
    
    # Armar el texto visual de respuesta
    respuesta = f"**Producto encontrado:** {mejor_coincidencia} \n\n**Últimas compras:**\n\n"
    for _, row in ultimas_compras.iterrows():
        fecha_str = row['Fecha'].strftime('%d/%m/%Y')
        precio = row['Precio Unitario']
        cant = row['Cantidad']
        prov = row['Nombre']
        respuesta += f"📅 **{fecha_str}** | 📦 Cant: {cant} | 💵 **USD {precio}** | 🏭 {prov}\n"
    
    return respuesta

# 4. Diseño del Chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

if prompt := st.chat_input("Buscá un producto (ej. Sillon Apolo)..."):
    # Guardar y mostrar lo que escribió el usuario
    st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Buscar y responder
    respuesta_bot = buscar_historial(prompt, df)
    
    with st.chat_message("assistant"):
        st.markdown(respuesta_bot)
    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta_bot})
