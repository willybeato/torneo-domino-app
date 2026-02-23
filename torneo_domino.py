import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="Torneo de Dominó", page_icon="🎲", layout="wide")

# Estilos CSS personalizados para imitar el marcador de la imagen
st.markdown("""
    <style>
    /* Estilo para la barra superior del marcador */
    .marcador-header {
        background: #333; /* Color oscuro similar a la barra */
        color: white;
        padding: 10px 15px;
        border-radius: 8px 8px 0 0;
        font-weight: bold;
        text-align: center;
        font-size: 1.2em;
    }
    /* Estilo para los totales al final de la tabla */
    .marcador-total {
        background: #222; /* Color más oscuro para el pie */
        color: white;
        padding: 10px 15px;
        border-radius: 0 0 8px 8px;
        font-weight: bold;
        font-size: 1.5em;
        text-align: center;
    }
    /* Pequeño indicador de la meta */
    .marcador-meta {
        font-size: 0.6em;
        color: #aaa;
    }
    /* Centrar y dar estilo a la tabla */
    .stDataFrame {
        margin-top: 0;
        border-radius: 0;
    }
    /* Alinear los números a la derecha */
    .stDataFrame div[data-testid="stTableBody"] div div div:not(:first-child) {
        text-align: right;
        font-size: 1.1em;
    }
    /* Estilo para los botones de acción */
    .action-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 5px;
    }
    </style>
""", unsafe_allow_html=True)


# 2. Inicializar variables de estado
if 'fase' not in st.session_state:
    st.session_state.fase = 'configuracion'
if 'num_parejas' not in st.session_state:
    st.session_state.num_parejas = 4
if 'nombres_parejas' not in st.session_state:
    st.session_state.nombres_parejas = []
if 'parejas_stats' not in st.session_state:
    st.session_state.parejas_stats = {}
if 'mesa_actual' not in st.session_state:
    st.session_state.mesa_actual = []
if 'fila_espera' not in st.session_state:
    st.session_state.fila_espera = []
if 'historial_partidas' not in st.session_state:
    st.session_state.historial_partidas = []

# Variables para la partida actual y la edición
if 'historial_manos_actual' not in st.session_state:
    st.session_state.historial_manos_actual = []
if 'meta_puntos' not in st.session_state:
    st.session_state.meta_puntos = 200
if 'editing_mano_index' not in st.session_state:
    st.session_state.editing_mano_index = None

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def recalcular_totales(manos, pareja_a, pareja_b):
    """Calcula los puntos totales de cada pareja en base al historial de manos."""
    total_a = 0
    total_b = 0
    for mano in manos:
        if mano['ganador'] == pareja_a:
            total_a += mano['puntos']
        else:
            total_b += mano['puntos']
    return total_a, total_b

def verificar_ganador_partida(total_a, total_b, meta, pareja_a, pareja_b):
    """Verifica si alguna pareja ha alcanzado la meta de puntos y finaliza la partida."""
    ganador_partida = None
    perdedor_partida = None
    pts_finales_ganador = 0
    pts_finales_perdedor = 0

    if total_a >= meta:
        ganador_partida = pareja_a
        perdedor_partida = pareja_b
        pts_finales_ganador = total_a
        pts_finales_perdedor = total_b
    elif total_b >= meta:
        ganador_partida = pareja_b
        perdedor_partida = pareja_a
        pts_finales_ganador = total_b
        pts_finales_perdedor = total_a
    
    if ganador_partida:
        # 1. Guardar stats generales
        st.session_state.parejas_stats[ganador_partida]['victorias'] += 1
        st.session_state.parejas_stats[ganador_partida]['puntos_totales'] += pts_finales_ganador
        st.session_state.parejas_stats[perdedor_partida]['puntos_totales'] += pts_finales_perdedor
        
        # 2. Guardar en historial de partidas
        num_partida = len(st.session_state.historial_partidas) + 1
        st.session_state.historial_partidas.append({
            "Partida": f"#{num_partida}",
            "Ganador": ganador_partida,
            "Perdedor": perdedor_partida,
            "Marcador": f"{pts_finales_ganador} a {pts_finales_perdedor}"
        })
        
        # 3. Mensaje de victoria
        st.balloons()
        st.success(f"🎉 ¡{ganador_partida} ganó la partida con {pts_finales_ganador} puntos! 🎉")
        
        # 4. Rotar jugadores
        st.session_state.fila_espera.append(perdedor_partida)
        siguiente = st.session_state.fila_espera.pop(0)
        st.session_state.mesa_actual = [ganador_partida, siguiente]
        
        # 5. Reiniciar para la nueva partida
        st.session_state.historial_manos_actual = []
        st.session_state.editing_mano_index = None
        st.rerun()

