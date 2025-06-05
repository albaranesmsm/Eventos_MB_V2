import streamlit as st
import pandas as pd
import datetime
import sqlite3
st.set_page_config(page_title="Control de Equipos NFC", layout="centered")
# Conexión a base de datos SQLite
conn = sqlite3.connect("eventos.db", check_same_thread=False)
cursor = conn.cursor()
# Crear tablas si no existen
cursor.execute("""
CREATE TABLE IF NOT EXISTS eventos (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   nombre TEXT,
   codigo TEXT UNIQUE,
   mostradores INTEGER,
   botelleros INTEGER,
   vitrinas INTEGER,
   enfriadores INTEGER,
   kits INTEGER,
   num_barras INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS barras (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   evento_codigo TEXT,
   nombre TEXT,
   mostradores INTEGER,
   botelleros INTEGER,
   vitrinas INTEGER,
   enfriadores INTEGER,
   kits_portatiles INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipos (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   evento_codigo TEXT,
   barra TEXT,
   tipo TEXT,
   serial TEXT UNIQUE,
   timestamp TEXT
)
""")
conn.commit()
# Estado inicial
if "evento_codigo" not in st.session_state:
   st.session_state.evento_codigo = None
# Cargar evento existente
st.title("🧊 Control de Equipos de Frío por NFC")
eventos = cursor.execute("SELECT codigo, nombre FROM eventos").fetchall()
eventos_dict = {f"{n} ({c})": c for c, n in eventos}
opciones = list(eventos_dict.keys())
if opciones:
   seleccion = st.selectbox("📂 Cargar evento existente o crear uno nuevo", ["Nuevo evento"] + opciones)
else:
   seleccion = "Nuevo evento"
# Crear nuevo evento
if seleccion == "Nuevo evento":
   st.header("🔧 Configuración del Evento")
   nombre_evento = st.text_input("Nombre del evento")
   codigo_evento = st.text_input("Código del evento único")
   num_mostradores = st.number_input("Total de Mostradores", min_value=0)
   num_botelleros = st.number_input("Total de Botelleros", min_value=0)
   num_vitrinas = st.number_input("Total de Vitrinas", min_value=0)
   num_enfriadores = st.number_input("Total de Enfriadores", min_value=0)
   num_kits = st.number_input("Total de Kits portátiles", min_value=0)
   num_barras = st.number_input("Número total de barras", min_value=1)
   if st.button("✅ Crear evento"):
       try:
           cursor.execute("""
               INSERT INTO eventos (nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           """, (nombre_evento, codigo_evento, num_mostradores, num_botelleros, num_vitrinas, num_enfriadores, num_kits, num_barras))
           conn.commit()
           st.session_state.evento_codigo = codigo_evento
           st.rerun()
       except sqlite3.IntegrityError:
           st.error("❌ Ya existe un evento con ese código.")
else:
   st.session_state.evento_codigo = eventos_dict[seleccion]
