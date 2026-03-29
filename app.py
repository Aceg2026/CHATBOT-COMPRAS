import streamlit as st
import pandas as pd
from thefuzz import process

# 1. Configuración visual de la página
st.set_page_config(page_title="Asistente de Compras", page_icon="🛒", layout="centered")
st.title("🛒 Chatbot de Historial de Compras")

# LINK DE TU GOOGLE SHEET (Reemplazá esto por tu link publicado como CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWOB_6N4gok52hpQG5yjMJjXSlQt4wUsRDoydUf5MZtY9nXZ_A6GHDcUta9VA1vtB64d6pPh7FIRvX/pub?output=csv"

# 2. Cargar los datos desde Google Sheets en tiempo real
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        st.error("Error al cargar la base de datos. Verificá el link de Google Sheets.")
        return pd.DataFrame()

df = load_data()

# 3. La inteligencia del buscador (¡MEJORADA!)
def buscar_historial(query, df):
    if df.empty:
        return "La base de datos está vacía o no se pudo conectar."
    
    # Limpiar filas vacías y obtener nombres únicos
    df_clean = df.dropna(subset=['Descripcion'])
    productos_unicos = df_clean['Descripcion'].unique()
    
    # Búsqueda difusa: extraemos las 3 mejores coincidencias en lugar de solo 1
    mejores_coincidencias = process.extract(query, productos_unicos, limit=3)
    
    # Filtramos solo las que tengan un puntaje de similitud aceptable (mayor a 55)
    coincidencias_validas = [match[0] for match in mejores_coincidencias if match[1] >= 55]
    
    if not coincidencias_validas:
        return f"Mmm, no encontré nada parecido a '{query}'. ¿Podrías intentar con otra palabra clave?"
    
    # Armar el texto visual de respuesta para cada coincidencia encontrada
    respuesta = f"Encontré estas opciones para **'{query}'**:\n\n"
    
    for producto in coincidencias_validas:
        respuesta += f"### 📦 {producto}\n"
        
        # Filtrar y ordenar
        resultados = df_clean[df_clean['Descripcion'] == producto]
        ultimas_compras = resultados.sort_values(by='Fecha', ascending=False).head(3)
        
        for _, row in ultimas_compras.iterrows():
            fecha_str = row['Fecha'].strftime('%d/%m/%Y')
            precio = row['Precio Unitario']
            cant = row['Cantidad']
            prov = row['Nombre']
            respuesta += f"- 📅 **{fecha_str}** | Cant: {cant} | 💵 **USD {precio}** | 🏭 {prov}\n"
        
        respuesta += "\n---\n" # Línea separadora entre productos
    
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
