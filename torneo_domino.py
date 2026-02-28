import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components

# 1. Configuración de la página
st.set_page_config(page_title="Anotador de Dominó", page_icon="🎲", layout="wide")

# CSS para forzar que el formulario se mantenga en 1 sola línea en celulares
st.markdown("""
<style>
[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 10px !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] > div {
    flex: 1 1 0% !important;
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# CÓDIGO ANTI-SUEÑO (Wake Lock API)
# ==========================================
components.html(
    """
    <script>
    let wakeLock = null;
    const requestWakeLock = async () => {
        try {
            if ('wakeLock' in navigator) {
                wakeLock = await navigator.wakeLock.request('screen');
            }
        } catch (err) {
            console.log('No se pudo activar.');
        }
    };
    document.addEventListener('click', requestWakeLock, { once: true });
    requestWakeLock();
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') requestWakeLock();
    });
    </script>
    """,
    height=0, width=0
)

# ==========================================
# FUNCIONES DE AUTO-GUARDADO (SALAS)
# ==========================================
def obtener_archivo_backup():
    if 'sala' in st.session_state and st.session_state.sala:
        # Limpiar el nombre de la sala para evitar errores en el archivo
        nombre_limpio = "".join(x for x in st.session_state.sala if x.isalnum())
        return f"backup_{nombre_limpio}.json"
    return None

def guardar_backup():
    archivo = obtener_archivo_backup()
    if archivo:
        datos = {
            'fase': st.session_state.fase,
            'modo_juego': st.session_state.modo_juego,
            'num_parejas': st.session_state.num_parejas,
            'nombres_parejas': st.session_state.nombres_parejas,
            'parejas_stats': st.session_state.parejas_stats,
            'mesa_actual': st.session_state.mesa_actual,
            'fila_espera': st.session_state.fila_espera,
            'historial_partidas': st.session_state.historial_partidas,
            'historial_manos_actual': st.session_state.historial_manos_actual,
            'meta_puntos': st.session_state.meta_puntos
        }
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f)

def cargar_backup(nombre_sala):
    nombre_limpio = "".join(x for x in nombre_sala if x.isalnum())
    archivo = f"backup_{nombre_limpio}.json"
    if os.path.exists(archivo):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                for key, value in datos.items():
                    st.session_state[key] = value
            return True
        except:
            return False
    return False

def borrar_backup():
    archivo = obtener_archivo_backup()
    if archivo and os.path.exists(archivo):
        os.remove(archivo)

# 2. Inicializar variables de estado
if 'fase' not in st.session_state:
    st.session_state.fase = 'inicio_sala'
if 'sala' not in st.session_state:
    st.session_state.sala = ""
if 'modo_juego' not in st.session_state:
    st.session_state.modo_juego = 'torneo'
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
        
        if st.session_state.modo_juego == 'torneo':
            st.session_state.fila_espera.append(perdedor_partida)
            siguiente = st.session_state.fila_espera.pop(0)
            st.session_state.mesa_actual = [ganador_partida, siguiente]
        
        st.session_state.historial_manos_actual = []
        guardar_backup()
        st.rerun()

def convertir_df_a_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# ==========================================
# FASE 0: INICIO Y RECUPERACIÓN DE SALA (NUEVO)
# ==========================================
if st.session_state.fase == 'inicio_sala':
    st.title("🎲 Anotador de Dominó")
    st.info("💡 Crea un nombre para tu mesa. Si tu teléfono recarga la página, vuelve a escribir el mismo nombre para recuperar tu partida exacta.")
    
    with st.form("form_sala"):
        sala_input = st.text_input("Nombre de la Mesa / Partida", placeholder="Ej: MesaViernes", value="Mesa1")
        submit = st.form_submit_button("Entrar / Recuperar 🚀", type="primary", use_container_width=True)
        
        if submit:
            if sala_input.strip() == "":
                st.error("Escribe un nombre para la sala.")
            else:
                st.session_state.sala = sala_input
                # Intentamos cargar si ya existía
                if cargar_backup(sala_input):
                    st.toast("¡Partida recuperada con éxito!", icon="✅")
                    st.rerun()
                else:
                    # Si no existía, pasamos a elegir el modo
                    st.session_state.fase = 'seleccion_modo'
                    st.rerun()

# ==========================================
# FASE 0.5: SELECCIÓN DE MODO
# ==========================================
elif st.session_state.fase == 'seleccion_modo':
    st.title(f"Mesa: {st.session_state.sala}")
    st.subheader("¿Cómo van a jugar hoy?")
    
    modo = st.radio("Elige el formato:", ["🏆 Torneo (Rey de la mesa)", "⚔️ Duelo Fijo (Solo 2 parejas)"], index=0)
    
    if st.button("Siguiente 👉", type="primary", use_container_width=True):
        st.session_state.modo_juego = 'torneo' if "Torneo" in modo else 'duelo'
        if st.session_state.modo_juego == 'duelo': st.session_state.num_parejas = 2
        st.session_state.fase = 'configuracion'
        guardar_backup()
        st.rerun()

# ==========================================
# FASE 1: CONFIGURACIÓN
# ==========================================
elif st.session_state.fase == 'configuracion':
    st.title("⚙️ Configuración")
    
    if st.session_state.modo_juego == 'torneo':
        cantidad = st.number_input("Cantidad total de parejas jugando", min_value=3, max_value=20, value=4, step=1)
    else:
        st.info("Modo Duelo Fijo: Se jugará un mano a mano constante entre 2 parejas.")
        cantidad = 2
        
    meta = st.number_input("¿A cuántos puntos se gana la partida? (La Meta)", min_value=50, max_value=500, value=200, step=50)
    
    if st.button("Siguiente 👉"):
        st.session_state.num_parejas = cantidad
        st.session_state.meta_puntos = meta
        st.session_state.fase = 'registro'
        guardar_backup()
        st.rerun()

# ==========================================
# FASE 2: REGISTRO DE NOMBRES
# ==========================================
elif st.session_state.fase == 'registro':
    st.title("📝 Nombres de las Parejas")
    with st.form("form_nombres"):
        nombres_input = [st.text_input(f"Nombre Pareja {i+1}", f"Pareja {i+1}") for i in range(st.session_state.num_parejas)]
        if st.form_submit_button("Guardar Nombres 💾"):
            if len(set(nombres_input)) < len(nombres_input):
                st.error("Usa nombres diferentes para cada pareja.")
            else:
                st.session_state.nombres_parejas = nombres_input
                st.session_state.parejas_stats = {nom: {'victorias': 0, 'puntos_totales': 0} for nom in nombres_input}
                
                if st.session_state.modo_juego == 'torneo':
                    st.session_state.fase = 'orden_inicial'
                else:
                    st.session_state.mesa_actual = [nombres_input[0], nombres_input[1]]
                    st.session_state.fila_espera = []
                    st.session_state.fase = 'torneo'
                guardar_backup()
                st.rerun()

# ==========================================
# FASE 3: ORDEN (SÓLO PARA TORNEO)
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
        st.info("💡 Selecciona a las parejas restantes **una por una** en el orden exacto.")
        espera = st.multiselect("Elige quién va primero, quién segundo, etc.:", options=restantes)
        
        if len(espera) == len(restantes):
            if st.button("¡Comenzar Torneo! 🎲", type="primary", use_container_width=True):
                st.session_state.mesa_actual = mesa
                st.session_state.fila_espera = espera
                st.session_state.fase = 'torneo'
                guardar_backup()
                st.rerun()

# ==========================================
# FASE 4: PARTIDA EN CURSO
# ==========================================
elif st.session_state.fase == 'torneo':
    pareja_a = st.session_state.mesa_actual[0]
    pareja_b = st.session_state.mesa_actual[1]
    meta = st.session_state.meta_puntos

    pts_a, pts_b = recalcular_totales(st.session_state.historial_manos_actual, pareja_a, pareja_b)
    verificar_ganador_partida(pts_a, pts_b, meta, pareja_a, pareja_b)

    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        st.markdown("### ✍️ Anotar Rápido")
        
        # --- FORMULARIO EQUIPO A ---
        with st.form("form_a", clear_on_submit=True):
            ca1, ca2, ca3 = st.columns([1.5, 1, 1])
            ca1.markdown(f"<div style='font-size:1.1em; font-weight:bold; padding-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>🔵 {pareja_a}</div>", unsafe_allow_html=True)
            pts_a_input = ca2.text_input("pts_a", value="", placeholder="Pts...", label_visibility="collapsed")
            submit_a = ca3.form_submit_button("➕ Añadir", type="primary", use_container_width=True)
            
            if submit_a:
                if pts_a_input.strip().isdigit() and int(pts_a_input) > 0:
                    st.session_state.historial_manos_actual.append({"ganador": pareja_a, "puntos": int(pts_a_input)})
                    guardar_backup()
                    st.rerun()
                elif pts_a_input.strip() != "":
                    st.warning("⚠️ Número inválido")

        # --- FORMULARIO EQUIPO B ---
        with st.form("form_b", clear_on_submit=True):
            cb1, cb2, cb3 = st.columns([1.5, 1, 1])
            cb1.markdown(f"<div style='font-size:1.1em; font-weight:bold; padding-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>🔴 {pareja_b}</div>", unsafe_allow_html=True)
            pts_b_input = cb2.text_input("pts_b", value="", placeholder="Pts...", label_visibility="collapsed")
            submit_b = cb3.form_submit_button("➕ Añadir", type="primary", use_container_width=True)
            
            if submit_b:
                if pts_b_input.strip().isdigit() and int(pts_b_input) > 0:
                    st.session_state.historial_manos_actual.append({"ganador": pareja_b, "puntos": int(pts_b_input)})
                    guardar_backup()
                    st.rerun()
                elif pts_b_input.strip() != "":
                    st.warning("⚠️ Número inválido")

        st.write("") 

        # --- MARCADOR HTML ---
        html_manos = ""
        for i, mano in enumerate(st.session_state.historial_manos_actual):
            p_a = mano['puntos'] if mano['ganador'] == pareja_a else 0
            p_b = mano['puntos'] if mano['ganador'] == pareja_b else 0
            c_a = "#ffffff" if p_a > 0 else "#555555"
            c_b = "#ffffff" if p_b > 0 else "#555555"
            html_manos += f"<div style='display:flex; text-align:center; font-size:1.4em; padding:6px 0; border-bottom:1px solid #222;'><div style='width:50%; color:{c_a}; border-right:1px solid #333;'>{p_a}</div><div style='width:50%; color:{c_b};'>{p_b}</div></div>"

        if not html_manos:
            html_manos = "<div style='text-align:center; color:#666; padding:20px; font-style:italic;'>Inicia la partida agregando puntos arriba</div>"

        html_marcador = f"<div style='background-color:#0d0d0d; padding:15px; border-radius:12px; color:white; border:2px solid #2a2a2a; margin-bottom:20px; font-family:sans-serif;'><div style='display:flex; text-align:center; font-size:1.3em; font-weight:bold; padding-bottom:10px; border-bottom:2px solid #333;'><div style='width:50%; border-right:2px solid #333; padding:0 5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{pareja_a}</div><div style='width:50%; padding:0 5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{pareja_b}</div></div><div style='padding:10px 0; min-height:120px;'>{html_manos}</div><div style='display:flex; text-align:center; border-top:2px solid #333; padding-top:15px;'><div style='width:50%; border-right:2px solid #333;'><div style='font-size:3.5em; font-weight:bold; line-height:1;'>{pts_a}</div><div style='color:#888; font-size:0.9em; margin-top:5px;'>/ {meta}</div></div><div style='width:50%;'><div style='font-size:3.5em; font-weight:bold; line-height:1;'>{pts_b}</div><div style='color:#888; font-size:0.9em; margin-top:5px;'>/ {meta}</div></div></div></div>"
        st.markdown(html_marcador, unsafe_allow_html=True)

        components.html(
            """
            <script>
            const inputs = window.parent.document.querySelectorAll('input[placeholder="Pts..."]');
            inputs.forEach(function(input) {
                input.setAttribute('inputmode', 'numeric');
                input.setAttribute('pattern', '[0-9]*');
            });
            </script>
            """,
            height=0, width=0
        )

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
                        guardar_backup()
                        st.rerun()
                
                if st.button("❌ Borrar esta mano", use_container_width=True):
                    st.session_state.historial_manos_actual.pop(idx)
                    guardar_backup()
                    st.rerun()
            else:
                st.write("Aún no hay puntos para corregir.")

    with col_der:
        if st.session_state.modo_juego == 'torneo':
            st.subheader("⏳ Fila de Espera")
            for i, pareja_espera in enumerate(st.session_state.fila_espera):
                if i == 0: st.success(f"**1. {pareja_espera}** *(Siguientes)*")
                else: st.write(f"{i+1}. {pareja_espera}")
            st.divider()
        else:
            st.info("⚔️ **Modo Duelo Activo:** Las parejas juegan directo sin rotaciones.")
            st.divider()

        st.header("📊 Tabla General")
        datos = [{"Pareja": p, "Victorias": s['victorias'], "Puntos Totales": s['puntos_totales']} for p, s in st.session_state.parejas_stats.items()]
        df_pos = pd.DataFrame(datos).sort_values(by=["Victorias", "Puntos Totales"], ascending=[False, False]).reset_index(drop=True)
        df_pos.index += 1
        st.dataframe(df_pos, use_container_width=True)
        
        st.divider()
        st.header("📜 Historial Completo")
        if st.session_state.historial_partidas:
            df_historial = pd.DataFrame(st.session_state.historial_partidas)
            st.dataframe(df_historial.iloc[::-1], use_container_width=True, hide_index=True)
            
            csv = convertir_df_a_csv(df_historial)
            st.download_button(
                label="📥 Descargar Historial (Excel/CSV)",
                data=csv,
                file_name='historial_domino.csv',
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.info("No hay partidas finalizadas aún.")

    st.divider()
    if st.button("⚠️ Terminar y Reiniciar TODO", type="secondary"):
        borrar_backup()
        st.session_state.clear()
        st.rerun()