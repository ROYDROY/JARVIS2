# Plan de Expansión: Visión-Acción (Computer Use) para JARVIS 4.0

El objetivo es dotar a JARVIS local de la capacidad de interactuar con la interfaz gráfica de Windows exactamente igual que un humano: **Mirar la pantalla, reconocer elementos visuales y mover el ratón para hacer clic**, sin depender de integraciones profundas de código.

> [!IMPORTANT]
> **User Review Required**
> Necesito tu aprobación para comenzar a escribir el código de estos nuevos "órganos" para tu JARVIS. Lee el plan y confirma si es la dirección que quieres tomar.

## Open Questions
1. ¿Tienes instalado y funcionando el modelo visual en tu Ollama local (ej. `llava` o `qwen2.5-vl`)? Lo necesitaremos para que JARVIS entienda las capturas de pantalla.
2. ¿Tu JARVIS se está ejecutando actualmente como Administrador? Para que el ratón virtual pueda hacer clics en programas con permisos elevados, el script de Python necesitará permisos de Administrador.

## Proposed Changes

Vamos a crear una arquitectura de dos módulos independientes que se comunican con el cerebro central (`jarvis_app.py`).

---

### Módulo Óptico y Motor

#### [NEW] `herramientas/Ojo_Escritorio.py`
Un script independiente cuya función es tomar capturas de la pantalla.
- Implementará una función para capturar el escritorio, comprimir la imagen y pasarla a base64.
- Incluirá un "Grid" o "Anotador Visual" (superpone una cuadrícula en la pantalla) para ayudar al modelo local (Llava) a calcular las coordenadas (X, Y) con precisión sin equivocarse de píxeles.

#### [NEW] `herramientas/Mano_Fisica.py`
Un envoltorio de seguridad sobre la librería `pyautogui` y el propio motor nativo de `Open Interpreter`.
- Funciones seguras para `mover_raton(x, y)`, `hacer_clic()`, `escribir(texto)`.
- Implementará un "Freno de emergencia" (Failsafe) para que, si el robot se vuelve loco y empieza a hacer clics donde no debe, puedas llevar el ratón de verdad a una esquina de la pantalla y el sistema se aborte instantáneamente.

---

### Integración en el Cerebro

#### [MODIFY] `jarvis_app.py`
Actualizaremos el núcleo de JARVIS para integrar estos nuevos sentidos.
- **Modificación del System Prompt:** Añadiremos la directiva: *"Ahora tienes visión y manos físicas. Antes de operar un programa que no tiene API, usa la herramienta `tomar_captura()`, analiza dónde está el botón que quieres pulsar, y usa `mover_raton(x,y)` y `hacer_clic()` para operarlo."*
- **Nueva Acción UI:** Un botón en la interfaz de JARVIS ("Activar Visión de Escritorio") para encender este modo solo cuando lo necesites (para no saturar tu gráfica constantemente).

## Verification Plan

### Manual Verification
1. Pedir a JARVIS: *"Abre la calculadora de Windows y pulsa el número 5 usando solo tu ratón y tu visión"*.
2. JARVIS deberá hacer una captura, razonar que el '5' está en la coordenada (X: 400, Y: 600), mover físicamente el cursor del PC delante de nuestros ojos, y hacer clic.
