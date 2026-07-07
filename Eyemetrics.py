import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# 1. CONFIGURACIÓN DE LA PÁGINA Y VARIABLES
st.set_page_config(page_title="Análisis de métricas oculares", layout="wide")

# Inicialización de variables de estado para la navegación y ajustes
if 'dispositivo' not in st.session_state:
    st.session_state.dispositivo = None
if 'min_f' not in st.session_state: st.session_state.min_f = 5
if 'max_f' not in st.session_state: st.session_state.max_f = 40
if 'req_sac_pre' not in st.session_state: st.session_state.req_sac_pre = True
if 'req_sac_post' not in st.session_state: st.session_state.req_sac_post = True
if 'min_sac_post' not in st.session_state: st.session_state.min_sac_post = 2
if 'max_sac_post' not in st.session_state: st.session_state.max_sac_post = 10
if 'req_vel_post' not in st.session_state: st.session_state.req_vel_post = False
if 'min_vel_post' not in st.session_state: st.session_state.min_vel_post = 200.0
if 'max_vel_post' not in st.session_state: st.session_state.max_vel_post = 350.0


# 2. FUNCIONES AUXILIARES
def limpiar_señal(serie_pupila, serie_validez, serie_movimiento, freq_hz=100, margen_ms=250, umbral_min=2.0, max_salto=0.1):
    s = serie_pupila.copy()
    s[serie_validez != 'Valid'] = np.nan
    s[serie_movimiento == 'Saccade'] = np.nan
    diff = s.diff().abs()
    s[diff > max_salto] = np.nan
    s[s < umbral_min] = np.nan
    muestras_margen = int((margen_ms / 1000) * freq_hz)
    mask = s.isna()
    mask_expandida = mask.rolling(window=muestras_margen*2, center=True).max().fillna(0).astype(bool)
    s[mask_expandida] = np.nan
    return s.interpolate(method='linear', limit_direction='both')

def generar_grafica_baseline(df_seg, val_base_izq, val_base_der, duracion_base_ms=200):
    tiempo_relativo = df_seg['Tiempo (s)'] - df_seg['Tiempo (s)'].iloc[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tiempo_relativo, y=df_seg['pupila_izq_corr'], name="Ojo Izquierdo (Corregido)", mode='lines', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=tiempo_relativo, y=df_seg['pupila_der_corr'], name="Ojo Derecho (Corregido)", mode='lines', line=dict(color='blue')))
    fig.add_vline(x=duracion_base_ms/1000, line_dash="dash", line_color="black", annotation_text="Fin Baseline")
    fig.update_layout(
        title="Cambio en el Tamaño de la Pupila (Corrección Sustractiva)",
        xaxis_title="Tiempo (s)", yaxis_title=" Incremento Diámetro de pupila (mm)",
        hovermode="x unified",
        shapes=[dict(type='line', yref='y', y0=0, y1=0, xref='paper', x0=0, x1=1, line=dict(color='black', width=1, dash='dot'))]
    )
    return fig



