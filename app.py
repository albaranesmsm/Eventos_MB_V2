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
    barra_id INTEGER,
    tipo TEXT,
    serial TEXT UNIQUE,
    timestamp TEXT,
    FOREIGN KEY(barra_id) REFERENCES barras(id) ON DELETE CASCADE
)
""")
conn.commit()

# Estado inicial
if "evento_codigo" not in st.session_state:
    st.session_state.evento_codigo = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

st.title("🧊 Control de Equipos de Frío por NFC")

# Funciones auxiliares

def cargar_eventos():
    eventos = cursor.execute("SELECT codigo, nombre FROM eventos ORDER BY nombre").fetchall()
    eventos_dict = {f"{n} ({c})": c for c, n in eventos}
    return eventos_dict

def cargar_evento(codigo):
    return cursor.execute("SELECT * FROM eventos WHERE codigo = ?", (codigo,)).fetchone()

def cargar_barras(evento_codigo):
    return cursor.execute("SELECT * FROM barras WHERE evento_codigo = ?", (evento_codigo,)).fetchall()

def cargar_equipos(evento_codigo):
    return cursor.execute("SELECT * FROM equipos WHERE evento_codigo = ?", (evento_codigo,)).fetchall()

def actualizar_evento(id_evento, nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras):
    cursor.execute("""


Claro, aquí tienes el código completo, organizado en pantallas para que puedas crear, editar barras y equipos, y que al guardar se actualice el archivo Excel para descargar. Es una versión funcional que usa SQLite y Streamlit:

