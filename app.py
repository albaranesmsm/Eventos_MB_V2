import streamlit as st
import pandas as pd
import datetime
import sqlite3
from io import BytesIO
st.set_page_config(page_title="Control de Equipos NFC", layout="centered")
# Conexión a la base de datos
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
if "evento_codigo" not in st.session_state:
   st.session_state.evento_codigo = None
st.title("🧊 Control de Equipos de Frío por NFC")
# Cargar eventos existentes
eventos = cursor.execute("SELECT codigo, nombre FROM eventos").fetchall()
eventos_dict = {f"{n} ({c})": c for c, n in eventos}
opciones = ["Nuevo evento"] + list(eventos_dict.keys())
seleccion = st.selectbox("📂 Cargar evento existente o crear uno nuevo", opciones)
# Crear nuevo evento
if seleccion == "Nuevo evento":
   st.header("🔧 Configuración del Evento")
   nombre_evento = st.text_input("Nombre del evento")
   codigo_evento = st.text_input("Código único del evento")
   num_mostradores = st.number_input("Total de Mostradores", min_value=0)
   num_botelleros = st.number_input("Total de Botelleros", min_value=0)
   num_vitrinas = st.number_input("Total de Vitrinas", min_value=0)
   num_enfriadores = st.number_input("Total de Enfriadores", min_value=0)
   num_kits = st.number_input("Total de Kits portátiles", min_value=0)
   num_barras = st.number_input("Número total de barras", min_value=1)
   if st.button("✅ Crear evento"):
       if not nombre_evento or not codigo_evento:
           st.error("⚠️ Por favor, rellena todos los campos obligatorios.")
       else:
           try:
               cursor.execute("""
                   INSERT INTO eventos (nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               """, (nombre_evento, codigo_evento, num_mostradores, num_botelleros, num_vitrinas, num_enfriadores, num_kits, num_barras))
               for i in range(1, int(num_barras) + 1):
                   cursor.execute("""
                       INSERT INTO barras (evento_codigo, nombre, mostradores, botelleros, vitrinas, enfriadores, kits_portatiles)
                       VALUES (?, ?, 0, 0, 0, 0, 0)
                   """, (codigo_evento, f"Barra {i}"))
               conn.commit()
               st.session_state.evento_codigo = codigo_evento
               st.rerun()
           except sqlite3.IntegrityError:
               st.error("❌ El código del evento ya existe.")
else:
   st.session_state.evento_codigo = eventos_dict[seleccion]
