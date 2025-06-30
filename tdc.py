import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import customtkinter as ctk 
import tkinter as tk 
from PIL import Image 

# --- Parámetros por defecto para la UI ---

# 1. Modelo del Sistema 
DEFAULT_TAU_SISTEMA = 175.0 # Constante de tiempo térmica en segundos. 

# 2. Parámetros del Controlador PID
DEFAULT_KP_CONTROLADOR_PID = 2.0    # Ganancia Proporcional (Kp). Determina la magnitud de la respuesta del controlador al error actual.
DEFAULT_KI_CONTROLADOR_PID = 0.001   # Ganancia Integral (Ki). Elimina el error de estado estacionario.
DEFAULT_KD_CONTROLADOR_PID = 5.0    # Ganancia Derivativa (Kd). Reacciona a la velocidad de cambio del error, ayuda a amortiguar oscilaciones y reducir sobreimpulso.

# 3. Parámetros de la Simulación
DEFAULT_DELTA_T = 1.0          # Paso de una unidad de tiempo de la simulación en segundos. Ya no es configurable desde la UI.
DEFAULT_DURACION_SIMULACION = 3600.0 # Duración total de la simulación en segundos (3600 segundos = 60 minutos).
DEFAULT_SETPOINT = 180.0       # Temperatura seleccionada.
DEFAULT_DEADBAND_THRESHOLD = 5.0 # Umbral de error en °C. El controlador solo actuará si el error es mayor que este valor.

# 4. Definición de Perturbaciones (formato: "tiempo,valor,duracion;tiempo,valor,duracion;...")
DEFAULT_PERTURBACIONES_STR = "600,-2.0,40;1800,-1.5,30;2700,-0.8,25" # Los valores negativos simulan caídas de temperatura.

# 5. Parámetro de Temperatura Ambiente
AMBIENT_TEMPERATURE = 20.0 

# --- Función Principal de Simulación ---
def simular_air_fryer(theta_i, kp_c, ki_c, kd_c, 
                      tau_s,                     
                      delta_t, duracion, deadband_threshold, 
                      perturbaciones_data=None):
    """
    Parámetros que recibe:
        theta_i (float): Temperatura deseada (Setpoint) en °C.
        kp_c (float): Ganancia Proporcional del controlador (Kp).
        ki_c (float): Ganancia Integral del controlador (Ki).
        kd_c (float): Ganancia Derivativa del controlador (Kd).
        tau_s (float): Constante de tiempo del sistema (tau de la air fryer).
        delta_t (float): Paso de tiempo de la simulación en segundos.
        duracion (float): Duración total de la simulación en segundos.
        deadband_threshold (float): Umbral de la banda en °C.
        perturbaciones_data: Lista de valores que definen perturbaciones. Ej: [{'tiempo': 600, 'valor': -2.0, 'duracion': 40}]
    Retorno:
        tiempo, theta_o, theta_controlador, f, error, p_total, effective_error_for_plotting (arrays de NumPy)
        Contienen la evolución de todas las variables clave a lo largo del tiempo.
    """
        
    tiempo = np.arange(0, duracion + delta_t, delta_t)
    num_pasos = len(tiempo) 

    theta_o = np.zeros(num_pasos)          
    theta_controlador = np.zeros(num_pasos) 
    f = np.zeros(num_pasos)                
    error = np.zeros(num_pasos)            
    p_total = np.zeros(num_pasos)          
    effective_error_for_plotting = np.zeros(num_pasos) # Nuevo array para almacenar el error efectivo

    theta_o[0] = AMBIENT_TEMPERATURE # Temperatura inicial de la freidora

    integral_error = 0.0 
    ultimo_error = 0.0 # Necesario para el cálculo del término derivativo

    for i in range(1, num_pasos): 
        f[i] = theta_o[i-1] 
        error[i] = theta_i - f[i]

        effective_error = error[i]
        if abs(error[i]) < deadband_threshold: 
            effective_error = 0.0 # Si el error está dentro del umbral, se considera cero para el PID
            # integral_error se mantiene en su último valor si effective_error es 0.0 para evitar acumulación innecesaria 
            
        # Almacenar el effective_error para graficar
        effective_error_for_plotting[i] = effective_error
            
        # La acumulación del error integral se hace solo si hay un error efectivo fuera de la deadband
        if effective_error != 0.0:
            integral_error += effective_error * delta_t 
        
        # El término derivativo también usa el error efectivo
        derivada_error = (effective_error - ultimo_error) / delta_t 
        
        theta_controlador[i] = (kp_c * effective_error + 
                                ki_c * integral_error +
                                kd_c * derivada_error) 
        
        # Se limita la salida del controlador porque la freidora alcanza hasta 200 °C
        if theta_controlador[i] < 0:
            theta_controlador[i] = 0.0 
        if theta_controlador[i] > 200.0: 
            theta_controlador[i] = 200.0 # Límite superior de la potencia de calentamiento

        ultimo_error = effective_error # Actualiza el último error con el error efectivo para la derivada siguiente

        # Perturbaciones
        current_perturbation_value = 0.0
        if perturbaciones_data:
            for p_info in perturbaciones_data:
                tiempo_inicio = p_info['tiempo']
                duracion_p = p_info['duracion']
                valor_p = p_info['valor']
                if tiempo_inicio <= tiempo[i] < (tiempo_inicio + duracion_p):
                    current_perturbation_value += valor_p
        p_total[i] = current_perturbation_value 

        # Cálculo theta o
        # dtheta_o_dt representa el cambio de temperatura por unidad de tiempo
        # El término p_total[i] simula el efecto de las perturbaciones (ej. entrada de aire frío)
        dtheta_o_dt = (1/tau_s) * (theta_controlador[i] - theta_o[i-1]) + p_total[i]
        theta_o[i] = theta_o[i-1] + dtheta_o_dt * delta_t

        # temperatura de la freidora no baja de la temperatura ambiente
        if theta_o[i] < AMBIENT_TEMPERATURE:
            theta_o[i] = AMBIENT_TEMPERATURE

    return tiempo, theta_o, theta_controlador, f, error, p_total, effective_error_for_plotting