```python
import streamlit as st
import pandas as pd
import datetime
import sqlite3

st.set_page_config(page_title="Control de Equipos NFC", layout="centered")

# --- Conexión a SQLite ---
conn = sqlite3.connect("eventos.db", check_same_thread=False)
cursor = conn.cursor()

# --- Crear tablas ---
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
    barra_id INTEGER,
    tipo TEXT,
    serial TEXT UNIQUE,
    timestamp TEXT,
    FOREIGN KEY(barra_id) REFERENCES barras(id) ON DELETE CASCADE
)
""")
conn.commit()

# --- Estado global ---
if "evento_codigo" not in st.session_state:
    st.session_state.evento_codigo = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"
if "barra_id" not in st.session_state:
    st.session_state.barra_id = None

st.title("🧊 Control de Equipos de Frío por NFC")

# --- Funciones auxiliares ---

def cargar_eventos():
    eventos = cursor.execute("SELECT codigo, nombre FROM eventos ORDER BY nombre").fetchall()
    return {f"{n} ({c})": c for c, n in eventos}

def cargar_evento(codigo):
    return cursor.execute("SELECT * FROM eventos WHERE codigo = ?", (codigo,)).fetchone()

def cargar_barras(evento_codigo):
    return cursor.execute("SELECT * FROM barras WHERE evento_codigo = ?", (evento_codigo,)).fetchall()

def cargar_equipos(evento_codigo):
    return cursor.execute("SELECT * FROM equipos WHERE evento_codigo = ?", (evento_codigo,)).fetchall()

def cargar_equipos_por_barra(barra_id):
    return cursor.execute("SELECT * FROM equipos WHERE barra_id = ?", (barra_id,)).fetchall()

def actualizar_evento(id_evento, nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras):
    cursor.execute("""
        UPDATE eventos SET nombre=?, codigo=?, mostradores=?, botelleros=?, vitrinas=?, enfriadores=?, kits=?, num_barras=? WHERE id=?
    """, (nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras, id_evento))
    conn.commit()

def actualizar_barra(id_barra, nombre, mostradores, botelleros, vitrinas, enfriadores, kits):
    cursor.execute("""
        UPDATE barras SET nombre=?, mostradores=?, botelleros=?, vitrinas=?, enfriadores=?, kits_portatiles=? WHERE id=?
    """, (nombre, mostradores, botelleros, vitrinas, enfriadores, kits, id_barra))
    conn.commit()

def actualizar_equipo(id_equipo, tipo, serial):
    cursor.execute("""
        UPDATE equipos SET tipo=?, serial=? WHERE id=?
    """, (tipo, serial, id_equipo))
    conn.commit()

def eliminar_equipo(id_equipo):
    cursor.execute("DELETE FROM equipos WHERE id=?", (id_equipo,))
    conn.commit()

def crear_excel(evento_codigo):
    barras = cargar_barras(evento_codigo)
    equipos = cargar_equipos(evento_codigo)
    df_barras = pd.DataFrame(barras, columns=["id", "evento_codigo", "nombre", "mostradores", "botelleros", "vitrinas", "enfriadores", "kits_portatiles"])
    df_equipos = pd.DataFrame(equipos, columns=["id", "evento_codigo", "barra_id", "tipo", "serial", "timestamp"])
    from io import BytesIO
    import xlsxwriter
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_barras.to_excel(writer, sheet_name='Barras', index=False)
        df_equipos.to_excel(writer, sheet_name='Equipos', index=False)
    return output.getvalue()

# --- Páginas ---

def pagina_inicio():
    st.header("📂 Selección o creación de evento")
    eventos_dict = cargar_eventos()
    opciones = ["Nuevo evento"] + list(eventos_dict.keys()) if eventos_dict else ["Nuevo evento"]
    seleccion = st.selectbox("Cargar evento existente o crear uno nuevo", opciones)

    if seleccion == "Nuevo evento":
        nombre = st.text_input("Nombre del evento")
        codigo = st.text_input("Código único del evento")
        mostradores = st.number_input("Total de mostradores", min_value=0)
        botelleros = st.number_input("Total de botelleros", min_value=0)
        vitrinas = st.number_input("Total de vitrinas", min_value=0)
        enfriadores = st.number_input("Total de enfriadores", min_value=0)
        kits = st.number_input("Total de kits portátiles", min_value=0)
        num_barras = st.number_input("Número total de barras", min_value=1)

        if st.button("Crear evento"):
            try:
                cursor.execute("""
                    INSERT INTO eventos (nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nombre, codigo, mostradores, botelleros, vitrinas, enfriadores, kits, num_barras))
                conn.commit()
                st.success("Evento creado correctamente.")
                st.session_state.evento_codigo = codigo
                st.session_state.pagina = "Registrar Barras"
                st.experimental_rerun()
            except sqlite3.IntegrityError:
                st.error("Ya existe un evento con ese código.")
    else:
        codigo = eventos_dict[seleccion]
        if st.button("Cargar evento"):
            st.session_state.evento_codigo = codigo
            st.session_state.pagina = "Registrar Barras"
            st.experimental_rerun()

def pagina_registrar_barras():
    evento = cargar_evento(st.session_state.evento_codigo)
    st.success(f"Evento: {evento[1]} (Código: {evento[2]})")
    total_barras = evento[8]
    barras = cargar_barras(evento[2])
    idx = len(barras)

    st.header(f"Registrar barra {idx + 1} de {total_barras}")

    if idx >= total_barras:
        st.info("Todas las barras ya han sido registradas.")
        if st.button("Ir a Editar Barras"):
            st.session_state.pagina = "Editar Barras"
            st.experimental_rerun()
    else:
        nombre = st.text_input("Nombre o ubicación de la barra")
        mostradores = st.number_input("Mostradores", min_value=0)
        botelleros = st.number_input("Botelleros", min_value=0)
        vitrinas = st.number_input("Vitrinas", min_value=0)
        enfriadores = st.number_input("Enfriadores", min_value=0)
        kits = st.number_input("Kits portátiles", min_value=0)

        equipos_nuevos = []
        def leer_tags(tipo, cantidad):
            equipos_barra = []
            for i in range(int(cantidad)):
                tag = st.text_input(f"{tipo} {i+1}", key=f"{tipo}_{idx}_{i}")
                if tag:
                    existe = cursor.execute("SELECT 1 FROM equipos WHERE serial = ?", (tag.strip(),)).fetchone()
                    if existe:
                        st.warning(f"{tipo} {i+1}: Este código ya fue registrado")
                    else:
                        equipos_barra.append((evento[2], None, tipo, tag.strip(), datetime.datetime.now().isoformat()))
            return equipos_barra

        equipos_nuevos += leer_tags("Botellero", botelleros)
        equipos_nuevos += leer_tags("Vitrina", vitrinas)
        equipos_nuevos += leer_tags("Enfriador", enfriadores)
        equipos_nuevos += leer_tags("Kit portátil", kits)

        if st.button("Guardar barra y continuar"):
            cursor.execute("""
                INSERT INTO barras (evento_codigo, nombre, mostradores, botelleros, vitrinas, enfriadores, kits_portatiles)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (evento[2], nombre, mostradores, botelleros, vitrinas, enfriadores, kits))
            barra_id = cursor.lastrowid

            for equipo in equipos_nuevos:
                cursor.execute("""
                    INSERT INTO equipos (evento_codigo, barra_id, tipo, serial, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (equipo[0], barra_id, equipo[2], equipo[3], equipo[4]))
            conn.commit()
            st.success("Barra y equipos guardados")
            st.experimental_rerun()

    if st.button("Volver a Inicio"):
        st.session_state.pagina = "Inicio"
        st.experimental_rerun()

def pagina_editar_barras():
    evento = cargar_evento(st.session_state.evento_codigo)
    st.success(f"Editar barras del evento: {evento[1]} (Código: {evento[2]})")
    barras = cargar_barras(evento[2])
    if not barras:
        st.info("No hay barras para editar.")
    else:
        opciones = {f"{b[0]} - {b[2]}": b for b in barras}
        seleccion = st.selectbox("Selecciona la barra a editar", list(opciones.keys()))
        barra = opciones[seleccion]

        nombre = st.text_input("Nombre o ubicación", barra[2])
        mostradores = st.number_input("Mostradores", min_value=0, value=barra[3])
        botelleros = st.number_input("Botelleros", min_value=0, value=barra[4])
        vitrinas = st.number_input("Vitrinas", min_value=0, value=barra[5])
        enfriadores = st.number_input("Enfriadores", min_value=0, value=barra[6])
        kits = st.number_input("Kits portátiles", min_value=0, value=barra[7])

        if st.button("Guardar cambios en barra"):
            actualizar_barra(barra[0], nombre, mostradores, botelleros, vitrinas, enfriadores, kits)
            st.success("Barra actualizada")

        if st.button("Editar equipos de esta barra"):
            st.session_state.barra_id = barra[0]
            st.session_state.pagina = "Editar Equipos"
            st.experimental_rerun()

    if st.button("Volver a Registrar Barras"):
        st.session_state.pagina = "Registrar Barras"
        st.experimental_rerun()

    if st.button("Ir a Resumen"):
        st.session_state.pagina = "Resumen"
        st.experimental_rerun()

def pagina_editar_equipos():
    barra_id = st.session_state.barra_id
    if not barra_id:
        st.warning("No se ha seleccionado una barra.")
        st.session_state.pagina = "Editar Barras"
        st.experimental_rerun()
    barra = cursor.execute("SELECT * FROM barras WHERE id = ?", (barra_id,)).fetchone()
    st.success(f"Editar equipos de la barra: {barra[2]}")

    equipos = cargar_equipos_por_barra(barra_id)
    if not equipos:
        st.info("No hay equipos registrados en esta barra.")
    else:
        for equipo in equipos:
            with st.expander(f"Equipo ID {equipo[0]} - Serial: {equipo[4]}"):
                tipo = st.text_input("Tipo", value=equipo[3], key=f"tipo_{equipo[0]}")
                serial = st.text_input("Serial", value=equipo[4], key=f"serial_{equipo[0]}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Guardar", key=f"guardar_{equipo[0]}"):
                        existe = cursor.execute("SELECT id FROM equipos WHERE serial = ? AND id != ?", (serial.strip(), equipo[0])).fetchone()
                        if existe:
                            st.error("Este serial ya está registrado en otro equipo.")
                        else:
                            actualizar_equipo(equipo[0], tipo, serial)
                            st.success("Equipo actualizado")
                with col2:
                    if st.button("Eliminar", key=f"eliminar_{equipo[0]}"):
                        eliminar_equipo(equipo[0])
                        st.success("Equipo eliminado")
                        st.experimental_rerun()

    if st.button("Volver a Editar Barras"):
        st.session_state.pagina = "Editar Barras"
        st.experimental_rerun()

    if st.button("Ir a Resumen"):
        st.session_state.pagina = "Resumen"
        st.experimental_rerun()

def pagina_resumen():
    st.header("📊 Resumen del evento")
    evento = cargar_evento(st.session_state.evento_codigo)
    barras = cargar_barras(evento[2])
    equipos = cargar_equipos(evento[2])

    df_barras = pd.DataFrame(barras, columns=["id", "evento_codigo", "nombre", "mostradores", "botelleros", "vitrinas", "enfriadores", "kits_portatiles"])
    df_equipos = pd.DataFrame(equipos, columns=["id", "evento_codigo", "barra_id", "tipo", "serial", "timestamp"])

    st.subheader("Barras registradas")
    st.dataframe(df_barras)

    st.subheader("Equipos registrados")
    st.dataframe(df_equipos)

    excel_data = crear_excel(evento[2])
    st.download_button("Descargar Excel actualizado", excel_data, file_name=f"evento_{evento[2]}_datos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.button("Volver a Editar Barras"):
        st.session_state.pagina = "Editar Barras"
        st.experimental_rerun()

    if st.button("Volver a Inicio"):
        st.session_state.pagina = "Inicio"
        st.experimental_rerun()

# --- Control de navegación ---
if st.session_state.pagina == "Inicio":
    pagina_inicio()
elif st.session_state.pagina == "Registrar Barras":
    pagina_registrar_barras()
elif st.session_state.pagina == "Editar Barras":
    pagina_editar_barras()
elif st.session_state.pagina == "Editar Equipos":
    pagina_editar_equipos()
elif st.session_state.pagina == "Resumen":
    pagina_resumen()
