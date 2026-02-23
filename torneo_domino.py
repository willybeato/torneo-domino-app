import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="Torneo de Dominó", page_icon="🎲", layout="wide")

# Estilos CSS para simular la tabla elegante y fondos oscuros
st.markdown("""
    <style>
    .equipo-header {
        background-color: #2c2f33;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 10px 10px 0 0;
        margin-bottom: 0px;
        font-weight: bold;
    }
    .totales-gigantes {
        text-align: center; 
        font-size: 4.5em; 
        font-weight: bold;
        margin-top: 20px;
        line-height: 1.1;
    }
    .totales-meta {
        font-size: 0.3em; 
        color: #888;
        font-weight: normal;
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
    total_a = sum([m['puntos'] for m in manos if m['ganador'] == pareja_a])
    total_b = sum([m['puntos'] for m in manos if m['ganador'] == pareja_b])
    return total_a, total_b

def verificar_ganador_partida(total_a, total_b, meta, pareja_a, pareja_b):
    ganador_partida, perdedor_partida = None, None
    pts_finales_ganador, pts_finales_perdedor = 0, 0

    if total_a >= meta:
        ganador_partida, perdedor_partida = pareja_a, pareja_b
        pts_finales_ganador, pts_finales_perdedor = total_a, total_b
    elif total_b >= meta:
        ganador_partida, perdedor_partida = pareja_b, pareja_a
        pts_finales_ganador, pts_finales_perdedor = total_b, total_a
    
    if ganador_partida:
        st.session_state.parejas_stats[ganador_partida]['victorias'] += 1
        st.session_state.parejas_stats[ganador_partida]['puntos_totales'] += pts_finales_ganador
        st.session_state.parejas_stats[perdedor_partida]['puntos_totales'] += pts_finales_perdedor
        
        num_partida = len(st.session_state.historial_partidas) + 1
        st.session_state.historial_partidas.append({
            "Partida": f"#{num_partida}", "Ganador": ganador_partida,
            "Perdedor": perdedor_partida, "Marcador": f"{pts_finales_ganador} a {pts_finales_perdedor}"
        })
        
        st.balloons()
        st.success(f"🎉 ¡{ganador_partida} ganó la partida con {pts_finales_ganador} puntos! 🎉")
        
        st.session_state.fila_espera.append(perdedor_partida)
        siguiente = st.session_state.fila_espera.pop(0)
        st.session_state.mesa_actual = [ganador_partida, siguiente]
        
        st.session_state.historial_manos_actual = []
        st.session_state.editing_mano_index = None
        st.rerun()

# ==========================================
# FASE 1 y 2 (Configuración Inicial)
# ==========================================
if st.session_state.fase == 'configuracion':
    st.title("⚙️ Configuración del Torneo")
    cantidad = st.number_input("Cantidad de parejas", min_value=3, max_value=20, value=4, step=1)
    meta = st.number_input("Puntos para ganar (Meta)", min_value=50, max_value=500, value=200, step=50)
    if st.button("Siguiente 👉"):
        st.session_state.num_parejas = cantidad
        st.session_state.meta_puntos = meta
        st.session_state.fase = 'registro'
        st.rerun()

elif st.session_state.fase == 'registro':
    st.title("📝 Nombres de las Parejas")
    with st.form("form_nombres"):
        nombres_input = [st.text_input(f"Pareja {i+1}", f"Pareja {i+1}") for i in range(st.session_state.num_parejas)]
        if st.form_submit_button("Guardar Nombres 💾"):
            if len(set(nombres_input)) < len(nombres_input):
                st.error("Usa nombres diferentes para cada pareja.")
            else:
                st.session_state.nombres_parejas = nombres_input
                st.session_state.parejas_stats = {nom: {'victorias': 0, 'puntos_totales': 0} for nom in nombres_input}
                st.session_state.fase = 'orden_inicial'
                st.rerun()

# ==========================================
# FASE 3: Definir Orden Inicial (CORREGIDA)
# ==========================================
elif st.session_state.fase == 'orden_inicial':
    st.title("🪑 Orden de Inicio")
    nombres = st.session_state.nombres_parejas
    
    st.subheader("1. La Mesa Principal")
    mesa = st.multiselect("Elige las DOS (2) parejas que inician jugando:", options=nombres, max_selections=2)
    
    if len(mesa) == 2:
        st.divider()
        restantes = [n for n in nombres if n not in mesa]
        
        st.subheader("2. La Fila de Espera")
        st.info("💡 **Importante:** Selecciona a las parejas restantes **una por una** en el orden exacto en el que quieres que entren a jugar.")
        
        # Eliminamos el parámetro "default" para que el usuario deba elegir el orden manualmente
        espera = st.multiselect("Elige quién va primero en la fila, quién segundo, etc.:", options=restantes)
        
        if len(espera) == len(restantes):
            st.success("¡Orden configurado correctamente!")
            if st.button("¡Comenzar Torneo! 🎲", type="primary", use_container_width=True):
                st.session_state.mesa_actual = mesa
                st.session_state.fila_espera = espera
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

    pts_a, pts_b = recalcular_totales(st.session_state.historial_manos_actual, pareja_a, pareja_b)

    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        # --- NOMBRES DE LOS EQUIPOS ---
        col_name_a, col_name_b = st.columns(2)
        col_name_a.markdown(f"<h3 class='equipo-header'>{pareja_a}</h3>", unsafe_allow_html=True)
        col_name_b.markdown(f"<h3 class='equipo-header'>{pareja_b}</h3>", unsafe_allow_html=True)
        
        # --- INPUTS RÁPIDOS PARA AGREGAR PUNTOS ---
        col_form_a, col_form_b = st.columns(2)
        
        with col_form_a:
            with st.form("add_a", clear_on_submit=True):
                ca1, ca2 = st.columns([2, 1])
                pts_in_a = ca1.number_input("Pts", min_value=1, step=1, value=10, label_visibility="collapsed")
                if ca2.form_submit_button("➕", use_container_width=True):
                    st.session_state.historial_manos_actual.append({"ganador": pareja_a, "puntos": pts_in_a})
                    st.rerun()
                    
        with col_form_b:
            with st.form("add_b", clear_on_submit=True):
                cb1, cb2 = st.columns([2, 1])
                pts_in_b = cb1.number_input("Pts", min_value=1, step=1, value=10, label_visibility="collapsed")
                if cb2.form_submit_button("➕", use_container_width=True):
                    st.session_state.historial_manos_actual.append({"ganador": pareja_b, "puntos": pts_in_b})
                    st.rerun()

        st.divider()

        # --- MODO EDICIÓN ---
        if st.session_state.editing_mano_index is not None:
            idx = st.session_state.editing_mano_index
            mano_to_edit = st.session_state.historial_manos_actual[idx]
            
            st.warning(f"✏️ Editando Mano #{idx+1}")
            with st.form("form_edit_row"):
                e_col1, e_col2, e_col3 = st.columns([2, 2, 1])
                edit_ganador = e_col1.selectbox("Ganador", [pareja_a, pareja_b], index=0 if mano_to_edit['ganador'] == pareja_a else 1)
                edit_puntos = e_col2.number_input("Puntos", min_value=1, step=1, value=mano_to_edit['puntos'])
                
                if e_col3.form_submit_button("Guardar ✔️"):
                    st.session_state.historial_manos_actual[idx] = {'ganador': edit_ganador, 'puntos': edit_puntos}
                    st.session_state.editing_mano_index = None
                    st.rerun()
            if st.button("❌ Cancelar edición"):
                st.session_state.editing_mano_index = None
                st.rerun()
            st.divider()

        # --- TABLA DE ANOTACIONES ESTILO LISTA ---
        if st.session_state.historial_manos_actual:
            for i, mano in enumerate(st.session_state.historial_manos_actual):
                p_a = mano['puntos'] if mano['ganador'] == pareja_a else 0
                p_b = mano['puntos'] if mano['ganador'] == pareja_b else 0
                
                c_idx, c_pta, c_ptb, c_act1, c_act2 = st.columns([0.5, 2, 2, 0.5, 0.5])
                c_idx.markdown(f"<div style='color: gray; padding-top: 5px; font-size: 0.9em;'>{i+1}</div>", unsafe_allow_html=True)
                c_pta.markdown(f"<div style='text-align: center; font-size: 1.4em;'>{p_a}</div>", unsafe_allow_html=True)
                c_ptb.markdown(f"<div style='text-align: center; font-size: 1.4em;'>{p_b}</div>", unsafe_allow_html=True)
                
                with c_act1:
                    if st.button("✏️", key=f"e_{i}", help="Editar esta mano"):
                        st.session_state.editing_mano_index = i
                        st.rerun()
                with c_act2:
                    if st.button("❌", key=f"d_{i}", help="Borrar esta mano"):
                        st.session_state.historial_manos_actual.pop(i)
                        st.rerun()
                
                st.markdown("<hr style='margin: 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("Escribe los puntos y usa el botón ➕ de arriba para anotar.")

        # --- TOTALES GIGANTES ABAJO ---
        st.write("")
        col_tot_a, col_tot_b = st.columns(2)
        col_tot_a.markdown(f"<div class='totales-gigantes'>{pts_a}<span class='totales-meta'>/{meta}</span></div>", unsafe_allow_html=True)
        col_tot_b.markdown(f"<div class='totales-gigantes'>{pts_b}<span class='totales-meta'>/{meta}</span></div>", unsafe_allow_html=True)

        verificar_ganador_partida(pts_a, pts_b, meta, pareja_a, pareja_b)

    # ==========================================
    # COLUMNA DERECHA (Estadísticas y Espera)
    # ==========================================
    with col_der:
        st.subheader("⏳ En Fila de Espera")
        for i, pareja_espera in enumerate(st.session_state.fila_espera):
            if i == 0: st.info(f"**1. {pareja_espera}** *(Entra en la siguiente)*")
            else: st.write(f"{i+1}. {pareja_espera}")
        
        st.divider()
        st.header("📊 Tabla General")
        datos = [{"Pareja": p, "Victorias": s['victorias'], "Puntos Totales": s['puntos_totales']} for p, s in st.session_state.parejas_stats.items()]
        df_pos = pd.DataFrame(datos).sort_values(by=["Victorias", "Puntos Totales"], ascending=[False, False]).reset_index(drop=True)
        df_pos.index += 1
        st.dataframe(df_pos, use_container_width=True)
        
        st.divider()
        st.header("📜 Historial Completo")
        if st.session_state.historial_partidas:
            st.dataframe(pd.DataFrame(st.session_state.historial_partidas).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("No hay partidas finalizadas aún.")

    st.divider()
    if st.button("⚠️ Terminar Torneo y Reiniciar Datos"):
        st.session_state.clear()
        st.rerun()