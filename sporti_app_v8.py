import streamlit as st
import sqlite3
from datetime import datetime
import random
import pandas as pd
import webbrowser

# Conexión con la base de datos SQLite
conn = sqlite3.connect('sporti_data.db')
c = conn.cursor()

# Crear tablas si no existen
c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
    correo TEXT PRIMARY KEY,
    nombre TEXT, clave TEXT, sexo TEXT, edad INTEGER, altura INTEGER,
    tipo_corredor TEXT, foto TEXT, estilo_musical TEXT, vo2_max INTEGER)""")

c.execute("""CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, correo TEXT, fecha TEXT,
    entrenamiento TEXT, distancia INTEGER, bpm_actual INTEGER,
    fatiga TEXT, playlist TEXT, mensaje TEXT)""")

# Interfaz
st.title("🎧 SPORTI v5 – App avanzada con persistencia")

# Funciones
def login(correo, clave):
    c.execute("SELECT * FROM usuarios WHERE correo=? AND clave=?", (correo, clave))
    return c.fetchone()

def registrar_usuario(correo, nombre, clave, sexo, edad, altura, tipo_corredor, foto, estilo_musical, vo2_max):
    c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (correo, nombre, clave, sexo, edad, altura, tipo_corredor, foto, estilo_musical, vo2_max))
    conn.commit()

# Estado de sesión
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "bpm_actual" not in st.session_state:
    st.session_state.bpm_actual = None
if "fatiga" not in st.session_state:
    st.session_state.fatiga = None
if "fase" not in st.session_state:
    st.session_state.fase = "inicio"

menu = st.sidebar.selectbox("Menú", ["Iniciar sesión", "Registrarse", "Admin"])

if st.session_state.logged_in:
    usuario = st.session_state.usuario_actual
    nombre_usuario = usuario[1]
    correo = usuario[0]
    sexo = usuario[3]
    edad = usuario[4]
    altura = usuario[5]
    tipo_corredor = usuario[6]
    foto = usuario[7]
    estilo_musical = usuario[8]
    vo2_max = usuario[9]

    st.sidebar.subheader("🎯 Usuario: " + nombre_usuario)
    st.sidebar.write("📧 Correo:", correo)
    st.sidebar.write("♀ Sexo:", sexo)
    st.sidebar.write("🎂 Edad:", edad)
    st.sidebar.write("📏 Altura:", altura)
    st.sidebar.write("🏃 Tipo corredor:", tipo_corredor)
    st.sidebar.write("🎶 Estilo musical:", estilo_musical)
    st.sidebar.write("🧬 VO₂ max:", vo2_max)

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.usuario_actual = None
        st.rerun()

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

        if tipo_entrenamiento == "Zona 2":
            mensaje = ("Zona 2 es ideal para aumentar tu capacidad aeróbica sin elevar demasiado el VO₂ max. "
                       "La música puede ayudarte a mantener un ritmo constante y relajado, lo que favorece la resistencia a largo plazo.")
        else:
            mensaje = "Este tipo de entrenamiento aún no tiene una recomendación personalizada."

        st.info(mensaje)

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
        st.session_state.resultado_mensaje = mensaje
        st.session_state.resultado_url = url
        st.session_state.fase = "playlist"
    else:
        st.warning("No se encontró una playlist recomendada para esta combinación.")
     # Esto va FUERA del else, con la misma indentación del if principal
    if st.session_state.fase == "playlist":
        st.success(f"Playlist recomendada: [{st.session_state.resultado_playlist}]({st.session_state.resultado_url})")
        st.markdown(
    f'<a href="{st.session_state.resultado_url}" target="_blank">'
    f'<button style="background-color: #1DB954; color: white; padding: 10px; border: none; border-radius: 5px;">'
    f'🎵 Ir a Playlist en Spotify</button></a>',
    unsafe_allow_html=True
)       
if st.button("✅ Ya comencé, continuar"):
    st.session_state.fase = "ejecutando"       
    if st.session_state.fase == "ejecutando":
        st.success("Sesión musical en curso. ¡Disfruta tu entrenamiento!")
        if st.button("⏹ Finalizar sesión"):
            c.execute("""INSERT INTO sesiones (correo, fecha, entrenamiento, distancia, bpm_actual, fatiga, playlist, mensaje)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (correo, datetime.now().strftime("%Y-%m-%d %H:%M"), tipo_entrenamiento, distancia,
                       bpm_actual, fatiga, st.session_state.resultado_playlist, st.session_state.resultado_mensaje))
            conn.commit()
            st.success("Sesión guardada exitosamente.")
            st.session_state.fase = "inicio"

elif menu == "Iniciar sesión":
    correo = st.text_input("Correo electrónico")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        usuario = login(correo, clave)
        if usuario:
            st.session_state.usuario_actual = usuario
            st.session_state.logged_in = True
            st.success(f"Bienvenido {usuario[1]}!")
            st.rerun()
        else:
            st.error("Correo o contraseña incorrectos.")

elif menu == "Registrarse":
    nombre = st.text_input("Nombre completo")
    correo = st.text_input("Correo electrónico")
    clave = st.text_input("Contraseña", type="password")
    sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
    edad = st.number_input("Edad", 15, 100, 25)
    altura = st.number_input("Altura (cm)", 140, 210, 170)
    tipo_corredor = st.selectbox("Tipo corredor", ["Principiante", "Intermedio", "Avanzado"])
    foto = st.text_input("URL de tu foto (opcional)")
    estilo_musical = st.selectbox("Estilo musical favorito", ["Rock", "Pop", "Electrónica", "Metal", "Hip-hop"])
    vo2_max = st.number_input("VO₂ max estimado", 30, 70, 45)

    if st.button("Registrar"):
        registrar_usuario(correo, nombre, clave, sexo, edad, altura, tipo_corredor, foto, estilo_musical, vo2_max)
        st.success("Registro exitoso. Ahora puedes iniciar sesión.")

elif menu == "Admin":
    clave_admin = st.sidebar.text_input("Clave de admin", type="password")
    if clave_admin == "admin123":
        st.header("Vista de Administrador")
        usuarios = pd.read_sql("SELECT * FROM usuarios", conn)
        sesiones = pd.read_sql("SELECT * FROM sesiones", conn)
        st.write("Usuarios registrados:", usuarios)
        st.write("Historial de sesiones:", sesiones)

conn.close()
