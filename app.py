import streamlit as st
import sqlite3
import datetime
# --- Configuración ---
st.set_page_config(page_title="Registro Equipos NFC", layout="centered")
# --- Conexión y creación de tablas SQLite ---
conn = sqlite3.connect("eventos.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS eventos (
   codigo TEXT PRIMARY KEY,
   nombre TEXT,
   fecha TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS barras (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   evento_codigo TEXT,
   nombre TEXT,
   FOREIGN KEY(evento_codigo) REFERENCES eventos(codigo)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipos (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   evento_codigo TEXT,
   barra TEXT,
   tipo TEXT,
   serial TEXT,
   timestamp TEXT,
   FOREIGN KEY(evento_codigo) REFERENCES eventos(codigo)
)
""")
conn.commit()
# --- Funciones ---
def cargar_eventos():
   return cursor.execute("SELECT codigo, nombre FROM eventos").fetchall()
def cargar_barras(evento_codigo):
   return cursor.execute("SELECT nombre FROM barras WHERE evento_codigo = ?", (evento_codigo,)).fetchall()
def cargar_equipos(evento_codigo, barra):
   return cursor.execute(
       "SELECT tipo, COUNT(*) FROM equipos WHERE evento_codigo = ? AND barra = ? GROUP BY tipo",
       (evento_codigo, barra)
   ).fetchall()
def existe_tag(evento_codigo, serial):
   return cursor.execute(
       "SELECT 1 FROM equipos WHERE evento_codigo = ? AND serial = ?", (evento_codigo, serial)
   ).fetchone() is not None
# --- Variables de sesión ---
if "evento_codigo" not in st.session_state:
   st.session_state.evento_codigo = None
if "registrando_equipo" not in st.session_state:
   st.session_state.registrando_equipo = False
if "barra_actual" not in st.session_state:
   st.session_state.barra_actual = None
if "tipo_actual" not in st.session_state:
   st.session_state.tipo_actual = None
if "contador_tags" not in st.session_state:
   st.session_state.contador_tags = 0
if "tags_a_registrar" not in st.session_state:
   st.session_state.tags_a_registrar = 0
# --- Interfaz ---
st.title("📲 Registro de Equipos NFC")
# Selección de evento
eventos = cargar_eventos()
if not eventos:
   st.warning("No hay eventos cargados en la base de datos.")
   st.stop()
evento_sel = st.selectbox("Selecciona un evento", [f"{c} - {n}" for c, n in eventos])
codigo, nombre_evento = evento_sel.split(" - ", maxsplit=1)
st.session_state.evento_codigo = codigo
# Mostrar barras para el evento
barras = cargar_barras(codigo)
if not barras:
   st.warning("No hay barras definidas para este evento.")
   st.stop()
barra_sel = st.selectbox("Selecciona una barra", [b[0] for b in barras])
# Mostrar equipos declarados (simulación: pide cantidad por tipo, puedes adaptar según tu base)
st.header(f"Barras y Equipos para el evento {nombre_evento}")
tipos_posibles = ["frío", "sonido", "iluminación", "mostradores"]
# Para la barra seleccionada, pedimos cantidades a declarar por tipo (excepto MOSTRADORES)
cantidades = {}
st.subheader(f"Introduce cantidad de equipos por tipo para la barra {barra_sel}:")
for tipo in tipos_posibles:
   if tipo == "mostradores":
       st.info("No se registran tags para tipo MOSTRADORES.")
       continue
   cantidad = st.number_input(f"{tipo.capitalize()}", min_value=0, step=1, key=f"{barra_sel}_{tipo}")
   cantidades[tipo] = cantidad
# Botón para iniciar registro
if not st.session_state.registrando_equipo:
   # Selección para comenzar registro
   tipo_sel = st.selectbox("Selecciona tipo de equipo para registrar tags", [t for t in cantidades if cantidades[t] > 0])
   cantidad_a_registrar = cantidades.get(tipo_sel, 0)
   if cantidad_a_registrar > 0:
       if st.button(f"Comenzar registro de {cantidad_a_registrar} tags para {tipo_sel} en barra {barra_sel}"):
           st.session_state.registrando_equipo = True
           st.session_state.barra_actual = barra_sel
           st.session_state.tipo_actual = tipo_sel
           st.session_state.contador_tags = 0
           st.session_state.tags_a_registrar = cantidad_a_registrar
           st.experimental_rerun()
else:
   st.subheader(f"Registrando tags para tipo '{st.session_state.tipo_actual}' en barra '{st.session_state.barra_actual}'")
   tag_input = st.text_input(f"Introduce tag #{st.session_state.contador_tags + 1}")
   if tag_input:
       if st.session_state.tipo_actual == "mostradores":
           st.warning("No se debe registrar tags para MOSTRADORES.")
       else:
           if existe_tag(st.session_state.evento_codigo, tag_input.strip()):
               st.error("Este tag ya ha sido registrado.")
           else:
               cursor.execute("""
                   INSERT INTO equipos (evento_codigo, barra, tipo, serial, timestamp)
                   VALUES (?, ?, ?, ?, ?)
               """, (
                   st.session_state.evento_codigo,
                   st.session_state.barra_actual,
                   st.session_state.tipo_actual,
                   tag_input.strip(),
                   datetime.datetime.now().isoformat()
               ))
               conn.commit()
               st.success(f"Tag #{st.session_state.contador_tags + 1} registrado correctamente.")
               st.session_state.contador_tags += 1
               if st.session_state.contador_tags >= st.session_state.tags_a_registrar:
                   st.success("✅ Registro completo para este tipo y barra.")
                   st.session_state.registrando_equipo = False
                   st.session_state.barra_actual = None
                   st.session_state.tipo_actual = None
                   st.session_state.contador_tags = 0
                   st.session_state.tags_a_registrar = 0
               st.experimental_rerun()
   if st.button("Cancelar registro"):
       st.session_state.registrando_equipo = False
       st.session_state.barra_actual = None
       st.session_state.tipo_actual = None
       st.session_state.contador_tags = 0
       st.session_state.tags_a_registrar = 0
       st.experimental_rerun()
