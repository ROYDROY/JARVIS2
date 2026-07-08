# Refactorización Dinámica del Enrutador de Cerebros de JARVIS

El objetivo es eliminar los bloques `if/else` estáticos y crear un sistema de registro de APIs dinámico y ampliable. JARVIS debe detectar cualquier clave, evaluar su idoneidad para cada tarea, y seleccionar automáticamente el mejor modelo disponible basándose en puntuaciones, sin necesidad de "parchear" el código para cada nueva API.

## Problema Actual
La función `seleccionar_cerebro` tiene la lógica de selección de LLMs anclada en sentencias `if has_gemini: ... elif has_deepseek: ...`. Esto significa que JARVIS no "comprende" qué capacidades tiene cada API; solo sigue instrucciones fijas, lo que dificulta escalar a nuevos modelos sin intervención humana en el código fuente.

## Proposed Changes

### Componente Principal (`jarvis_app.py`)

#### [MODIFY] [jarvis_app.py](file:///c:/JARVIS2/jarvis_app.py)
1.  **Creación del Registro Dinámico (`API_REGISTRY`)**:
    Implementaremos un diccionario central (o clase) que defina las APIs conocidas, sus modelos ideales para cada rol, y una "puntuación" para que JARVIS pueda compararlas matemáticamente.
    ```python
    API_REGISTRY = {
        "GEMINI": {
            "key": "GEMINI_API_KEY",
            "desc": "Visión avanzada, contexto masivo y análisis profundo de datos.",
            "color": "#1A73E8",
            "models": {
                "Ingeniero": "gemini/gemini-2.5-pro",
                "Análisis": "gemini/gemini-2.5-pro",
                "Conversación": "gemini/gemini-2.5-flash"
            },
            "scores": {"Ingeniero": 100, "Análisis": 100, "Conversación": 80}
        },
        "DEEPSEEK": {
            "key": "DEEPSEEK_API_KEY",
            "desc": "Excelencia en código y razonamiento matemático.",
            "color": "#4D94FF",
            "models": {
                "Ingeniero": "deepseek/deepseek-coder",
                "Análisis": "deepseek/deepseek-chat",
                "Conversación": "deepseek/deepseek-chat"
            },
            "scores": {"Ingeniero": 95, "Análisis": 80, "Conversación": 85}
        },
        # OpenAI, Anthropic, Groq...
    }
    ```

2.  **Refactorización de `seleccionar_cerebro()`**:
    -   Se escanearán las variables de entorno para ver qué APIs están activas.
    -   Según la tarea (`es_codigo`, `es_analisis`, `es_autonomo` o modo manual), JARVIS cruzará las APIs activas con la tabla de `scores` y seleccionará matemáticamente la que tenga mayor puntuación para ese rol.
    -   Esto elimina por completo los `if/elif` por cada modelo. Si en el futuro añadimos una nueva API, solo hay que agregar sus datos al diccionario (o archivo de configuración) y el núcleo la procesará automáticamente.

3.  **Detección de APIs "Desconocidas"**:
    -   Cualquier variable de entorno que termine en `_API_KEY` pero no esté en el registro, será clasificada dinámicamente como una API personalizada.
    -   JARVIS inferirá el prefijo del proveedor (ej. `NVIDIA` -> `nvidia_nim/auto`) y la añadirá al gestor, permitiéndote forzarla si quieres.

4.  **Refactorización de la Interfaz (Gestor de APIs)**:
    -   El popup de "Cerebros y APIs" se alimentará directamente de `API_REGISTRY`. Las tarjetas de UI, descripciones y colores se generarán recorriendo el diccionario, haciendo que UI y Backend compartan la misma fuente de verdad.

## Verification Plan
### Manual Verification
1.  Iniciaremos JARVIS.
2.  Comprobaremos en el menú de "Cerebros y APIs" que todas las APIs (tanto las estándar como las añadidas dinámicamente) aparecen correctamente en la UI.
3.  Simularemos prompts de distintos roles (ej: "escribe un script", "analiza esta imagen", "dime un chiste") y verificaremos que JARVIS selecciona el modelo esperado consultando los logs o los "prints" en consola (Gemini Pro para código/análisis, etc.).
4.  Borraremos una clave desde el Gestor de APIs y verificaremos que JARVIS enruta automáticamente al "segundo mejor modelo" sin fallos de lógica.

> [!IMPORTANT]
> **Revisión Requerida**
> Con este sistema, JARVIS será totalmente modular. Si estás de acuerdo con esta arquitectura basada en un registro de puntuaciones (scores), dame luz verde y procederé a reestructurar el núcleo (`jarvis_app.py`) para hacerlo permanente y dinámico.