# Si hay evento cargado
if st.session_state.evento_codigo:
   codigo = st.session_state.evento_codigo
   evento = cursor.execute("SELECT * FROM eventos WHERE codigo = ?", (codigo,)).fetchone()
   st.success(f"Evento cargado: {evento[1]} (Código: {evento[2]})")
   with st.expander("✏️ Editar datos generales del evento"):
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
   st.header("🍸 Barras del evento")
   barras = cursor.execute("SELECT * FROM barras WHERE evento_codigo = ?", (codigo,)).fetchall()
   for barra in barras:
       with st.expander(f"🧪 {barra[2]}"):
           nombre = st.text_input("Nombre o ubicación", value=barra[2], key=f"nombre_{barra[0]}")
           mostradores = st.number_input("Mostradores", min_value=0, value=barra[3], key=f"most_{barra[0]}")
           botelleros = st.number_input("Botelleros", min_value=0, value=barra[4], key=f"bot_{barra[0]}")
           vitrinas = st.number_input("Vitrinas", min_value=0, value=barra[5], key=f"vit_{barra[0]}")
           enfriadores = st.number_input("Enfriadores", min_value=0, value=barra[6], key=f"enf_{barra[0]}")
           kits = st.number_input("Kits portátiles", min_value=0, value=barra[7], key=f"kpt_{barra[0]}")
           if st.button(f"💾 Guardar cambios en {barra[2]}", key=f"guardar_barra_{barra[0]}"):
               cursor.execute("""
                   UPDATE barras SET nombre=?, mostradores=?, botelleros=?, vitrinas=?, enfriadores=?, kits_portatiles=?
                   WHERE id=?
               """, (nombre, mostradores, botelleros, vitrinas, enfriadores, kits, barra[0]))
               conn.commit()
               st.success(f"✅ Barra '{nombre}' actualizada")
   st.header("🔖 Registrar equipos por tag")
   for barra in barras:
       nombre_barra = barra[2]
       equipos_a_registrar = {
           "botellero": barra[4],
           "vitrina": barra[5],
           "enfriador": barra[6],
           "kit portátil": barra[7],
       }
       st.subheader(f"📍 {nombre_barra}")
       for tipo, cantidad in equipos_a_registrar.items():
           existentes = cursor.execute("""
               SELECT COUNT(*) FROM equipos
               WHERE evento_codigo = ? AND barra = ? AND tipo = ?
           """, (codigo, nombre_barra, tipo)).fetchone()[0]
           restantes = cantidad - existentes
           if restantes > 0:
               st.markdown(f"**{tipo.title()}s restantes por registrar:** {restantes}")
               for i in range(restantes):
                   tag = st.text_input(f"🔹 Tag {tipo.title()} #{i+1} en {nombre_barra}", key=f"{nombre_barra}_{tipo}_{i}")
                   if tag:
                       try:
                           cursor.execute("""
                               INSERT INTO equipos (evento_codigo, barra, tipo, serial, timestamp)
                               VALUES (?, ?, ?, ?, ?)
                           """, (codigo, nombre_barra, tipo, tag.strip(), datetime.datetime.now().isoformat()))
                           conn.commit()
                           st.success(f"✅ {tipo.title()} registrado")
                           st.rerun()
                       except sqlite3.IntegrityError:
                           st.error("❌ Ese tag ya existe.")
           else:
               st.info(f"✔️ Todos los {tipo.title()}s están registrados.")
   st.header("🛠️ Editar equipos registrados")
   df_equipos = pd.read_sql_query("SELECT * FROM equipos WHERE evento_codigo = ?", conn, params=(codigo,))
   for i, row in df_equipos.iterrows():
       col1, col2, col3 = st.columns([3, 2, 2])
       with col1:
           nuevo_serial = st.text_input(f"🔹 Tag {row['id']}", value=row['serial'], key=f"serial_{row['id']}")
       with col2:
           nuevo_tipo = st.text_input("Tipo", value=row['tipo'], key=f"tipo_{row['id']}")
       with col3:
           nueva_barra = st.text_input("Barra", value=row['barra'], key=f"barra_{row['id']}")
       if st.button("Guardar cambios", key=f"guardar_equipo_{row['id']}"):
           try:
               cursor.execute("""
                   UPDATE equipos SET serial=?, tipo=?, barra=? WHERE id=?
               """, (nuevo_serial.strip(), nuevo_tipo.strip(), nueva_barra.strip(), row['id']))
               conn.commit()
               st.success("✅ Tag actualizado")
               st.rerun()
           except sqlite3.IntegrityError:
               st.error("❌ El tag ya existe.")
   st.header("📤 Exportar datos")
   df_barras = pd.read_sql_query("SELECT * FROM barras WHERE evento_codigo = ?", conn, params=(codigo,))
   df_equipos = pd.read_sql_query("SELECT * FROM equipos WHERE evento_codigo = ?", conn, params=(codigo,))
   def to_excel(df1, df2):
       output = BytesIO()
       with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
           df1.to_excel(writer, sheet_name='Resumen por barra', index=False)
           df2.to_excel(writer, sheet_name='Equipos por tag', index=False)
       return output.getvalue()
   excel_data = to_excel(df_barras, df_equipos)
   st.download_button("📥 Descargar Excel", data=excel_data,
                      file_name=f"{codigo}_registro_evento.xlsx",
                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
