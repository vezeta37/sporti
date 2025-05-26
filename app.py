
import streamlit as st
import sqlite3
from datetime import datetime
import random
import pandas as pd
import webbrowser

# Conexión con la base de datos SQLite
conn = sqlite3.connect('sporti_data.db')
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, correo TEXT, fecha TEXT,
    entrenamiento TEXT, distancia INTEGER, bpm_actual INTEGER,
    fatiga TEXT, playlist TEXT, mensaje TEXT)""")

# Simulación de usuario logeado para pruebas
st.session_state.logged_in = True
st.session_state.usuario_actual = ["demo@correo.cl", "Usuario Demo", "", "", 35, 175, "Intermedio", "", "Rock", 48]

# Estado inicial
if "fase" not in st.session_state:
    st.session_state.fase = "inicio"
if "bpm_actual" not in st.session_state:
    st.session_state.bpm_actual = None
if "fatiga" not in st.session_state:
    st.session_state.fatiga = None

usuario = st.session_state.usuario_actual
correo = usuario[0]
estilo_musical = usuario[8]
vo2_max = usuario[9]

st.title("🎧 SPORTI en la Nube – Demo")
st.subheader("🏃 Simulador de Entrenamiento")

if st.session_state.fase == "inicio":
    if st.button("🔄 Sincronizar con Google Fit (simulado)"):
        st.session_state.bpm_actual = random.randint(115, 135)
        st.session_state.fatiga = random.choice(["Baja", "Media", "Alta"])
        st.success("Datos sincronizados correctamente.")
        st.session_state.fase = "entrenamiento"

if st.session_state.fase == "entrenamiento":
    bpm_actual = st.session_state.bpm_actual
    fatiga = st.session_state.fatiga

    st.markdown(f"**BPM actual:** {bpm_actual}")
    st.markdown(f"**Fatiga reportada:** {fatiga}")

    tipo_entrenamiento = st.selectbox("Tipo de entrenamiento", ["Zona 2", "Tempo", "Intervalos", "Fondo largo", "Recuperación"])
    distancia = st.slider("Kilómetros", 1, 20, 5)

    st.markdown("**BPM esperado:** 119 - 130")
    st.markdown(f"**VO₂ max actual:** {vo2_max}")

    st.info("Ejemplo de recomendación musical basada en entrenamiento y fatiga")

    if st.button("🎶 Buscar Playlist"):
        combinaciones = pd.read_excel("Sporti_Combinaciones_Musicales_Final.xlsx")
        filtro = combinaciones[
            (combinaciones["zona"] == tipo_entrenamiento) &
            (combinaciones["musica"] == estilo_musical) &
            (combinaciones["fatiga"] == fatiga)
        ]

        if not filtro.empty:
            playlist = filtro.iloc[0]["playlist"]
            url = filtro.iloc[0]["url"]
            mensaje = filtro.iloc[0]["mensaje"]
            st.session_state.resultado_playlist = playlist
            st.session_state.resultado_url = url
            st.session_state.resultado_mensaje = mensaje
            st.session_state.fase = "playlist"
        else:
            st.warning("No se encontró una playlist recomendada para esta combinación.")

if st.session_state.fase == "playlist":
    st.success(f"Playlist recomendada: [{st.session_state.resultado_playlist}]({st.session_state.resultado_url})")
    st.markdown(f"[▶️ Ir a Spotify]({st.session_state.resultado_url})", unsafe_allow_html=True)
    if st.button("🟢 Ya comencé, continuar"):
        st.session_state.fase = "ejecutando"
    if st.button("🔙 Volver"):
        st.session_state.fase = "entrenamiento"

if st.session_state.fase == "ejecutando":
    st.success("🎵 Sesión musical en curso.")
    if st.button("⏹ Finalizar sesión"):
        c.execute("""INSERT INTO sesiones (correo, fecha, entrenamiento, distancia, bpm_actual, fatiga, playlist, mensaje)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (correo, datetime.now().strftime("%Y-%m-%d %H:%M"), tipo_entrenamiento, distancia,
                   bpm_actual, fatiga, st.session_state.resultado_playlist, st.session_state.resultado_mensaje))
        conn.commit()
        st.success("Sesión guardada exitosamente.")
        st.session_state.fase = "inicio"