# 3. INTERFAZ 
# PANTALLA DE INICIO: SELECCIÓN DE DISPOSITIVO 
if st.session_state.dispositivo is None:
    st.title("Selecciona tu dispositivo")
    st.write("Elige la tecnología de eye-tracking utilizada para el experimento.")

    col1, col2 = st.columns(2) # (O las proporciones que hayas usado)
    
    with col1:
        # Foto de Tobii Pro Glasses 3 y botón de selección
        margen_izq1, col_img1, margen_der1 = st.columns([1, 2, 1])
        with col_img1:
            try:
                # Volvemos a usar use_container_width=True para que se adapte a su sub-columna
                st.image("tobii_img.png", use_container_width=True)
            except:
                st.info("Imagen de Tobii")
                
        if st.button("Tobii Pro Glasses 3", use_container_width=True):
            st.session_state.dispositivo = "Tobii"
            st.rerun()
            
        # Guía de exportación desde Tobii Pro Glasses 3
        with st.popover("Guía de exportación desde Tobii", use_container_width=True):
            st.subheader("Paso 1: Descarga de grabación en Tobii Controller App")
            st.image("Paso1_tobii.png", use_container_width=True)
            st.write("Una vez realizada la grabación, se busca en el menú de la Controller App la pestaña ‘Play Recordings’. " \
            "En ella, aparecerán todas las grabaciones realizadas con el dispositivo que se hayan guardado en la tarjeta SD que esté insertada en la unidad de grabación. " \
            "Se selecciona la que se quiera descargar y se presiona el icono de descarga. " \
            "Se debe seleccionar la opción ‘Recording folder’ para descargar todos los datos.")
            st.subheader("Paso 2: Creación de proyecto en Tobii Pro Lab")
            st.image("Paso2_tobii.png", use_container_width=True)
            st.write("Una vez descargada la grabación en el ordenador, se abre el programa Tobii Pro Lab y se crea un nuevo proyecto en el menú Create new Project. " \
            "Como se ve en la imagen, habrá que seleccionar ‘Glasses’ como tipo de proyecto para crear.")
            st.subheader("Paso 3: Importación de grabación de Tobii Pro Glasses")
            st.image("Paso3_tobii.png", use_container_width=True)
            st.write("Un proyecto puede estar formado por varias grabaciones. " \
            "Al ser un proyecto nuevo, no aparecerán grabaciones disponibles, habrá que pulsar el botón ‘Import’, " \
            "seleccionar ‘Glasses 3 recordings’ y buscar la carpeta en la que se encuentre la grabación de las Tobii que se ha descargado anteriormente.")
            st.subheader("Paso 4: Exportación de datos en Excel")
            st.image("Paso4_tobii.png", use_container_width=True)
            st.write("Una vez seleccionada la grabación, se hace clic en el botón Data Export. " \
            "Aparecerá una interfaz con la configuración del archivo que se quiere descargar. " \
            "En el menú de la derecha 'Settings' se debe escoger el formato 'Single Excel File' para exportar. " \
            "El archivo mostrará, para cada registro (cada 10 ms), el valor de cada parámetro de seguimiento ocular." \
            "Es importante no seleccionar valores de los sensores adicionales (acelerómetro, giroscopio y magnetómetro) para la exportación para evitar errores en la interpretación de datos")

    with col2:
        # Foto de Gazepoint GP3 y botón de selección
        margen_izq2, col_img2, margen_der2 = st.columns([1, 2, 1])
        
        with col_img2:
            try:
                st.image("gazepoint_img.png", use_container_width=True)
            except:
                st.info("Imagen de Gazepoint")
                
        if st.button("Gazepoint GP3", use_container_width=True):
            st.session_state.dispositivo = "Gazepoint"
            st.rerun()

        # Guía de exportación desde Gazepoint GP3
        with st.popover("Guía de exportación desde Gazepoint", use_container_width=True):
            st.subheader("Paso 1: Creación de proyecto en Gazepoint Analysis")
            st.image("Paso1_GP3.png", use_container_width=True)
            st.write("Pulsar ‘New Project’ en el selector de proyectos que aparece al abrir la aplicación.")
            st.subheader("Paso 2: Selección de ubicación para el proyecto")
            st.image("Paso2_GP3.png", use_container_width=True)
            st.write("Seleccionar la carpeta en la que se quiere guardar el nuevo proyecto." \
            "No se podrá escoger una carpeta en la que ya exista un proyecto realizado con anterioridad. ")
            st.subheader("Paso 3: Realización de grabación")
            st.image("Paso3_GP3.png", use_container_width=True)
            st.write("Al abrir la interfaz de Gazepoint Analysis, se mostrará una previsualización en tiempo real de la pantalla actual. " \
            "A continuación, para comenzar a grabar, se debe hacer clic en el botón ‘Start Record’ situado en la barra de herramientas superior. " \
            "Para detener la grabación, se debe de pulsar el botón ‘Stop Record’, que se encuentra en la misma posición que el de inicio de grabación. " \
            "Al detener una grabación se cerrará el programa.")
            st.subheader("Paso 4: Abrir el proyecto en modo exportación de datos")
            st.image("Paso4_GP3.png", use_container_width=True)
            st.write("Para extraer los datos de eye-tracking de una grabación de Gazepoint GP3 primero se debe abrir el proyecto creado anteriormente en Gazepoint Analysis, que se había guardado en una carpeta conocida." \
            "Al abrirlo, se debe seleccionar el modo ‘Analyze data’ de la barra de herramientas superior y pulsar el botón ‘Export’.")
            st.subheader("Paso 5: Descarga de archivo CSV con los datos")
            st.image("Paso5_GP3.png", use_container_width=True)
            st.write("Tras pulsar ‘Export’ se abrirá una ventana que permite configurar el archivo que se va a descargar." \
            "En ‘Select CSV Data’ se puede seleccionar las métricas que se quieren extraer." \
            "Pulsando ‘Export CSV Data’ se descargará en la carpeta del proyecto el archivo con los datos de eye-tracking." \
            "Se encuentra en la carpeta llamada ‘result’, y es el archivo CSV que finaliza en ‘all_gaze’")

