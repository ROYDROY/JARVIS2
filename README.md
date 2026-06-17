# JARVIS2 - Arquitectura y Documentación Maestra

> [!IMPORTANT]
> **PARA CUALQUIER IA (Claude, GPT, Gemini, Copilot, etc.) LEYENDO ESTO:**
> Este es el documento maestro del sistema JARVIS2. Si has sido invocado para modificar, reparar o expandir a JARVIS2, **LEE ESTE DOCUMENTO CON ATENCIÓN ANTES DE ACTUAR**. No intentes reinventar la rueda; respeta esta arquitectura.

## 1. ¿Qué es JARVIS2?
JARVIS2 es un asistente de IA local, 100% privado y autónomo, diseñado para ejecutarse en Windows. Tiene control total sobre el sistema operativo, gestión de archivos, y ejecución de código en tiempo real. 
Está construido bajo la premisa de "No sobreingeniería": no utiliza orquestadores caóticos ni interfaces pesadas. Es rápido, auditable y modular.

### El Núcleo Tecnológico (Stack)
* **Motores LLM (Arquitectura MoE Híbrida):** 
  - *Local:* Ollama ejecutando modelos cuantizados (`qwen2.5-coder:14b` para código, `llama3.1:8b` para charla rápida) usando la RTX 3080.
  - *Nube (Cirujano Especialista):* Gemini 3.5 Flash a través de API oficial de Google para tareas complejas, análisis de textos largos y procesamiento visual ultra-rápido (reemplazando a v1.5 Pro para optimizar costes y cuotas).
* **Orquestador (El "Cuerpo"):** Open Interpreter (en entorno virtual Python). Traduce las decisiones de la IA en código Python/PowerShell y lo ejecuta localmente.
* **Interfaz:** Interfaz Gráfica Unificada (GUI) desarrollada en `customtkinter` con soporte para reconocimiento de voz continuo y síntesis de voz nativa (`jarvis_app.py`).

---

## 2. Arquitectura de Archivos (El Mapa del Tesoro)