# Si hay evento cargado
if st.session_state.evento_codigo:
   codigo = st.session_state.evento_codigo
   evento = cursor.execute("SELECT * FROM eventos WHERE codigo = ?", (codigo,)).fetchone()
   st.success(f"Evento cargado: {evento[1]} (Código: {evento[2]})")
   with st.expander("✏️ Editar datos del evento"):
       nuevo_nombre = st.text_input("Nombre del evento", value=evento[1])
       nuevo_mostradores = st.number_input("Total de Mostradores", min_value=0, value=evento[3])
       nuevo_botelleros = st.number_input("Total de Botelleros", min_value=0, value=evento[4])
       nuevo_vitrinas = st.number_input("Total de Vitrinas", min_value=0, value=evento[5])
       nuevo_enfriadores = st.number_input("Total de Enfriadores", min_value=0, value=evento[6])
       nuevo_kits = st.number_input("Total de Kits portátiles", min_value=0, value=evento[7])
       nuevo_barras = st.number_input("Número total de barras", min_value=1, value=evento[8])
       if st.button("💾 Guardar cambios en el evento"):
           cursor.execute("""
               UPDATE eventos SET nombre=?, mostradores=?, botelleros=?, vitrinas=?, enfriadores=?, kits=?, num_barras=?
               WHERE codigo=?
           """, (nuevo_nombre, nuevo_mostradores, nuevo_botelleros, nuevo_vitrinas, nuevo_enfriadores, nuevo_kits, nuevo_barras, codigo))
           conn.commit()
           st.success("✅ Datos del evento actualizados")
           st.rerun()
   # Continuación del registro de barras
   total_barras = nuevo_barras
   barras_actuales = cursor.execute("SELECT * FROM barras WHERE evento_codigo = ?", (codigo,)).fetchall()
   idx = len(barras_actuales)
   if idx < total_barras:
       st.header(f"📍 Barra {idx + 1} de {total_barras}")
       nombre_barra = st.text_input("Nombre o ubicación de esta barra")
       mostradores = st.number_input("Mostradores", min_value=0)
       botelleros = st.number_input("Nº Botelleros", min_value=0)
       vitrinas = st.number_input("Nº Vitrinas", min_value=0)
       enfriadores = st.number_input("Nº Enfriadores", min_value=0)
       kits = st.number_input("Nº Kits portátiles", min_value=0)
       def leer_tags(tipo, cantidad):
           st.subheader(f"{tipo}s")
           equipos_barra = []
           for i in range(int(cantidad)):
               tag = st.text_input(f"{tipo} {i+1}", key=f"{tipo}_{idx}_{i}")
               if tag:
                   existe = cursor.execute("SELECT 1 FROM equipos WHERE serial = ?", (tag.strip(),)).fetchone()
                   if existe:
                       st.warning(f"{tipo} {i+1}: Este código ya fue registrado")
                   else:
                       equipos_barra.append((codigo, nombre_barra, tipo, tag.strip(), datetime.datetime.now().isoformat()))
           return equipos_barra
       equipos_nuevos = []
       equipos_nuevos += leer_tags("Botellero", botelleros)
       equipos_nuevos += leer_tags("Vitrina", vitrinas)
       equipos_nuevos += leer_tags("Enfriador", enfriadores)
       equipos_nuevos += leer_tags("Kit portátil", kits)
       if st.button("💾 Guardar barra y continuar"):
           cursor.execute("""
               INSERT INTO barras (evento_codigo, nombre, mostradores, botelleros, vitrinas, enfriadores, kits_portatiles)
               VALUES (?, ?, ?, ?, ?, ?, ?)
           """, (codigo, nombre_barra, mostradores, botelleros, vitrinas, enfriadores, kits))
           cursor.executemany("""
               INSERT INTO equipos (evento_codigo, barra, tipo, serial, timestamp)
               VALUES (?, ?, ?, ?, ?)
           """, equipos_nuevos)
           conn.commit()
           st.success("✅ Barra guardada")
           st.rerun()
   else:
       st.success("🎉 Registro de todas las barras completado")
       df_barras = pd.read_sql_query("SELECT * FROM barras WHERE evento_codigo = ?", conn, params=(codigo,))
       df_equipos = pd.read_sql_query("SELECT * FROM equipos WHERE evento_codigo = ?", conn, params=(codigo,))
       st.subheader("📊 Resumen por barra")
       st.dataframe(df_barras)
       st.subheader("📦 Equipos registrados")
       st.dataframe(df_equipos)
       @st.cache_data
       def to_excel(df1, df2):
           from io import BytesIO
           output = BytesIO()
           with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
               df1.to_excel(writer, sheet_name='Resumen por barra', index=False)
               df2.to_excel(writer, sheet_name='Equipos por tag', index=False)
           return output.getvalue()
       excel_data = to_excel(df_barras, df_equipos)
       st.download_button("📥 Descargar Excel completo", data=excel_data,
                          file_name=f"{codigo}_registro_evento.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