# ==========================================
# FASE 1: Elegir cantidad de parejas
# ==========================================
if st.session_state.fase == 'configuracion':
    st.title("⚙️ Configuración del Torneo")
    cantidad = st.number_input("Cantidad de parejas participando", min_value=3, max_value=20, value=4, step=1)
    meta = st.number_input("Puntos para ganar una partida", min_value=50, max_value=500, value=200, step=50)
    
    if st.button("Siguiente 👉"):
        st.session_state.num_parejas = cantidad
        st.session_state.meta_puntos = meta
        st.session_state.fase = 'registro'
        st.rerun()

# ==========================================
# FASE 2: Registrar nombres
# ==========================================
elif st.session_state.fase == 'registro':
    st.title("📝 Nombres de las Parejas")
    
    with st.form("form_nombres"):
        nombres_input = []
        for i in range(st.session_state.num_parejas):
            nombre = st.text_input(f"Nombre de la Pareja {i+1}", f"Pareja {i+1}")
            nombres_input.append(nombre)
            
        if st.form_submit_button("Guardar Nombres 💾"):
            if len(set(nombres_input)) < len(nombres_input):
                st.error("Error: Usa nombres diferentes para cada pareja.")
            else:
                st.session_state.nombres_parejas = nombres_input
                st.session_state.parejas_stats = {nom: {'victorias': 0, 'puntos_totales': 0} for nom in nombres_input}
                st.session_state.fase = 'orden_inicial'
                st.rerun()

# ==========================================
# FASE 3: Definir Orden Inicial
# ==========================================
elif st.session_state.fase == 'orden_inicial':
    st.title("🪑 Orden de Inicio")
    nombres = st.session_state.nombres_parejas
    mesa = st.multiselect("1. Elige las DOS (2) parejas que inician en la mesa:", options=nombres, max_selections=2)
    
    if len(mesa) == 2:
        restantes = [n for n in nombres if n not in mesa]
        st.write("2. Ordena la fila de espera (Selecciona en el orden que quieres que entren):")
        espera = st.multiselect("Fila de Espera", options=restantes, default=restantes)
        
        if len(espera) == len(restantes):
            if st.button("¡Comenzar Torneo! 🎲"):
                st.session_state.mesa_actual = mesa
                st.session_state.fila_espera = espera
                st.session_state.historial_manos_actual = []
                st.session_state.fase = 'torneo'
                st.rerun()