# PANTALLA DE CARGA DE ARCHIVOS 
else:
    st.title(f"Análisis de Métricas Oculares - {st.session_state.dispositivo}")
    
    # Botón para volver atrás
    if st.button("← Cambiar dispositivo"):
        st.session_state.dispositivo = None
        st.rerun()
        
    st.divider()
    
    # Botón para subir archivos
    if st.session_state.dispositivo == "Tobii":
        texto_carga = "Introduce tu archivo de datos de Tobii (Excel)"
        tipo_archivo = ["xlsx"]
    else:
        texto_carga = "Introduce tu archivo de datos de Gazepoint (CSV)"
        tipo_archivo = ["csv"]

    archivo_subido = st.file_uploader(texto_carga, type=tipo_archivo)

    
    if archivo_subido is not None:
        
        # Lectura de archivo y comprobación de carga
        try:
            if st.session_state.dispositivo == "Tobii":
                df_datos = pd.read_excel(archivo_subido)
            else:
                df_datos = pd.read_csv(archivo_subido, sep=None, engine='python')
                
            st.success("Archivo cargado correctamente. Navega por las pestañas para ver el análisis.")
            
            # PESTAÑAS
            tab_contador, tab_pupilometria = st.tabs(["Parpadeos", "Pupilometría"])

            # PESTAÑA: PARPADEOS

            with tab_contador:
                df = df_datos.copy() 
                
                # GAZEPOINT
                # Se buscan las columnas de tiempo, parpadeos y duración de parpadeos
                if st.session_state.dispositivo == "Gazepoint":
                    df.columns = df.columns.str.strip()
                    posibles_time_cols = [c for c in df.columns if "TIME" in c.upper()]
                    posibles_bkid_cols = [c for c in df.columns if "BKID" in c.upper()]
                    posibles_bkdur_cols = [c for c in df.columns if "BKDUR" in c.upper()]
                    
                    if not posibles_time_cols:
                        st.error("❌ No se encontró la columna de tiempo.")
                    elif not posibles_bkid_cols:
                        st.error("❌ El archivo no contiene la columna 'BKID'.")
                    elif not posibles_bkdur_cols:
                        st.error("❌ El archivo no contiene la columna 'BKDUR' (Duración del parpadeo). Asegúrate de marcarla al exportar en Gazepoint.")
                    else:
                        time_col = posibles_time_cols[0]
                        bkid_col = posibles_bkid_cols[0]
                        bkdur_col = posibles_bkdur_cols[0]

                        # Limpieza de números con notación distinta 
                        def parsear_columna(serie):
                            s = serie.astype(str).str.strip()
                            
                            def limpiar_val(x):
                                if pd.isna(x) or x.lower() == 'nan' or x == 'none':
                                    return np.nan
                                
                                # Si tiene más de un punto (ej: "1.000.488"), se quitan todos menos el último
                                if x.count('.') > 1:
                                    partes = x.rsplit('.', 1)
                                    x = partes[0].replace('.', '') + '.' + partes[1]
                                
                                # Si tiene coma y punto (ej: "1,000.48" o "1.000,48")
                                elif ',' in x and '.' in x:
                                    if x.rfind(',') > x.rfind('.'):
                                        x = x.replace('.', '').replace(',', '.')
                                    else:
                                        x = x.replace(',', '')
                                
                                # Si solo tiene coma (ej: "1000,48")
                                elif ',' in x:
                                    x = x.replace(',', '.')
                                    
                                try:
                                    return float(x)
                                except:
                                    return np.nan
                                    
                            return s.apply(limpiar_val)

                        # Se aplica la limpieza a las columnas de tiempo y duración de parpadeos
                        df[time_col] = parsear_columna(df[time_col])
                        df[bkdur_col] = parsear_columna(df[bkdur_col])
                        df[bkid_col] = pd.to_numeric(df[bkid_col], errors='coerce')

                        df_blinks = df[df[bkdur_col] > 0].copy()

                        if df_blinks.empty:
                            st.warning("⚠️ No se detectaron parpadeos válidos (BKDUR > 0) en este archivo.")
                        else:
                            # Recopilación de datos de parpadeos
                            resumen = pd.DataFrame()
                            resumen["Parpadeo_ID"] = df_blinks[bkid_col].astype(int)
                            resumen["Fin (s)"] = df_blinks[time_col].round(4)
                            resumen["Duración (s)"] = df_blinks[bkdur_col].round(4)
                            
                            # Cálculo del inicio restando la duración real al tiempo final
                            resumen["Inicio (s)"] = (resumen["Fin (s)"] - resumen["Duración (s)"]).round(4)
                            
                            # Orden de columnas y creación del índice visual
                            resumen["Parpadeo"] = range(1, len(resumen) + 1)
                            
                            st.success(f"Se han detectado **{len(resumen)}** parpadeos.")

                            # Redondeo de decimales 
                            resumen["Inicio (s)"] = resumen["Inicio (s)"].round(3)
                            resumen["Fin (s)"] = resumen["Fin (s)"].round(3)
                            resumen["Duración (s)"] = resumen["Duración (s)"].round(4)

                            # FIGURAS
                            # Tabla de parpadeos
                            st.dataframe(resumen[["Parpadeo", "Inicio (s)", "Fin (s)", "Duración (s)"]], use_container_width=True, hide_index=True)               
                            st.divider()

                            # Gráfico de parpadeos a lo largo del tiempo
                            st.subheader("Parpadeos a lo largo del tiempo")
                            resumen["Duración (ms)"] = (resumen["Duración (s)"] * 1000).round(1)
                            fig_gp = go.Figure()
                            fig_gp.add_trace(go.Bar(
                                x=resumen["Inicio (s)"], y=resumen["Duración (ms)"], width=0.3, marker_color="#29B244",
                                hovertemplate="<b>Parpadeo #%{customdata}</b><br>Tiempo: %{x:.3f} s<br>Duración: %{y} ms<extra></extra>",
                                customdata=resumen["Parpadeo"], name="Parpadeo"
                            ))
                            fig_gp.update_layout(xaxis_title="Tiempo (s)", yaxis_title="Duración (ms)", hovermode="closest", bargap=0, yaxis=dict(rangemode="tozero"))
                            st.plotly_chart(fig_gp, use_container_width=True)

                            # Métricas adicionales
                            st.divider()
                            duracion_total_gp = df[time_col].max() - df[time_col].min()
                            frec_min_gp = (len(resumen) / duracion_total_gp) * 60
                            dur_media_ms_gp = round(resumen["Duración (ms)"].mean())
                            col_m1, col_m2 = st.columns(2)
                            col_m1.metric("Frecuencia media de parpadeo", f"{frec_min_gp:.0f} parpadeos/min")
                            col_m2.metric("Duración media del parpadeo", f"{dur_media_ms_gp} ms")

                            # Evolución de la frecuencia de parpadeo
                            st.divider()
                            st.subheader("Evolución de la Frecuencia de Parpadeo")
                            tiempo_max = int(resumen["Inicio (s)"].max()) + 10 
                            eje_x = np.arange(0, tiempo_max, 1)
                            eje_y = []
                            for t in eje_x:
                                parpadeos_ventana = ((resumen["Inicio (s)"] > t - 60) & (resumen["Inicio (s)"] <= t)).sum()
                                eje_y.append(parpadeos_ventana)
                            fig_tendencia = go.Figure()
                            fig_tendencia.add_trace(go.Scatter(
                                x=eje_x, 
                                y=eje_y, 
                                mode='lines', 
                                name='Parpadeos / min',
                                line=dict(color="#29B244", width=2), 
                                fill='tozeroy', # Rellena la zona inferior para darle aspecto de área
                                fillcolor="#8AEF9E"
                            ))
                            fig_tendencia.update_layout(
                                xaxis_title="Tiempo (s)", 
                                yaxis_title="Parpadeos/minuto",
                                hovermode="x unified",
                                yaxis=dict(rangemode="tozero") # Evita que el eje Y flote por encima del cero
                            )
                            st.plotly_chart(fig_tendencia, use_container_width=True)
                            
                            # Distribución de parpadeos por duración
                            st.divider()
                            st.subheader("Distribución de parpadeos por duración")
                            df_counts_gp = resumen.assign(ms_round=resumen["Duración (ms)"].round(-1).astype(int)).groupby("ms_round").size().reset_index(name="Cantidad").sort_values("ms_round")
                            fig_dist_gp = px.bar(df_counts_gp, x="ms_round", y="Cantidad", labels={"ms_round": "Duración (ms)", "Cantidad": "Número de Parpadeos"}, text_auto=True, template="plotly_dark", color_discrete_sequence=["#29B244"])
                            fig_dist_gp.update_xaxes(type="linear", tickmode="linear", dtick=10)
                            fig_dist_gp.update_layout(bargap=0.2)
                            st.plotly_chart(fig_dist_gp, use_container_width=True)
                
                # TOBII PRO GLASSES 3
                elif st.session_state.dispositivo == "Tobii":
                    
                    # Botón para ajustar los parámetros de parpadeos
                    with st.popover("Ajustar parámetros de parpadeo", use_container_width=True):
                        st.write("Define las condiciones para identificar un parpadeo.")
                        st.subheader("Duración del parpadeo (filas de Excel, cada fila equivale a 10 ms)")
                        
                        # Duración en filas del parpadeo
                        c1, c2 = st.columns(2)
                        with c1: st.session_state.min_f = st.number_input("Mínimo de filas:", min_value=1, value=st.session_state.min_f)
                        with c2: st.session_state.max_f = st.number_input("Máximo de filas:", min_value=1, value=st.session_state.max_f)
                        st.info(f"Configuración actual: Bloques de {st.session_state.min_f} a {st.session_state.max_f} filas.")
                        with st.popover("ⓘ"):
                            st.write("La duración se mide en número de filas consecutivas de 'EyesNotFound'.")
                            st.image("ayuda1.png", caption="Esquema de duración del parpadeo")

                        # Requerimiento de 'Saccade' antes del parpadeo
                        st.subheader("Condición anterior")
                        st.session_state.req_sac_pre = st.checkbox("Considerar sacada antes del parpadeo", value=st.session_state.req_sac_pre)
                        if st.session_state.req_sac_pre: st.warning("Se ignorarán los parpadeos que no tengan una sacada previa registrada.")
                        with st.popover("ⓘ"):
                            st.write("El algoritmo busca una etiqueta 'Saccade' justo antes del inicio del parpadeo.")
                            st.image("ayuda2.png", caption="Ejemplo de sacada previa al parpadeo")

                        # Requerimiento de 'Saccade' después del parpadeo
                        st.subheader("Condición Posterior")
                        st.session_state.req_sac_post = st.checkbox("Considerar sacada después del parpadeo", value=st.session_state.req_sac_post)

                        if st.session_state.req_sac_post:
                            c3, c4 = st.columns(2)
                            st.session_state.min_sac_post = c3.number_input("Mínimo filas sacada:", min_value=1, value=st.session_state.min_sac_post)
                            st.session_state.max_sac_post = c4.number_input("Máximo filas sacada:", min_value=1, value=st.session_state.max_sac_post)
                            with st.popover("ⓘ"):
                                st.write("Se analiza si existe un movimiento sacádico inmediatamente después del parpadeo.")
                                st.image("ayuda3.png", caption="Ejemplo de sacada posterior al parpadeo")
                            
                            # Velocidad angular
                            st.session_state.req_vel_post = st.checkbox("Filtrar por velocidad angular pico (º/s)", value=st.session_state.req_vel_post)
                            
                            if st.session_state.req_vel_post:
                                cv1, cv2 = st.columns(2)
                                st.session_state.min_vel_post = cv1.number_input("Velocidad pico mínima (º/s):", min_value=0.0, value=st.session_state.min_vel_post)
                                st.session_state.max_vel_post = cv2.number_input("Velocidad pico máxima (º/s):", min_value=0.0, value=st.session_state.max_vel_post)
                            with st.popover("ⓘ"):
                                st.write("Se analiza la velocidad angular máxima del ojo durante el movimiento sacádico posterior.")
                                st.image("ayuda4.png", caption="Esquema del cálculo de la velocidad angular")
                                                            
                    st.divider() # Línea divisoria debajo del botón de ajustes
                    
                    # Cálculo previo de velocidad angular 
                    gzx = df['Gaze direction left X'].fillna(0).values
                    gzy = df['Gaze direction left Y'].fillna(0).values
                    gzz = df['Gaze direction left Z'].fillna(0).values
                    t_seg = df['Recording timestamp'].values / 1000000.0
                    velocidades = np.zeros(len(df))
                    
                    for k in range(1, len(df)):
                        if gzx[k] == 0 or gzx[k-1] == 0: continue
                        dt = t_seg[k] - t_seg[k-1]
                        if dt <= 0: continue
                        v1, v2 = np.array([gzx[k-1], gzy[k-1], gzz[k-1]]), np.array([gzx[k], gzy[k], gzz[k]])
                        prod_esc = np.dot(v1, v2)
                        mod1, mod2 = np.linalg.norm(v1), np.linalg.norm(v2)
                        cos_theta = np.clip(prod_esc / (mod1 * mod2), -1.0, 1.0)
                        velocidades[k] = np.degrees(np.arccos(cos_theta)) / dt
                    df['Velocidad Angular'] = velocidades

                    # Algoritmo de detección de parpadeos
                    if 'Recording timestamp' in df.columns and 'Eye movement type' in df.columns:
                        tiempos = df['Recording timestamp'].tolist()
                        tipos_movimiento = df['Eye movement type'].tolist()
                        resultados = []
                        num_evento, i = 1, 0
                        etiquetas_blink = ['EyesNotFound', 'Unclassified']
                        
                        while i < len(tipos_movimiento):
                            if tipos_movimiento[i] in etiquetas_blink:
                                inicio_idx = i
                                tiene_eyes_not_found = False
                                sac_pre = (inicio_idx > 0 and tipos_movimiento[inicio_idx - 1] == 'Saccade')
                                
                                while i < len(tipos_movimiento) and tipos_movimiento[i] in etiquetas_blink:
                                    if tipos_movimiento[i] == 'EyesNotFound': tiene_eyes_not_found = True
                                    i += 1
                                    
                                fin_idx = i - 1
                                long_blink = fin_idx - inicio_idx + 1
                                long_sac_post, vel_pico, j = 0, 0.0, i
                                indices_sacada = []
                                
                                while j < len(tipos_movimiento) and tipos_movimiento[j] == 'Saccade':
                                    long_sac_post += 1
                                    indices_sacada.append(j)
                                    j += 1
                                    
                                if indices_sacada:
                                    vel_pico = df['Velocidad Angular'].iloc[indices_sacada].max()
                                    
                                sac_post_valida = (st.session_state.min_sac_post <= long_sac_post <= st.session_state.max_sac_post)
                                vel_post_valida = (st.session_state.min_vel_post <= vel_pico <= st.session_state.max_vel_post) if st.session_state.req_vel_post else True
                                cond_parp = st.session_state.min_f <= long_blink <= st.session_state.max_f
                                cond_pre = sac_pre if st.session_state.req_sac_pre else True
                                cond_post = (long_sac_post > 0 and sac_post_valida and vel_post_valida) if st.session_state.req_sac_post else True

                                if cond_parp and tiene_eyes_not_found and cond_pre and cond_post:
                                    t_ini, t_fin = tiempos[inicio_idx] / 1000000.0, tiempos[fin_idx] / 1000000.0
                                    resultados.append({
                                        'Parpadeo': num_evento, 'Inicio (s)': round(t_ini, 4), 'Fin (s)': round(t_fin, 4),
                                        'Duración (s)': round(t_fin - t_ini, 4), 'Filas Parpadeo': long_blink,
                                        'Sacada Previa': "Sí" if sac_pre else "No", 'Filas Sacada Posterior': long_sac_post,
                                        'Velocidad Pico (º/s)': round(vel_pico, 2)
                                    })
                                    num_evento += 1
                            else: i += 1

                        # FIGURAS  
                        df_resultados = pd.DataFrame(resultados)
                        if not df_resultados.empty:
                            # Mensaje de número de parpadeos detectados y tabla de parpadeos
                            st.success(f"Se han detectado {len(df_resultados)} parpadeos.")
                            df_resultados.index = df_resultados.index + 1
                            st.dataframe(df_resultados, use_container_width=True)
                            st.divider()

                            # Gráfico de parpadeos a lo largo del tiempo
                            st.subheader("Parpadeos a lo largo del tiempo")
                            df_resultados['Duración (ms)'] = df_resultados['Filas Parpadeo'] * 10
                            fig_tiempo = go.Figure(go.Bar(
                                x=df_resultados['Inicio (s)'], y=df_resultados['Duración (ms)'], width=0.45, marker_color="#0D0840",
                                hovertemplate='<b>Parpadeo #%{customdata}</b><br>Tiempo: %{x:.3f} s<br>Duración: %{y} ms<extra></extra>',
                                customdata=df_resultados['Parpadeo'], name='Parpadeo'
                            ))
                            fig_tiempo.update_layout(xaxis_title="Tiempo (s)", yaxis_title="Duración (ms)", hovermode="closest", bargap=0, yaxis=dict(rangemode='tozero'))
                            st.plotly_chart(fig_tiempo, use_container_width=True)
                            st.divider()

                            # Métricas adicionales
                            col_m1, col_m2 = st.columns(2)
                            duracion_total_seg = (tiempos[-1] - tiempos[0]) / 1000000.0
                            frecuencia_min = (len(df_resultados) / duracion_total_seg) * 60
                            duracion_media_ms = round(df_resultados['Duración (s)'].mean() * 1000)
                            col_m1.metric("Frecuencia media de parpadeo", f"{frecuencia_min:.0f} parpadeos/min")
                            col_m2.metric("Duración media del parpadeo (cerrado)", f"{duracion_media_ms} ms")
                            st.divider()

                            # Evolución de la Frecuencia de Parpadeo
                            st.subheader("Evolución de la Frecuencia de Parpadeo")

                            if not df_resultados.empty:
                                tiempo_max_tobii = int(df_resultados["Inicio (s)"].max()) + 10 
                                eje_x_tobii = np.arange(0, tiempo_max_tobii, 1)
                                eje_y_tobii = []
                                for t in eje_x_tobii:
                                    parpadeos_ventana = ((df_resultados["Inicio (s)"] > t - 60) & (df_resultados["Inicio (s)"] <= t)).sum()
                                    eje_y_tobii.append(parpadeos_ventana)
                                fig_tendencia_tobii = go.Figure()
                                fig_tendencia_tobii.add_trace(go.Scatter(
                                    x=eje_x_tobii, 
                                    y=eje_y_tobii, 
                                    mode='lines', 
                                    name='Parpadeos / min',
                                    line=dict(color="#0D0840", width=2), # Color lila/morado para diferenciarlo de Gazepoint
                                    fill='tozeroy',
                                    fillcolor="#344082"
                                ))
                                fig_tendencia_tobii.update_layout(
                                    xaxis_title="Tiempo (s)", 
                                    yaxis_title="Parpadeos/min",
                                    hovermode="x unified",
                                    yaxis=dict(rangemode="tozero")
                                )
                                st.plotly_chart(fig_tendencia_tobii, use_container_width=True)
                            else:
                                st.warning("No se detectaron parpadeos para calcular la evolución de la frecuencia.")                     
                            st.divider()

                            # Distribución de parpadeos por duración
                            st.subheader("Distribución de parpadeos por duración")
                            df_resultados['ms'] = df_resultados['Filas Parpadeo'] * 10
                            df_counts = df_resultados.groupby('ms').size().reset_index(name='Cantidad').sort_values('ms')
                            fig_dist = px.bar(df_counts, x='ms', y='Cantidad', labels={'ms': 'Duración (ms)', 'Cantidad': 'Número de Parpadeos'}, text_auto=True, template="plotly_dark", color_discrete_sequence=["#0D0840"])
                            fig_dist.update_xaxes(type='linear', tickmode='linear', dtick=10)
                            fig_dist.update_layout(bargap=0.2)
                            st.plotly_chart(fig_dist, use_container_width=True)
                        else: st.warning("No se detectaron eventos con los ajustes actuales.")
                    else: st.error("El archivo no tiene las columnas necesarias: 'Recording timestamp' y 'Eye movement type'.")

            # PESTAÑA: PUPILOMETRÍA

            with tab_pupilometria:
                # TOBII PRO GLASSES 3
                if st.session_state.dispositivo == "Tobii":
                    df_p = df_datos.copy()
                    
                    # Cálculo de Validez
                    muestras_totales = len(df_p)
                    validos_izq = (df_p['Validity left'] == 'Valid').sum()
                    validos_der = (df_p['Validity right'] == 'Valid').sum()
                    pct_izq = (validos_izq / muestras_totales) * 100
                    pct_der = (validos_der / muestras_totales) * 100
                    
                    st.subheader("Validez del Experimento")
                    col1, col2 = st.columns(2)
                    col1.metric("Validez Ojo Izquierdo", f"{pct_izq:.2f}%")
                    col2.metric("Validez Ojo Derecho", f"{pct_der:.2f}%")

                    # Limpieza de la señal
                    df_p['pupila_izq_limpia'] = limpiar_señal(df_p['Pupil diameter left'], df_p['Validity left'], df_p['Eye movement type'], margen_ms=50, max_salto=0.25)
                    df_p['pupila_der_limpia'] = limpiar_señal(df_p['Pupil diameter right'], df_p['Validity right'], df_p['Eye movement type'], margen_ms=50, max_salto=0.25)
                    st.success("Señal de pupila limpiada e interpolada.")

                    # Visualización
                    st.subheader("Visualización")
                    ojo_seleccionar = st.radio("Selecciona el ojo a visualizar:", ["Izquierdo", "Derecho", "Ambos"])
                    df_p['Tiempo (s)'] = df_p['Computer timestamp'] / 1e6
                    tiempo = df_p['Tiempo (s)']

                    fig_pup = go.Figure()
                    if ojo_seleccionar in ["Izquierdo", "Ambos"]:
                        fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['Pupil diameter left'], name="Original Izq", line=dict(color='rgba(255, 0, 0, 0.3)')))
                        fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['pupila_izq_limpia'], name="Limpio Izq", line=dict(color='red')))
                    if ojo_seleccionar in ["Derecho", "Ambos"]:
                        fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['Pupil diameter right'], name="Original Der", line=dict(color='rgba(0, 0, 255, 0.3)')))
                        fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['pupila_der_limpia'], name="Limpio Der", line=dict(color='blue')))

                    fig_pup.update_layout(title="Comparativa de señal de pupila: Original vs. Limpia", xaxis_title="Tiempo (s)", yaxis_title="Diámetro de pupila", hovermode="x unified")
                    st.plotly_chart(fig_pup, use_container_width=True)

                    # Selector de segmento
                    t_min, t_max = float(df_p['Tiempo (s)'].min()), float(df_p['Tiempo (s)'].max())
                    rango_sel = st.slider("Selecciona el fragmento a analizar (segundos):", t_min, t_max, (t_min, t_min + 10.0))
                    df_segmento = df_p[(df_p['Tiempo (s)'] >= rango_sel[0]) & (df_p['Tiempo (s)'] <= rango_sel[1])].copy()
                    
                    duracion_base_ms = 200 
                    muestras_base = int((duracion_base_ms / 1000) * 100)
                    val_base_izq = df_segmento['pupila_izq_limpia'].iloc[:muestras_base].median()
                    val_base_der = df_segmento['pupila_der_limpia'].iloc[:muestras_base].median()
                    df_segmento['pupila_izq_corr'] = df_segmento['pupila_izq_limpia'] - val_base_izq
                    df_segmento['pupila_der_corr'] = df_segmento['pupila_der_limpia'] - val_base_der

                    st.plotly_chart(generar_grafica_baseline(df_segmento, val_base_izq, val_base_der), use_container_width=True)
                
                # GAZEPOINT GP3
                elif st.session_state.dispositivo == "Gazepoint":
                    df_p = df_datos.copy()
                    df_p.columns = df_p.columns.str.strip()
                    posibles_time = [c for c in df_p.columns if "TIME" in c.upper()]
                    if not posibles_time:
                        st.error("No se encontró la columna de tiempo.")
                    else:
                        time_col = posibles_time[0]
                        df_p[time_col] = parsear_columna(df_p[time_col])
                        df_p['LPMM'] = parsear_columna(df_p['LPMM'])
                        df_p['RPMM'] = parsear_columna(df_p['RPMM'])
                        df_p['LPMMV'] = pd.to_numeric(df_p['LPMMV'], errors='coerce')
                        df_p['RPMMV'] = pd.to_numeric(df_p['RPMMV'], errors='coerce')

                        # Cálculo de Validez
                        muestras_totales = len(df_p)
                        validos_izq = (df_p['LPMMV'] == 1).sum()
                        validos_der = (df_p['RPMMV'] == 1).sum()
                        pct_izq = (validos_izq / muestras_totales) * 100
                        pct_der = (validos_der / muestras_totales) * 100
                        
                        st.subheader("Validez del Experimento")
                        col1, col2 = st.columns(2)
                        col1.metric("Validez Ojo Izquierdo", f"{pct_izq:.2f}%")
                        col2.metric("Validez Ojo Derecho", f"{pct_der:.2f}%")

                        # Limpieza de la señal
                        # Eliminación los valores repetidos durante los parpadeos
                        df_p.loc[df_p['LPMMV'] == 0, 'LPMM'] = np.nan
                        df_p.loc[df_p['RPMMV'] == 0, 'RPMM'] = np.nan

                        # Adaptación para usar la función original limpiar_señal
                        val_izq_str = df_p['LPMMV'].map({1: 'Valid', 0: 'Invalid', np.nan: 'Invalid'})
                        val_der_str = df_p['RPMMV'].map({1: 'Valid', 0: 'Invalid', np.nan: 'Invalid'})
                        
                        # Como Gazepoint no tiene columna Saccade, se crea una vacía para evitar errores
                        mov_dummy = pd.Series('Unknown', index=df_p.index)
                        
                        df_p['pupila_izq_limpia'] = limpiar_señal(df_p['LPMM'], val_izq_str, mov_dummy, freq_hz=60, margen_ms=50, max_salto=0.3)
                        df_p['pupila_der_limpia'] = limpiar_señal(df_p['RPMM'], val_der_str, mov_dummy, freq_hz=60, margen_ms=50, max_salto=0.3)

                        st.success("Señal de pupila limpiada e interpolada correctamente.")

                        # Visualización
                        st.subheader("Visualización")
                        ojo_seleccionar = st.radio("Selecciona el ojo a visualizar:", ["Izquierdo", "Derecho", "Ambos"], key="ojo_gp")
                        tiempo = df_p[time_col]
                        
                        fig_pup = go.Figure()
                        if ojo_seleccionar in ["Izquierdo", "Ambos"]:
                            fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['LPMM'], name="Original Izq (con huecos)", line=dict(color='rgba(255, 0, 0, 0.3)')))
                            fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['pupila_izq_limpia'], name="Limpio Izq", line=dict(color='red')))
                        if ojo_seleccionar in ["Derecho", "Ambos"]:
                            fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['RPMM'], name="Original Der (con huecos)", line=dict(color='rgba(0, 0, 255, 0.3)')))
                            fig_pup.add_trace(go.Scatter(x=tiempo, y=df_p['pupila_der_limpia'], name="Limpio Der", line=dict(color='blue')))

                        fig_pup.update_layout(title="Comparativa de señal de pupila: Original vs. Limpia", xaxis_title="Tiempo (s)", yaxis_title="Diámetro de pupila (mm)", hovermode="x unified")
                        st.plotly_chart(fig_pup, use_container_width=True)

                        # Baseline interactivo
                        t_min, t_max = float(tiempo.min()), float(tiempo.max())
                        rango_sel = st.slider("Selecciona el fragmento a analizar (segundos):", t_min, t_max, (t_min, min(t_min + 10.0, t_max)), key="slider_gp")
                        
                        df_segmento = df_p[(tiempo >= rango_sel[0]) & (tiempo <= rango_sel[1])].copy()
                        
                        duracion_base_ms = 200 
                        muestras_base = int((duracion_base_ms / 1000) * 60) # Adaptado a 60Hz
                        
                        val_base_izq = df_segmento['pupila_izq_limpia'].iloc[:muestras_base].median()
                        val_base_der = df_segmento['pupila_der_limpia'].iloc[:muestras_base].median()
                        
                        df_segmento['pupila_izq_corr'] = df_segmento['pupila_izq_limpia'] - val_base_izq
                        df_segmento['pupila_der_corr'] = df_segmento['pupila_der_limpia'] - val_base_der
                        df_segmento['Tiempo (s)'] = df_segmento[time_col]

                        st.plotly_chart(generar_grafica_baseline(df_segmento, val_base_izq, val_base_der), use_container_width=True)
        # En caso de error
        except Exception as e:
            st.error(f"Hubo un error al procesar el archivo principal: {e}")