# --- Interfaz Gráfica  ---
entry_setpoint = None
entry_kp_c = None
entry_ki_c = None
entry_kd_c = None 
entry_tau_s = None
# Removido entry_delta_t de la inicialización de variables de entrada, ya no es un parámetro de la UI.
entry_duracion = None
entry_perturbaciones = None
entry_deadband_threshold = None 

# Variables para los objetos de gráfico de Matplotlib.
fig, ax1, ax2, canvas = None, None, None, None

# Variable global para almacenar perturbaciones parseadas
parsed_perturbations_for_plotting = []

def run_simulation_and_plot():
    global fig, ax1, ax2, canvas, parsed_perturbations_for_plotting 

    try:
        setpoint = float(entry_setpoint.get())
        kp_c = float(entry_kp_c.get())
        ki_c = float(entry_ki_c.get())
        kd_c = float(entry_kd_c.get()) 
        tau_s = float(entry_tau_s.get())
        duracion = float(entry_duracion.get())
        deadband_threshold = float(entry_deadband_threshold.get()) # Obtiene el valor del umbral desde la UI

        perturbaciones_str = entry_perturbaciones.get().strip()
        perturbaciones_list = []
        if perturbaciones_str:
            perturbaciones_raw = perturbaciones_str.split(';')
            for p_raw in perturbaciones_raw:
                parts = p_raw.split(',')
                if len(parts) == 3: 
                    tiempo_p = float(parts[0].strip())
                    valor_p = float(parts[1].strip())
                    duracion_p = float(parts[2].strip())
                    perturbaciones_list.append({'tiempo': tiempo_p, 'valor': valor_p, 'duracion': duracion_p})
                else:
                    tk.messagebox.showerror("Error de Entrada", 
                                            "Formato de perturbación incorrecto. Usa 'tiempo,valor,duracion;tiempo,valor,duracion'.")
                    return
        
        parsed_perturbations_for_plotting = perturbaciones_list
        
        # 2. Ejecutar la simulación con los parámetros de la UI
        # Recibe el nuevo array effective_error_for_plotting
        tiempo, theta_o, theta_controlador, f, error, p_total, effective_error_for_plotting = simular_air_fryer(
            theta_i=setpoint,
            kp_c=kp_c, 
            ki_c=ki_c, 
            kd_c=kd_c,
            tau_s=tau_s,
            delta_t=DEFAULT_DELTA_T, 
            duracion=duracion,
            deadband_threshold=deadband_threshold, 
            perturbaciones_data=perturbaciones_list 
        )

        # 3. Eliminar gráficos anteriores y dibujar nuevos
        ax1.clear()
        ax2.clear()

        # Primer Gráfico: Temperaturas
        ax1.plot(tiempo, theta_o, label=r'Temperatura Air Fryer ($\Theta_o$)', color='red', linewidth=2)
        ax1.plot(tiempo, [setpoint] * len(tiempo), linestyle='--', label=r'Setpoint ($\Theta_i$)', color='blue', linewidth=2)

        if parsed_perturbations_for_plotting:
            first_span = True 
            for p_info in parsed_perturbations_for_plotting:
                tiempo_inicio = p_info['tiempo']
                duracion_p = p_info['duracion']
                ax1.axvspan(tiempo_inicio, tiempo_inicio + duracion_p, 
                            facecolor='gray', alpha=0.2, 
                            label='Zona de Perturbación' if first_span else "")
                ax2.axvspan(tiempo_inicio, tiempo_inicio + duracion_p, 
                            facecolor='gray', alpha=0.2, 
                            label='Zona de Perturbación' if first_span else "")
                
                first_span = False 
                        
        ax1.set_title('Simulación de Temperatura con Controlador PID y Perturbaciones', fontdict={'fontsize': 14, 'fontweight': 'bold'})
        ax1.set_xlabel('Tiempo (segundos)', fontdict={'fontsize': 12})
        ax1.set_ylabel('Temperatura (°C)', fontdict={'fontsize': 12})
        ax1.legend()
        ax1.grid(True)
        ax1.set_ylim(0, 300) 
        

        # Segundo Gráfico: Salida del Controlador y Error
        ax2.plot(tiempo, theta_controlador, label=r'Salida del Controlador ($\Theta_{controlador}$)', color='green', linewidth=1.5)
        ax2.plot(tiempo, error, label=r'Error ($e = \Theta_i - \Theta_o$)', color='gray', linestyle='--')
        ax2.plot(tiempo, f, label=r'Señal de Realimentación (f)', color='purple', linestyle='-.')
        
        ax2.set_title('Salida del controlador, señal de error y realimentación', fontdict={'fontsize': 14, 'fontweight': 'bold'})
        ax2.set_xlabel('Tiempo (segundos)', fontdict={'fontsize': 12})
        ax2.set_ylabel('Valor', fontdict={'fontsize': 12}) 
        # MODIFICADO: Posición de la leyenda a 'lower right'
        ax2.legend(loc='lower right')
        ax2.grid(True)
        ax2.set_ylim(0, 300) 

        fig.set_facecolor("white") 
        for ax_item in [ax1, ax2]:
            ax_item.set_facecolor("white") 
            ax_item.tick_params(axis='x', colors='black') 
            ax_item.tick_params(axis='y', colors='black') 
            ax_item.xaxis.label.set_color('black') 
            ax_item.yaxis.label.set_color('black') 
            ax_item.title.set_color('black') 
            ax_item.spines['left'].set_color('black') 
            ax_item.spines['bottom'].set_color('black')
            ax_item.spines['right'].set_color('black')
            ax_item.spines['top'].set_color('black')
            
            for text in ax_item.legend().get_texts():
                text.set_color('black')

        fig.tight_layout() 
        canvas.draw() 
        
    except ValueError:
        tk.messagebox.showerror("Error de Entrada", "Ingresar valores numéricos válidos.")
    except Exception as e:
        tk.messagebox.showerror("Error de Simulación", f"Ocurrió un error durante la simulación: {e}")

