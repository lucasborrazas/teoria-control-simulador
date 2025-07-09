# Simulador de Air Fryer

El siguiente proyecto es una aplicación interactiva construida en el lenguaje de programación Python. Cuenta con una interfaz gráfica basada en CustomTkinter que permite simular el comportamiento térmico de una freidora de aire bajo un controlador PID (Proporcional–Integral–Derivativo). Además, permite agregar perturbaciones en el sistema para visualizar su impacto en la estabilidad térmica.

<p align="center">
  <img src="https://github.com/user-attachments/assets/72b7d909-4dc2-4c2f-a920-d67e5ca8ffec" alt="Vista previa del simulador" width="1200"/>
</p>

---

## 🎯 Características

- Interfaz con campos configurables.
- Visualización gráfica de:
  - Temperatura de la freidora.
  - Setpoint.
  - Salida del controlador.
  - Señal de error y realimentación.
  - Perturbaciones.
  - Lógica de controlador PID con umbrales de error.

---

## 🛠️ Requisitos

Tener instalado:

- Python `>= 3.8`
- pip (gestor de paquetes de Python)

---

## 📦 Instalación

1. **Clonar este repositorio**:
   ```bash
   git clone https://github.com/lucasborrazas/teoria-control-simulador.git 
   ```

2. **Crear un entorno virtual (opcional pero recomendado)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar las dependencias**:
   ```bash
   pip install numpy matplotlib customtkinter pillow
   ```
---

## 🚀 Ejecución

1. Ejecutar el script principal:

   ```bash
   python tdc.py
   ```

2. Se abrirá una ventana como la siguiente:

   <p align="center">
     <img src="https://github.com/user-attachments/assets/4393e381-f009-4f49-9369-ffeadff2fbdb" alt="Captura de pantalla" width="1200"/>
   </p>

---

## 🧪 Ingreso de parámetros

Inicialmente el simulador cuenta se ejcuta con determinados parámetros por default, pero pueden modificarse en los respectivos inputs.

- **Setpoint**: Temperatura deseada de la freidora (entre 80°C y 200°C).
- **Kp, Ki, Kd**: Constantes del controlador PID.
- **Tau (τ)**: Constante térmica del sistema.
- **Umbral de error**: Umbral de tolerancia.
- **Duración**: Tiempo total de simulación en segundos.
- **Perturbaciones**: Formato `tiempo,valor,duracion;...`, donde cada entrada representa una perturbación térmica (ej.: entrada de aire frío por apertura del cajón de la freidora).