# ==========================================
# FASE 4: Torneo en Curso
# ==========================================
elif st.session_state.fase == 'torneo':
    st.title("🏆 Torneo de Dominó")
    
    pareja_a = st.session_state.mesa_actual[0]
    pareja_b = st.session_state.mesa_actual[1]
    meta = st.session_state.meta_puntos

    # Calcular totales actuales al inicio de cada renderizado
    pts_a, pts_b = recalcular_totales(st.session_state.historial_manos_actual, pareja_a, pareja_b)

    col_izq, col_der = st.columns([1.3, 1])

    with col_izq:
        # --- MARCADOR ESTILIZADO ---
        st.header("Partida Actual")
        
        col_m1, col_m2 = st.columns(2)
        
        # Encabezados del marcador
        with col_m1:
            st.markdown(f'<div class="marcador-header">{pareja_a}</div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="marcador-header">{pareja_b}</div>', unsafe_allow_html=True)
            
        # Tabla de historial de manos y botones de acción
        if st.session_state.historial_manos_actual:
            for i, mano in enumerate(st.session_state.historial_manos_actual):
                puntos_a = mano['puntos'] if mano['ganador'] == pareja_a else 0
                puntos_b = mano['puntos'] if mano['ganador'] == pareja_b else 0
                
                col1, col2, col3 = st.columns([1, 1, 0.3])
                with col1:
                    st.write(f"Mano {i+1}: **{puntos_a}**")
                with col2:
                    st.write(f"Mano {i+1}: **{puntos_b}**")
                with col3:
                    # Botones de editar (✏️) y borrar (❌)
                    col_btn_edit, col_btn_del = st.columns(2)
                    if col_btn_edit.button("✏️", key=f"edit_{i}"):
                        st.session_state.editing_mano_index = i
                        st.rerun()
                    if col_btn_del.button("❌", key=f"del_{i}"):
                        st.session_state.historial_manos_actual.pop(i)
                        st.rerun() # Recalcula y verifica ganador automáticamente
        else:
            st.info("No se han anotado manos en esta partida.")

        # Totales al pie del marcador
        with col_m1:
            st.markdown(f'<div class="marcador-total">{pts_a} <span class="marcador-meta">/{meta}</span></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="marcador-total">{pts_b} <span class="marcador-meta">/{meta}</span></div>', unsafe_allow_html=True)

        st.divider()

        # --- LÓGICA PARA EDITAR UNA MANO ---
        if st.session_state.editing_mano_index is not None:
            idx = st.session_state.editing_mano_index
            mano_to_edit = st.session_state.historial_manos_actual[idx]
            
            st.subheader(f"Editando Mano #{idx+1}")
            with st.form(f"form_edit_{idx}"):
                edit_ganador = st.radio("Ganador", [pareja_a, pareja_b], index=0 if mano_to_edit['ganador'] == pareja_a else 1, horizontal=True)
                edit_puntos = st.number_input("Puntos", min_value=1, step=1, value=mano_to_edit['puntos'])
                
                if st.form_submit_button("Actualizar Mano ✔️"):
                    st.session_state.historial_manos_actual[idx] = {
                        'ganador': edit_ganador,
                        'puntos': edit_puntos
                    }
                    st.session_state.editing_mano_index = None
                    st.rerun() # Recalcula y verifica ganador automáticamente

        # --- FORMULARIO PARA ANOTAR UNA NUEVA MANO (si no se está editando) ---
        elif st.session_state.editing_mano_index is None:
            with st.form("registro_mano", clear_on_submit=True):
                st.subheader("Anotar Nueva Mano")
                ganador_mano = st.radio("¿Quién ganó?", [pareja_a, pareja_b], horizontal=True)
                puntos_mano = st.number_input("Puntos obtenidos", min_value=1, step=1, value=10)
                
                if st.form_submit_button("Sumar Puntos ➕"):
                    st.session_state.historial_manos_actual.append({
                        "ganador": ganador_mano,
                        "puntos": puntos_mano
                    })
                    st.rerun() # Recalcula y verifica ganador automáticamente

        # Verificar si alguien ganó la partida DESPUÉS de cualquier cambio (nueva mano, edición o borrado)
        pts_a_final, pts_b_final = recalcular_totales(st.session_state.historial_manos_actual, pareja_a, pareja_b)
        verificar_ganador_partida(pts_a_final, pts_b_final, meta, pareja_a, pareja_b)

    with col_der:
        # --- FILA DE ESPERA ---
        st.subheader("⏳ En Fila de Espera")
        if not st.session_state.fila_espera:
            st.info("No hay parejas en espera.")
        for i, pareja_espera in enumerate(st.session_state.fila_espera):
            if i == 0:
                st.info(f"**1. {pareja_espera}** *(Próximos en entrar)*")
            else:
                st.write(f"{i+1}. {pareja_espera}")
        
        st.divider()

        # --- TABLA DE POSICIONES GENERAL ---
        st.header("📊 Tabla General")
        datos_tabla = []
        for pareja, stats in st.session_state.parejas_stats.items():
            datos_tabla.append({
                "Pareja": pareja, 
                "Juegos Ganados": stats['victorias'], 
                "Puntos Totales": stats['puntos_totales']
            })
            
        df_posiciones = pd.DataFrame(datos_tabla)
        df_posiciones = df_posiciones.sort_values(by=["Juegos Ganados", "Puntos Totales"], ascending=[False, False]).reset_index(drop=True)
        df_posiciones.index = df_posiciones.index + 1
        st.dataframe(df_posiciones, use_container_width=True)
        
        # --- HISTORIAL DE PARTIDAS COMPLETADAS ---
        st.divider()
        st.header("📜 Historial de Partidas")
        if st.session_state.historial_partidas:
            df_historial = pd.DataFrame(st.session_state.historial_partidas)
            st.dataframe(df_historial.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Aún no se ha completado ninguna partida de {} puntos.".format(meta))

    # Botón de reinicio
    st.divider()
    if st.button("⚠️ Terminar Torneo y Empezar de Nuevo"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()