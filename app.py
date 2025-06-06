import streamlit as st
import pandas as pd
import datetime
import sqlite3
st.set_page_config(page_title="Control de Equipos NFC", layout="centered")
# Conexión a la base de datos
conn = sqlite3.connect("eventos.db", check_same_thread=False)
cursor = conn.cursor()
# Crear tablas si no existen, con columna timestamp en equipos
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
   num_mostradores = st.number_input("Total de Mostradores", min_value=0, value=0)
   num_botelleros = st.number_input("Total de Botelleros", min_value=0, value=0)
   num_vitrinas = st.number_input("Total de Vitrinas", min_value=0, value=0)
   num_enfriadores = st.number_input("Total de Enfriadores", min_value=0, value=0)
   num_kits = st.number_input("Total de Kits portátiles", min_value=0, value=0)
   num_barras = st.number_input("Número total de barras", min_value=1, value=1)
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
           st.experimental_rerun()
       except sqlite3.IntegrityError:
           st.error("❌ El código del evento ya existe.")
else:
   st.session_state.evento_codigo = eventos_dict.get(seleccion, None)
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
           st.experimental_rerun()
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
               st.experimental_rerun()
   st.header("🔖 Registrar Equipos NFC por Barra y Tipo")
   if not st.session_state.registrando_equipo:
       st.info("Selecciona la barra y el tipo de equipo para comenzar el registro de tags.")
       # Selección barra
       barra_sel = st.selectbox("Selecciona una barra", [b[2] for b in barras])
       # Mostrar tipos (excepto mostradores)
       tipos_materiales = ['botelleros', 'vitrinas', 'enfriadores', 'kits_portatiles']
       tipo_sel = st.selectbox("Selecciona tipo de equipo", tipos_materiales)
       # Obtener cantidad declarada en barra para el tipo seleccionado
       barra_info = next(b for b in barras if b[2] == barra_sel)
       cantidad_declarada = {
           'botelleros': barra_info[4],
           'vitrinas': barra_info[5],
           'enfriadores': barra_info[6],
           'kits_portatiles': barra_info[7],
       }.get(tipo_sel, 0)
       st.write(f"Cantidad declarada para {tipo_sel} en {barra_sel}: **{cantidad_declarada}**")
       if cantidad_declarada == 0:
           st.warning("No hay unidades declaradas para este tipo en la barra seleccionada.")
       else:
           if st.button("Comenzar registro de tags"):
               st.session_state.registrando_equipo = True
               st.session_state.barra_actual =
