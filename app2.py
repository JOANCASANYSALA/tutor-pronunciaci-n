import streamlit as st
import tempfile
from azure_pronunciation import evaluar_pronunciacion
import numpy as np
import json
import os
from datetime import datetime
import pandas as pd

# 🎨 Configuración de página
st.set_page_config(
    page_title="Tutor de pronunciación en inglés",
    page_icon="🎧",
    layout="centered"
)

st.title("Tutor de pronunciación en inglés")
st.markdown("""
Practica tu pronunciación con un **plan progresivo de 6 niveles (0–5)** 
y guarda tu progreso con evaluaciones automáticas de **Azure Speech**.
""")

#Definición de niveles
niveles = {
    1: ["Hello!", "Good morning.", "How are you?"],
    2: ["I like playing football.", "She is reading a book."],
    3: ["The weather today is beautiful.", "I’m learning English pronunciation."],
    4: ["If I had known, I would have come earlier.", "They were watching a movie when I arrived."],
    5: ["Despite the rain, the concert continued until midnight.", "She speaks English fluently with a British accent."]
}

#Identificación de usuario
usuario = st.text_input("👤 Escribe tu nombre o identificador de usuario:")

if usuario:
    st.success(f"Bienvenido, {usuario} ")
else:
    st.warning("Por favor, introduce tu nombre para registrar tu progreso.")
    st.stop()

#Selección de nivel y frase
nivel = st.slider("Selecciona tu nivel de práctica (0 - 5):", 0, 5, 0)

if nivel == 0:
    st.info("Nivel 0: Escribe tu propia frase personalizada para practicar libremente.")
    frase = st.text_input("Introduce tu frase en inglés:", "")
    if not frase:
        st.warning("Por favor, escribe una frase para practicar.")
        st.stop()
else:
    frase = st.selectbox("Elige una frase del nivel seleccionado:", niveles[nivel])

# 🎙️ Subida de archivo
st.subheader("Sube tu pronunciación")
audio_file = st.file_uploader("Sube tu grabación (.wav)", type=["wav"])

#Archivo historial
HISTORIAL_PATH = "historial.json"

# Función auxiliar: guardar resultado en historial
def guardar_en_historial(usuario, nivel, frase, resultados):
    nuevo_registro = {
        "usuario": usuario,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nivel": nivel,
        "frase": frase,
        "Pronunciación": resultados["PronunciationScore"],
        "Precisión": resultados["AccuracyScore"],
        "Fluidez": resultados["FluencyScore"],
        "Completitud": resultados["CompletenessScore"]
    }

    if os.path.exists(HISTORIAL_PATH):
        with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(nuevo_registro)
    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Variable que guardará la ruta final del audio a evaluar
temp_audio_path = None

# Si el usuario subió un archivo, usamos ese archivo para evaluar
if audio_file is not None:
    # Guardamos el archivo subido como temporal para que sea compatible con evaluar_pronunciacion
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        tmpfile.write(audio_file.read())
        temp_audio_path = tmpfile.name
    st.audio(temp_audio_path, format="audio/wav")

# Evaluación del audio
if temp_audio_path is not None and st.button("Evaluar pronunciación"):
    with st.spinner("Evaluando pronunciación..."):
        try:
            resultados = evaluar_pronunciacion(temp_audio_path, frase)
            st.success("Evaluación completada")

            # Mostrar resultados
            st.header("Resultados globales")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Pronunciación", f"{resultados['PronunciationScore']:.1f}")
            col2.metric("Precisión", f"{resultados['AccuracyScore']:.1f}")
            col3.metric("Fluidez", f"{resultados['FluencyScore']:.1f}")
            col4.metric("Completitud", f"{resultados['CompletenessScore']:.1f}")

            # Guardar historial
            guardar_en_historial(usuario, nivel, frase, resultados)

            # Resultados por palabra
            st.subheader("Resultados por palabra")
            for palabra in resultados["Words"]:
                barra = int(palabra["Score"])
                st.progress(barra / 100)
                st.write(f"**{palabra['Word']}** → {palabra['Score']:.1f}")

            #Sugerencias automáticas
            sugerencias = []

            if resultados["FluencyScore"] < 70:
                sugerencias.append("Habla con un ritmo más natural, evitando pausas largas.")
            if resultados["AccuracyScore"] < 70:
                sugerencias.append("Escucha atentamente la pronunciación nativa y repite.")
            if resultados["PronunciationScore"] < 75:
                sugerencias.append("Presta atención a los sonidos vocálicos difíciles.")
            if any(w["Score"] < 60 for w in resultados["Words"]):
                palabra_peor = min(resultados["Words"], key=lambda w: w["Score"])["Word"]
                sugerencias.append(f"Practica la pronunciación de la palabra **'{palabra_peor}'**.")

            if resultados["CompletenessScore"] < 80:
                sugerencias.append("Asegúrate de pronunciar todas las palabras completas.")

            if not sugerencias:
                sugerencias = ["¡Excelente pronunciación! Estás listo para subir de nivel."]

            st.subheader("💬 Sugerencias de mejora")
            for s in sugerencias:
                st.markdown(f"- {s}")

            # Progreso
            if nivel > 0 and resultados["PronunciationScore"] > 80 and nivel < 5:
                st.success(f"¡Muy bien, {usuario}! Puedes pasar al **nivel {nivel + 1}** ")
            elif nivel == 5 and resultados["PronunciationScore"] > 80:
                st.balloons()
                st.success("¡Has completado todos los niveles! Felicidades ")

        except Exception as e:
            st.error(f"Ocurrió un error al evaluar: {e}")

# Ver historial del usuario
st.subheader("Historial de progreso")

if os.path.exists(HISTORIAL_PATH):
    with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        user_data = [d for d in data if d["usuario"] == usuario]

        if user_data:
            df = pd.DataFrame(user_data)
            st.dataframe(df)
            st.line_chart(df[["Pronunciación", "Fluidez", "Precisión"]].reset_index(drop=True))
        else:
            st.info("Aún no tienes evaluaciones registradas.")
else:
    st.info("Aún no hay historial disponible.")