El proyecto vive en `C:\JARVIS2\`. Sus componentes clave son:

* `jarvis_app.py`: El punto de entrada principal. Una GUI unificada que gestiona el enrutamiento de la IA (MoE), el sistema de voz, la memoria vectorial (RAG con ChromaDB) y la ejecución de código (parche JSON para Open Interpreter).
* `config.yaml`: El panel de mandos para configuraciones base. Guarda también de forma automática la persistencia de estado de las expansiones de DLCs (Memoria Vectorial, Clicky/Visión y YouTube) modificados desde el panel lateral de la GUI.
* `.env`: Cortafuegos de credenciales. Almacena las APIs externas. **NUNCA** incrustar estas claves en el código fuente ni subirlas a repositorios. *(Nota: Ahora puede gestionarse cómodamente y de forma dinámica desde la sección "Cerebros y APIs" de la propia interfaz gráfica).*
  * *Nota para el Admin:* Si el `.env` se pierde en un formateo, puedes volver a llenarlo usando la interfaz.
  * *¿De dónde saco la API de Gemini?* Se genera gratis en [Google AI Studio](https://aistudio.google.com/app/apikey). Es el "motor" del Cirujano Especialista.
* `system.md`: **El Cerebro y las Reglas.** Contiene el System Prompt maestro. Dicta la personalidad, restricciones anti-alucinaciones y el uso del buscador autónomo.
* `\memoria\`:
  * `memoria.json`: El historial de "Hechos, Decisiones y Temas". Se inyecta como contexto al inicio de cada sesión para que JARVIS "recuerde" quién es el usuario y qué hizo antes.
  * `indice.json`: El mapa de la "Capa Caliente". Sabe qué discos, carpetas y aplicaciones existen para que el LLM no ande a ciegas.
* `\modulos\`: Archivos `.psm1` cargados al arranque mediante la arquitectura modular definida en `config.yaml`.
* `\herramientas\`: Scripts vitales, inmutables y ultra-optimizados (ver sección de Skills).
* `\sandbox\`: Entorno seguro donde el LLM genera archivos de trabajo.

---

## 3. Sistema de Memoria y Contexto

JARVIS2 utiliza un sistema híbrido de persistencia de contexto:
1. **Memoria de Sesión (RAM a corto plazo):** Al arrancar, [jarvis_app.py](file:///C:/JARVIS2/jarvis_app.py) carga la conversación previa directamente desde [ram_history.json](file:///C:/JARVIS2/ram_history.json). Al finalizar una consulta, el historial completo se vuelve a volcar en este archivo para evitar que la IA pierda el hilo al reiniciar la aplicación.
2. **Memoria Vectorial (Largo plazo - RAG):** Si está activo el interruptor del panel lateral, la conversación se inyecta en una base de datos vectorial local (ChromaDB en `vector_db`) usando incrustaciones locales de `nomic-embed-text`. Para consultas con suficiente contexto, se realiza una búsqueda de similitud y se recuperan recuerdos pasados útiles de forma dinámica, blindando al modelo contra alucinaciones del pasado.

> [!WARNING]
> Si en algún momento la memoria falla o alucina con datos personales del usuario, **EDITA `C:\JARVIS2\memoria\memoria.json` MANUALMENTE**. No intentes arreglarlo con código.

---

## 4. Modo OS y Sistema de Seguridad (Failsafe)

Cuando Jarvis utiliza el cerebro de Gemini 1.5 Pro, tiene habilitado el **OS Mode** (`interpreter.os = True`), lo que le otorga visión de pantalla y control físico sobre el ratón y teclado. Para evitar problemas de seguridad, JARVIS2 implementa el **Protocolo de Cero Sorpresas**:

1. **Consentimiento Previo (Doble Vía):** Antes de ejecutar ninguna tarea administrativa, Jarvis resumirá en 10 palabras su plan y detendrá la ejecución. Mostrará un **Pop-up** y esperará a que el usuario haga clic en `Autorizar` o diga la palabra clave (`Sí`, `Ok`, `Adelante`) por el micrófono.
2. **Botón del Pánico (ESC):** Durante la ejecución autónoma, si el usuario pulsa la tecla `ESC`, Jarvis lanzará el ratón a la esquina de la pantalla (coordenadas 0,0) activando un `FailSafeException` y abortando la ejecución de la IA instantáneamente.
3. **Anuncio de Arranque:** Si existe un archivo `rutinas.json` en `C:\JARVIS2\config\`, Jarvis anunciará por voz las tareas programadas al arrancar el programa.
4. **Modo Administrador (UAC):** Un interruptor en la interfaz gráfica (`🔓 Modo Admin`) permite elevar privilegios. Si Jarvis se encuentra con un error de `Acceso denegado`, solicitará por voz y chat que se active este botón. Una vez activo, Jarvis relanzará automáticamente el comando desencadenando el popup nativo UAC de Windows, garantizando que el usuario SIEMPRE tiene la última palabra antes de tocar el sistema a bajo nivel.

---

## 5. Herramientas de Interfaz (UI)

La GUI de JARVIS (`jarvis_app.py`) no es solo una terminal, cuenta con herramientas de ofimática integradas:
1. **Exportación de Conversaciones:** Botón `📄 Exportar Chat` que permite guardar el registro en Markdown (`.md`), Texto Plano (`.txt`), o mandarlo directo a la impresora nativa de Windows.
2. **Archivos Adjuntos (Visión y Parseo):** Puedes hacer *Drag & Drop* (arrastrar) de imágenes o archivos directamente sobre la interfaz (gracias a `windnd`), o usar el botón `📎`. JARVIS parseará la ruta automáticamente, y el motor LLM la procesará (ej: Gemini 3.5 leerá y analizará la imagen inyectada).
3. **Consciencia Temporal:** En cada interacción se inyecta silenciosamente `datetime.now()` en el prompt del sistema, por lo que la IA siempre sabe el día, fecha y hora exacta sin tener que hacer llamadas a PowerShell.
4. **Ocultación de Pensamientos (Chat Limpio):** El interruptor `Mostrar Pensamiento` del panel lateral permite ocultar la maraña de código de scripts intermedios y de razonamiento lógico técnico que genera el motor ReAct de Jarvis. Si está apagado, el chat mostrará una conversación totalmente limpia y fluida (sólo diálogos y alertas del sistema).

---

## 6. El Sistema de "Skills" (Herramientas)

Para evitar que Open Interpreter pierda tiempo, consuma demasiados tokens o cometa errores escribiendo código desde cero para tareas repetitivas, JARVIS2 utiliza scripts prefabricados ("Skills") en la carpeta `C:\JARVIS2\herramientas\`.

**Regla de Oro para IAs:** Nunca dejes que Open Interpreter genere un script de Python o PowerShell de la nada para una tarea compleja si ya existe una herramienta. 
Las herramientas principales son:
1. `Buscador.py`: Agente de búsqueda autónomo basado en DuckDuckGo. Implementa un filtro estricto anti-Wikipedia. Si la IA requiere información de actualidad o exterior, DEBE ejecutar este script.
2. `Buscar-Archivo.ps1`: Capa de búsqueda de archivos locales. Nunca uses `Get-ChildItem -Recurse` desde la raíz. Utiliza `es.exe` de Everything CLI y ha sido mejorado para soportar búsquedas de palabras clave independientes (operador lógico AND), permitiendo buscar frases en cualquier orden (ej. 'control compras' encuentra 'Control de compras').
3. `MotorVoz.py` / `NervioOptico.py`: Módulos periféricos de escucha pasiva, síntesis de voz y procesamiento de visión artificial.
4. `Escanear-Documento.ps1`: Capa de escaneo de documentos multipágina interactivo. Digitaliza la primera página de forma desatendida y directa. Cuenta con forzado de Flatbed (cama plana, propiedad `3088` y `3012`) tanto en el hardware como en cada ítem secundario de WIA, evitando la excepción `0x80210015` de alimentador vacío en escáneres Epson. Pregunta de forma interactiva si se desean escanear más páginas, compila el PDF resultante (utilizando Pillow) y lo abre en Acrobat Pro.

**Para añadir una nueva Skill:**
1. Escribe un script (Python o PowerShell) y guárdalo en `\herramientas\`.
2. **CRÍTICO:** Ve a `system.md` y añade una regla numérica indicándole a Open Interpreter que *siempre* ejecute esa ruta cuando se enfrente al problema en cuestión.

---

## 7. Protocolo de Ejecución y Compilación

* **Auto Run:** En [jarvis_app.py](file:///C:/JARVIS2/jarvis_app.py), la variable `interpreter.auto_run` está configurada como `True` de forma predeterminada cuando se ejecutan comandos aprobados. Está diseñado para velocidad total. Si entra en bucle, el usuario lo frena con la tecla `ESC` o `CTRL+C`.
* **Arranque del Sistema:** Para arrancar JARVIS sin mostrar la consola de comandos de fondo, ejecuta el script `lanzar_silencioso.vbs` o utiliza el acceso directo configurado en el Escritorio.
* **Actualización del Sistema:** Si una IA hace cambios profundos en el código base ([jarvis_app.py](file:///C:/JARVIS2/jarvis_app.py), `jarvis.ps1`, dependencias nuevas), se **DEBE** recompilar el ejecutable.
* **Comando para compilar:** `powershell -ExecutionPolicy Bypass -File C:\JARVIS2\build.ps1 -msg "Mensaje del commit"`
* **Dependencias de Python:** Siempre se operan desde `C:\JARVIS2\venv\Scripts\python.exe -m pip install <paquete>`. Nunca en la instalación global.

---

## 8. Proyección Futura (Hacia Dónde Crece)

Si recibes instrucciones para evolucionar JARVIS2, estas son las vías de crecimiento autorizadas:
1. **Proactividad (Cron Jobs):** Hacer que el orquestador se active en segundo plano, lea datos (Trading, Fénix) y notifique sin esperar prompt.
2. **Migración a SQLite:** Si `memoria.json` supera el tamaño crítico o el tiempo de carga se resiente, migrar el historial a SQLite con consultas estructuradas.
3. **Capa Visual UI (WebView2):** Si el terminal llega a su límite, crear una UI extremadamente ligera leyendo logs en tiempo real; pero el backend (este documento) permanecerá inmutable.

> [!TIP]
> Si estás ayudando a Rubén (el Administrador), recuerda que prima el control, el minimalismo y evitar procesos pesados. No pidas confirmaciones tontas. Usa tu razonamiento.