# --- Configuración de la Ventana Principal ---
if __name__ == "__main__":
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue")

    root = ctk.CTk() 
    root.title("Teoría de Control - Simulador de Air Fryer")
    root.geometry("1200x850") 

    root.bind("<Return>", lambda event: run_simulation_and_plot())

    # --- Header Frame (Encabezado) ---
    header_frame = ctk.CTkFrame(root, corner_radius=0)
    header_frame.pack(side="top", fill="x", pady=(0, 10))

    try:
        logo_image = ctk.CTkImage(Image.open("./logo.png"), size=(164, 60)) 
        logo_label = ctk.CTkLabel(header_frame, image=logo_image, text="")
        logo_label.grid(row=0, column=0, rowspan=2, padx=10, pady=5, sticky="w") 
    except FileNotFoundError:
        ctk.CTkLabel(header_frame, text="[Logo no encontrado]", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, rowspan=2, padx=10, pady=5, sticky="w")
    except Exception as e:
        ctk.CTkLabel(header_frame, text=f"[Error cargando logo: {e}]", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, rowspan=2, padx=10, pady=5, sticky="w")
    
    ctk.CTkLabel(header_frame, text="Teoría de Control - Simulador de Air Fryer", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=2, rowspan=2, padx=20, pady=5, sticky="nsew")

    names_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    names_frame.grid(row=0, column=4, rowspan=2, padx=10, pady=5, sticky="e")
    
    ctk.CTkLabel(names_frame, text="Docente: Mgtr. Omar Civale", font=ctk.CTkFont(size=16)).pack(anchor="e") 
    ctk.CTkLabel(names_frame, text="Alumno: Lucas Borrazás", font=ctk.CTkFont(size=16)).pack(anchor="e") 

    header_frame.grid_columnconfigure(0, weight=0) 
    header_frame.grid_columnconfigure(1, weight=1) 
    header_frame.grid_columnconfigure(2, weight=0) 
    header_frame.grid_columnconfigure(3, weight=1) 
    header_frame.grid_columnconfigure(4, weight=0) 
    header_frame.grid_rowconfigure((0, 1), weight=1)

    # --- Frame para los Controles de Parámetros ---
    control_frame = ctk.CTkFrame(root) 
    control_frame.pack(padx=10, pady=10, fill="x", expand=False) 

    labels_and_defaults = {
        f"Setpoint ({chr(0x0398)}{chr(0x1D62)}) [80 a 200°C]:": (tk.DoubleVar(value=DEFAULT_SETPOINT), "entry_setpoint"), 
        r"Kp (Ganancia Proporcional):": (tk.DoubleVar(value=DEFAULT_KP_CONTROLADOR_PID), "entry_kp_c"),
        r"Ki (Ganancia Integral):": (tk.DoubleVar(value=DEFAULT_KI_CONTROLADOR_PID), "entry_ki_c"),
        r"Kd (Ganancia Derivativa):": (tk.DoubleVar(value=DEFAULT_KD_CONTROLADOR_PID), "entry_kd_c"), 
        f"Tau ({chr(0x03C4)}) [segundos]:": (tk.DoubleVar(value=DEFAULT_TAU_SISTEMA), "entry_tau_s"), 
        f"Umbral de error [{chr(0x00B1)}°C]:": (tk.DoubleVar(value=DEFAULT_DEADBAND_THRESHOLD), "entry_deadband_threshold"), 
        r"Duración Simulación [segundos]:": (tk.DoubleVar(value=DEFAULT_DURACION_SIMULACION), "entry_duracion"),
        r"Perturbaciones (tiempo,valor,duración;...):": (tk.StringVar(value=DEFAULT_PERTURBACIONES_STR), "entry_perturbaciones")
    }

    col_count = 0
    row_num = 0
    num_params = len(labels_and_defaults)
    params_per_col = (num_params + 1) // 2 
    font_size = ctk.CTkFont(size=20) 

    for i, (label_text, (tk_var, var_name)) in enumerate(labels_and_defaults.items()):
        col = 0 if i < params_per_col else 2 
        current_row = i if i < params_per_col else i - params_per_col

        ctk.CTkLabel(control_frame, text=label_text, font=font_size).grid(row=current_row, column=col, padx=5, pady=2, sticky="w") 
        entry = ctk.CTkEntry(control_frame, textvariable=tk_var, width=250, font=font_size)
        entry.grid(row=current_row, column=col+1, padx=5, pady=1, sticky="ew") 
        globals()[var_name] = entry

        entry.bind("<Return>", lambda event: run_simulation_and_plot())


    control_frame.grid_columnconfigure((0, 2), weight=0) 
    control_frame.grid_columnconfigure((1, 3), weight=1) 

    # --- Frame para el Botón (Centrado) ---
    button_frame = ctk.CTkFrame(root, fg_color="transparent") 
    button_frame.pack(pady=10, fill="x", expand=False) 

    sim_button = ctk.CTkButton(button_frame, text="Simular sistema", command=run_simulation_and_plot, font=font_size, fg_color="#A7C7E7", text_color="black") 
    sim_button.pack(pady=5, anchor="center") 


    # --- Configuración de los Gráficos de Matplotlib ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7)) 
    
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True, padx=10, pady=10) 

    root.mainloop()
