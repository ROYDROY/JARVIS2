# Historial de Auditorías de Estabilidad (JARVIS 4.0)
*Fecha: Junio 2026*

Este documento registra los arreglos críticos realizados durante 11 pases de auditoría de código en `jarvis_app.py`. **ESTOS CAMBIOS SON ESTRUCTURALES Y NO DEBEN DESHACERSE BAJO NINGÚN CONCEPTO.**

### 1. Sistema de Hilos y Atomicidad (Threading)
- **Problema original:** El botón de "Hablar ahora" y la escucha pasiva (`wake_word`) chocaban intentando acceder al micrófono (PyAudio) al mismo tiempo, provocando cierres de aplicación y "sordera" de JARVIS.
- **Solución implementada:** Se implementó `self._prompt_lock = threading.Lock()` en `ejecutar_prompt()`. Este candado actúa como árbitro atómico. Es la **única** fuente de verdad que impide ejecuciones simultáneas.
- **Regla:** Ningún método de escucha o UI debe implementar comprobaciones como `if self.is_generating` por su cuenta. Todo el acceso pasa por adquirir `_prompt_lock` (non-blocking).

### 2. Gestión Segura de Interfaz Gráfica (Tkinter Queue)
- **Problema original:** Tareas en segundo plano intentaban modificar textos o ventanas, provocando errores silenciosos o crashes porque Tkinter no es thread-safe.
- **Solución implementada:** Todo se canaliza mediante `self.ui_queue`. Acciones como `("chat", texto)`, `("estado", mensaje)` o `("hablar", frase)` se insertan en la cola y el método central `procesar_cola()` las ejecuta en el hilo principal (`after`).
- **Regla:** JAMÁS tocar widgets de `ctk` desde hilos como `_escucha_worker` o `hilo_wake_word`.

### 3. Truncamiento Seguro del TTS (Texto a Voz)
- **Problema original:** Textos muy largos (especialmente de respuestas técnicas y código) atascaban el motor TTS, provocando cuelgues del sistema Windows.
- **Solución implementada:** En todos los motores de LLM (Fast-Track, ReAct, Nube), la salida hablada por voz pasa por una expresión regular que extrae máximo las **2 primeras frases**, con un **corte forzoso a 500 caracteres** (`" ".join(frases[:2])[:500]`).
- **Regla:** El TTS (`ui_queue.put(("hablar", ...))`) SIEMPRE debe ir protegido por este límite.

### 4. Memoria de Modelos Locales (Amnesia)
- **Problema original:** Los modelos locales (Fast-Track y ReAct) inicializaban su contexto desde cero cada vez, o usaban endpoints de generación simple (`/api/generate`), provocando que JARVIS olvidara lo dicho hace 10 segundos (alucinando sobre perceptrones o coches).
- **Solución implementada:** Se unificó la memoria a nivel global usando `interpreter.messages` de Open Interpreter.
  - Para *Fast-Track*, se migró a `/api/chat` y se inyecta `interpreter.messages[-10:]` en el payload.
  - Para *ReAct*, se inyecta la misma historia global como contexto base de su loop de razonamiento.
- **Regla:** Cualquier motor LLM futuro debe añadir el mensaje del usuario y la respuesta de la IA a `interpreter.messages`.

### 5. Control del Failsafe (PyAutoGUI)
- **Problema original:** Errores no controlados por movimientos de ratón a las esquinas si la aplicación automatizaba acciones.
- **Solución implementada:** Se bloqueó el hilo general con un `try-except` rodeando la importación de hotkeys y se usa `ESC` como botón de pánico de seguridad.

### 6. Control del Wake Word Global
- **Problema original:** El micrófono se bloqueaba porque el hilo se quedaba colgado o escuchando su propia voz.
- **Solución implementada:** Uso de la variable `is_speaking_global` como *guard* booleano, gestionado por `hablar_y_esperar()`. El Wake Word aborta su escucha inmediatamente si JARVIS está hablando físicamente, evitando ecos.

### 7. Elevación de Privilegios Autónoma (UAC)
- **Problema original:** Tareas como crear tareas programadas, instalar drivers o tocar el registro fallaban con "Acceso denegado". Si se lanzaba el programa principal como administrador desde el inicio, se rompía el `drag & drop` de Windows y se introducían riesgos de seguridad excesivos.
- **Solución implementada:** Se integró un botón `🔓 Modo Admin (UAC)`. Si el motor ReAct detecta palabras como "acceso denegado" en el output de un script `powershell`, el sistema pide por voz y chat al usuario que active el botón. Al activarlo (`_admin_granted_event.set()`), la misma instrucción se relanza usando `Start-Process -Verb RunAs` y redirección a `tempfile` en UTF-16LE, disparando el popup de Windows de forma delegada y segura.
- **Regla:** Ningún proceso Python debe elevarse. La elevación ocurre *on-demand* aislando comandos específicos en `ejecutar_codigo_admin`.

### 8. Consciencia Temporal (Inyección DateTime)
- **Problema original:** JARVIS no sabía qué día ni hora era, fallando en tareas que requerían contexto temporal ("saludos de buenos días", "qué hora es", "agenda de hoy").
- **Solución implementada:** Se inyecta `datetime.now()` dinámicamente en el system prompt tanto del motor ReAct como del Fast-Track antes de cada ejecución, dando consciencia exacta del momento actual.

### 9. Exportación de Conversación
- **Problema original:** No había forma de sacar el texto del chat para guardar un log útil o documento.
- **Solución implementada:** Nuevo menú en la UI (`_exportar_a_archivo`, `_imprimir_chat`) que parsea la conversación a texto plano, a Markdown enriquecido y permite mandarlo directo a la impresora nativa de Windows (`notepad /p`).

### 10. Archivos Adjuntos y Drag & Drop
- **Problema original:** Open Interpreter / Gemini soporta visión y parseo de archivos si se les pasa la ruta, pero la UI no dejaba arrastrarlos o buscarlos cómodamente.
- **Solución implementada:** Integración del módulo `windnd` nativo para capturar el *drop* de archivos en la ventana y un botón `📎` (`adjuntar_archivo`) para abrir el `filedialog`. Ambos métodos inyectan la ruta absoluta como `[Archivo: C:\ruta\archivo.ext]` directamente en el `textbox` del prompt.

---
**NOTA PARA FUTUROS DESARROLLOS:**
Si modificas `jarvis_app.py`, debes mantener estas reglas de sincronización. Las variables de estado `is_generating`, el lock y la `ui_queue` son pilares intocables de esta versión.
