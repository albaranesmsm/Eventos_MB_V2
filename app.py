import streamlit as st
import pandas as pd
import sqlite3
import datetime
st.set_page_config(page_title="Control de Equipos NFC", layout="centered")
# Conexión a base de datos
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
# Selección de evento
st.title("🧊 Control de Equipos de Frío por NFC")
eventos = cursor.execute("SELECT codigo, nombre FROM eventos").fetchall()
eventos_dict = {f"{n} ({c})": c for c, n in eventos}
opciones = list(eventos_dict.keys())
seleccion = st.selectbox("📁 Selecciona un evento existente o crea uno nuevo", ["Nuevo evento"] + opciones)
if seleccion == "Nuevo evento":
   st.header("🔧 Nuevo evento")
   nombre_evento = st.text_input("Nombre del evento")
   codigo_evento = st.text_input("Código único del evento")
   num_mostradores = st.number_input("Mostradores", min_value=0)
   num_botelleros = st.number_input("Botelleros", min_value=0)
   num_vitrinas = st.number_input("Vitrinas", min_value=0)
   num_enfriadores = st.number_input("Enfriadores", min_value=0)
   num_kits = st.number_input("Kits portátiles", min_value=0)
   num_barras = st.number_input("Número de barras", min_value=1)
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
           st.error("❌ El código del evento ya existe.")
else:
   st.session_state.evento_codigo = eventos_dict[seleccion]
# Edición del evento
if st.session_state.evento_codigo:
   codigo = st.session_state.evento_codigo
   evento = cursor.execute("SELECT * FROM eventos WHERE codigo = ?", (codigo,)).fetchone()
   st.success(f"📌 Evento cargado: {evento[1]} (Código: {evento[2]})")
   with st.expander("✏️ Editar datos generales del evento"):
       nuevo_nombre = st.text_input("Nombre", value=evento[1])
       nuevo_mostradores = st.number_input("Mostradores", min_value=0, value=evento[3])
       nuevo_botelleros = st.number_input("Botelleros", min_value=0, value=evento[4])
       nuevo_vitrinas = st.number_input("Vitrinas", min_value=0, value=evento[5])
       nuevo_enfriadores = st.number_input("Enfriadores", min_value=0, value=evento[6])
       nuevo_kits = st.number_input("Kits", min_value=0, value=evento[7])
       nuevo_barras = st.number_input("Nº Barras", min_value=1, value=evento[8])
       if st.button("💾 Guardar cambios del evento"):
           cursor.execute("""
               UPDATE eventos
               SET nombre=?, mostradores=?, botelleros=?, vitrinas=?, enfriadores=?, kits=?, num_barras=?
               WHERE codigo=?
           """, (nuevo_nombre, nuevo_mostradores, nuevo_botelleros, nuevo_vitrinas, nuevo_enfriadores, nuevo_kits, nuevo_barras, codigo))
           conn.commit()
           st.success("✅ Datos del evento actualizados")
           st.rerun()
   st.divider()
   st.subheader("🍸 Barras del evento")
   df_barras = pd.read_sql_query("SELECT * FROM barras WHERE evento_codigo = ?", conn, params=(codigo,))
   df_equipos = pd.read_sql_query("SELECT * FROM equipos WHERE evento_codigo = ?", conn, params=(codigo,))
   for idx, barra in enumerate(df_barras.itertuples(), 1):
       with st.expander(f"🧪 Editar Barra {idx}: {barra.nombre}"):
           nuevo_nombre = st.text_input("Nombre barra", value=barra.nombre, key=f"b_nombre_{barra.id}")
           mostradores = st.number_input("Mostradores", value=barra.mostradores, key=f"b_mostradores_{barra.id}")
           botelleros = st.number_input("Botelleros", value=barra.botelleros, key=f"b_botelleros_{barra.id}")
           vitrinas = st.number_input("Vitrinas", value=barra.vitrinas, key=f"b_vitrinas_{barra.id}")
           enfriadores = st.number_input("Enfriadores", value=barra.enfriadores, key=f"b_enfriadores_{barra.id}")
           kits = st.number_input("Kits portátiles", value=barra.kits_portatiles, key=f"b_kits_{barra.id}")
           if st.button(f"💾 Guardar cambios de barra {idx}", key=f"btn_barra_{barra.id}"):
               cursor.execute("""
                   UPDATE barras SET nombre=?, mostradores=?, botelleros=?, vitrinas=?, enfriadores=?, kits_portatiles=?
                   WHERE id=?
               """, (nuevo_nombre, mostradores, botelleros, vitrinas, enfriadores, kits, barra.id))
               conn.commit()
               st.success("✅ Barra actualizada correctamente")
               st.rerun()
   st.divider()
   st.subheader("🔄 Editar equipos por tag")
   for eq in df_equipos.itertuples():
       with st.expander(f"{eq.tipo} | {eq.barra}"):
           nuevo_serial = st.text_input("Código NFC", value=eq.serial, key=f"serial_{eq.id}")
           nuevo_tipo = st.selectbox("Tipo", ["Botellero", "Vitrina", "Enfriador", "Kit portátil"], index=["Botellero", "Vitrina", "Enfriador", "Kit portátil"].index(eq.tipo), key=f"tipo_{eq.id}")
           nueva_barra = st.selectbox("Barra", df_barras["nombre"].tolist(), index=df_barras["nombre"].tolist().index(eq.barra), key=f"barra_{eq.id}")
           if st.button(f"💾 Guardar equipo {eq.id}", key=f"btn_equipo_{eq.id}"):
               try:
                   cursor.execute("""
                       UPDATE equipos SET serial=?, tipo=?, barra=?
                       WHERE id=?
                   """, (nuevo_serial.strip(), nuevo_tipo, nueva_barra, eq.id))
                   conn.commit()
                   st.success("✅ Equipo actualizado")
                   st.rerun()
               except sqlite3.IntegrityError:
                   st.error("❌ Código NFC duplicado")
   st.subheader("📤 Exportar a Excel actualizado")
   @st.cache_data
   def to_excel(df1, df2):
       from io import BytesIO
       output = BytesIO()
       with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
           df1.to_excel(writer, sheet_name="Resumen por barra", index=False)
           df2.to_excel(writer, sheet_name="Equipos por tag", index=False)
       return output.getvalue()
   excel_data = to_excel(df_barras, df_equipos)
   st.download_button("📥 Descargar Excel", data=excel_data,
                      file_name=f"{codigo}_actualizado.xlsx",
                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
