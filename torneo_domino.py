import streamlit as st
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="Torneo de Dominó", page_icon="🎲", layout="wide")

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
        st.rerun()

# ==========================================
# FASE 1, 2 y 3 (Configuración Inicial)
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

elif st.session_state.fase == 'orden_inicial':
    st.title("🪑 Orden de Inicio")
    nombres = st.session_state.nombres_parejas
    
    st.subheader("1. La Mesa Principal")
    mesa = st.multiselect("Elige las DOS (2) parejas que inician jugando:", options=nombres, max_selections=2)
    
    if len(mesa) == 2:
        st.divider()
        restantes = [n for n in nombres if n not in mesa]
        st.subheader("2. La Fila de Espera")
        st.info("💡 Selecciona a las parejas restantes **una por una** en el orden exacto.")
        espera = st.multiselect("Elige quién va primero, quién segundo, etc.:", options=restantes)
        
        if len(espera) == len(restantes):
            if st.button("¡Comenzar Torneo! 🎲", type="primary", use_container_width=True):
                st.session_state.mesa_actual = mesa
                st.session_state.fila_espera = espera
                st.session_state.fase = 'torneo'
                st.rerun()

# ==========================================
# FASE 4: Torneo en Curso (HTML PURO PARA MÓVIL SIN SANGRÍA)
# ==========================================
elif st.session_state.fase == 'torneo':
    pareja_a = st.session_state.mesa_actual[0]
    pareja_b = st.session_state.mesa_actual[1]
    meta = st.session_state.meta_puntos

    pts_a, pts_b = recalcular_totales(st.session_state.historial_manos_actual, pareja_a, pareja_b)

    # Verificamos si alguien ya ganó antes de dibujar el marcador
    verificar_ganador_partida(pts_a, pts_b, meta, pareja_a, pareja_b)

    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        # --- GENERADOR DE MARCADOR HTML ---
        # ATENCIÓN: El HTML no debe tener espacios a la izquierda para que Streamlit no lo vuelva un bloque de código.
        html_manos = ""
        for i, mano in enumerate(st.session_state.historial_manos_actual):
            p_a = mano['puntos'] if mano['ganador'] == pareja_a else 0
            p_b = mano['puntos'] if mano['ganador'] == pareja_b else 0
            
            color_a = "#ffffff" if p_a > 0 else "#555555"
            color_b = "#ffffff" if p_b > 0 else "#555555"
            
            html_manos += f"""<div style="display: flex; text-align: center; font-size: 1.4em; padding: 6px 0; border-bottom: 1px solid #222;">
<div style="width: 50%; color: {color_a}; border-right: 1px solid #333;">{p_a}</div>
<div style="width: 50%; color: {color_b};">{p_b}</div>
</div>"""

        if not html_manos:
            html_manos = "<div style='text-align: center; color: #666; padding: 20px; font-style: italic;'>Inicia la partida agregando puntos abajo</div>"

        html_marcador = f"""<div style="background-color: #0d0d0d; padding: 15px; border-radius: 12px; color: white; border: 2px solid #2a2a2a; margin-bottom: 20px; font-family: sans-serif;">
<div style="display: flex; text-align: center; font-size: 1.3em; font-weight: bold; padding-bottom: 10px; border-bottom: 2px solid #333;">
<div style="width: 50%; border-right: 2px solid #333; padding: 0 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{pareja_a}</div>
<div style="width: 50%; padding: 0 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{pareja_b}</div>
</div>
<div style="padding: 10px 0; min-height: 120px;">
{html_manos}
</div>
<div style="display: flex; text-align: center; border-top: 2px solid #333; padding-top: 15px;">
<div style="width: 50%; border-right: 2px solid #333;">
<div style="font-size: 3.5em; font-weight: bold; line-height: 1;">{pts_a}</div>
<div style="color: #888; font-size: 0.9em; margin-top: 5px;">/ {meta}</div>
</div>
<div style="width: 50%;">
<div style="font-size: 3.5em; font-weight: bold; line-height: 1;">{pts_b}</div>
<div style="color: #888; font-size: 0.9em; margin-top: 5px;">/ {meta}</div>
</div>
</div>
</div>"""
        
        # Inyectamos el HTML sin indentación
        st.markdown(html_marcador, unsafe_allow_html=True)

        # --- FORMULARIO PARA ANOTAR PUNTOS ---
        st.markdown("### ✍️ Anotar")
        with st.form("form_anotar", clear_on_submit=True):
            ganador = st.radio("¿Quién ganó?", [pareja_a, pareja_b], horizontal=True, label_visibility="collapsed")
            c1, c2 = st.columns([2, 1])
            puntos = c1.number_input("Puntos", min_value=1, step=1, value=10, label_visibility="collapsed")
            submit = c2.form_submit_button("➕ Añadir", type="primary", use_container_width=True)
            
            if submit:
                st.session_state.historial_manos_actual.append({"ganador": ganador, "puntos": puntos})
                st.rerun()

        # --- CORRECCIONES ---
        st.write("")
        with st.expander("🛠️ Corregir / Borrar Manos"):
            if st.session_state.historial_manos_actual:
                opciones = [f"Mano {i+1}: {m['puntos']} pts ({m['ganador']})" for i, m in enumerate(st.session_state.historial_manos_actual)]
                seleccion = st.selectbox("Selecciona la mano:", opciones)
                idx = opciones.index(seleccion)
                mano_to_edit = st.session_state.historial_manos_actual[idx]
                
                with st.form("form_edit_row"):
                    edit_ganador = st.radio("Corregir Ganador", [pareja_a, pareja_b], index=0 if mano_to_edit['ganador'] == pareja_a else 1, horizontal=True)
                    edit_puntos = st.number_input("Corregir Puntos", min_value=1, step=1, value=mano_to_edit['puntos'])
                    if st.form_submit_button("✔️ Guardar Cambios", use_container_width=True):
                        st.session_state.historial_manos_actual[idx] = {'ganador': edit_ganador, 'puntos': edit_puntos}
                        st.rerun()
                
                if st.button("❌ Borrar esta mano", use_container_width=True):
                    st.session_state.historial_manos_actual.pop(idx)
                    st.rerun()
            else:
                st.write("Aún no hay puntos para corregir.")

    # ==========================================
    # COLUMNA DERECHA (Estadísticas y Espera)
    # ==========================================
    with col_der:
        st.subheader("⏳ Fila de Espera")
        for i, pareja_espera in enumerate(st.session_state.fila_espera):
            if i == 0: st.success(f"**1. {pareja_espera}** *(Siguientes)*")
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