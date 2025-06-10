import streamlit as st
import pandas as pd
import datetime
import sqlite3
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
# Estado inicial
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
   st.header("📥 Registrar equipos por tag")
   for barra in barras:
       st.subheader(f"📦 {barra[2]}")
       equipos_registrables = {
           "Botellero": barra[4],
           "Vitrina": barra[5],
           "Enfriador": barra[6],
           "Kit portátil": barra[7],
       }
       for tipo, cantidad in equipos_registrables.items():
           st.markdown(f"**🔹 {tipo}s esperados: {cantidad}**")
           # Recuperar tags ya registrados para esta barra y tipo
           registros_previos = cursor.execute(
               "SELECT serial FROM equipos WHERE evento_codigo = ? AND barra = ? AND tipo = ? ORDER BY id ASC",
               (codigo, barra[2], tipo)
           ).fetchall()
           seriales_guardados = [r[0] for r in registros_previos]
           registros = []
           for i in range(cantidad):
               valor_inicial = seriales_guardados[i] if i < len(seriales_guardados) else ""
               serial = st.text_input(f"{tipo} #{i+1} - Tag", value=valor_inicial, key=f"{barra[0]}_{tipo}_{i}")
               if serial.strip():
                   registros.append((codigo, barra[2], tipo, serial.strip(), datetime.datetime.now().isoformat()))
           if st.button(f"Guardar {tipo}s en {barra[2]}", key=f"guardar_{barra[0]}_{tipo}"):
               for r in registros:
                   try:
                       cursor.execute("INSERT INTO equipos (evento_codigo, barra, tipo, serial, timestamp) VALUES (?, ?, ?, ?, ?)", r)
                   except sqlite3.IntegrityError:
                       st.warning(f"⚠️ El tag '{r[3]}' ya existe y no se ha añadido.")
               conn.commit()
               st.success(f"✅ {tipo}s guardados para {barra[2]}")
               st.rerun()
   st.header("📤 Exportar a Excel actualizado")
   df_barras = pd.read_sql_query("SELECT * FROM barras WHERE evento_codigo = ?", conn, params=(codigo,))
   df_equipos = pd.read_sql_query("SELECT * FROM equipos WHERE evento_codigo = ?", conn, params=(codigo,))
   @st.cache_data
   def to_excel(df1, df2):
       from io import BytesIO
       output = BytesIO()
       with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
           df1.to_excel(writer, sheet_name='Resumen por barra', index=False)
           df2.to_excel(writer, sheet_name='Equipos por tag', index=False)
       return output.getvalue()
   excel_data = to_excel(df_barras, df_equipos)
   st.download_button("📥 Descargar Excel", data=excel_data,
                     file_name=f"{codigo}_registro_evento.xlsx",
                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
