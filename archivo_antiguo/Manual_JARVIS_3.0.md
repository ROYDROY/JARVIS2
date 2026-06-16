# Manual y Capacidades de JARVIS (Versión 3.0 Final - Doble Cerebro)

Este documento detalla la arquitectura, módulos y comandos disponibles en la iteración 3.0 de JARVIS, construida para ser un asistente local, privado y autónomo en Windows.

## 🧠 Arquitectura de Doble Cerebro (MoE Local)
JARVIS ya no utiliza un solo modelo estático. Hemos implementado un sistema de **Enrutamiento Dinámico de Expertos (Router MoE)** en su núcleo (`launcher.py` y `proactivo.py`). 

Antes de procesar tu orden, el Router analiza la frase en milisegundos y decide qué "cerebro" encender:
1. **Qwen 2.5 Coder (14 Billones de Parámetros):** El Ingeniero. Se enciende automáticamente si detecta palabras técnicas (script, código, error, powershell, archivo). Es un experto absoluto en generar automatizaciones de Windows y código sin fallos.
2. **Llama 3.1 (8 Billones de Parámetros):** El Analista. Se enciende para conversar, razonar lógicamente y hacer resúmenes basados en los manuales de la memoria RAG.

*Nota técnica: La ventana de contexto de ambos motores está limitada a 4096 tokens por seguridad, para evitar desbordamientos de la VRAM (RAM de Vídeo) al inyectar textos de los manuales.*

## 📚 El Hipocampo (Memoria RAG)
JARVIS cuenta con una base de datos vectorial (`ChromaDB` + `nomic-embed-text`) de conocimiento infinito sin consumo de RAM en reposo. 

**Conocimientos Inyectados Oficialmente:**
1. **Documentación Oficial de PowerShell 7.4** (470 comandos nativos).
2. **Curso Generative AI for Beginners** (Teoría y práctica de IA de Microsoft, en español).
3. **Reglas base (`system.md`) y logs históricos (`memoria.json`)**.

**Cómo Inyectar Nuevo Conocimiento:**
Si quieres que JARVIS aprenda un nuevo libro o manual permanentemente, abre una consola de PowerShell y ejecuta:
```powershell
C:\JARVIS2\venv\Scripts\python.exe C:\JARVIS2\herramientas\Gestor-Memoria.py "C:\Ruta\Al\Archivo.txt"
```

---

## 🛠️ Herramientas y Módulos
JARVIS cuenta con scripts en la carpeta `C:\JARVIS2\herramientas\` que extienden sus capacidades:
- **Proactivo (`proactivo.py`)**: Su sistema nervioso autónomo. Permite rutinas de fondo sin interacción del usuario. Incluye parche de auto-ejecución y Router MoE.
- **Analizador de Pantalla (`Analizar-Pantalla.py`)**: Utiliza `pyautogui` para sacar una foto de la pantalla.
- **Visión (`Vision.py`)**: Utiliza tu cámara web a través de LLaVA.
- **Navegador Web (`Navegar-Web.py`)**: Entorno aislado (`venv_browser`) con Chromium y `browser-use`. *(Requiere pulido futuro para dominar HTML complejos).*

---

## 🔒 Reglas de Seguridad
1. **Petición de Permisos:** Antes de escribir código, modificar archivos o ejecutar comandos de red, JARVIS DEBE explicar en 1 o 2 líneas exactas qué va a hacer.
2. **Red Aislada:** JARVIS opera en entorno local al 100% (usando tu RAM vía Ollama). No extrae información hacia internet.

---

## ⚙️ Uso Básico
Para encender el núcleo interactivo, ejecuta:
```powershell
python C:\JARVIS2\launcher.py
```
**Comandos en consola:**
- `modo auto`: Activa la auto-aprobación (JARVIS ejecutará el código de Qwen sin preguntar).
- `modo manual`: Vuelve a pedir confirmación (y/n) antes de cada ejecución.
- `salir`: Cierra la sesión de forma segura.
