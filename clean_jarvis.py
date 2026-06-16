import re
import os

ps1_path = r"C:\JARVIS2\jarvis.ps1"

with open(ps1_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Eliminar el bloque de inyectar memoria
content = re.sub(
    r"# ----- INYECTAR MEMORIA EN SYSTEM PROMPT -----.*?# ----- INDICE -----",
    "# ----- INDICE -----",
    content,
    flags=re.DOTALL
)

# Eliminar el bloque de inyectar índice
content = re.sub(
    r"\$indicePath = \"\$root\\memoria\\indice\.json\".*?# ----- JARVIS -----",
    "# ----- JARVIS -----",
    content,
    flags=re.DOTALL
)

# Eliminar el bloque de restaurar system.md
content = re.sub(
    r"# ----- RESTAURAR SYSTEM\.MD ORIGINAL -----.*?# ----- LIMPIEZA CATEGORIA A -----",
    "# ----- LIMPIEZA CATEGORIA A -----",
    content,
    flags=re.DOTALL
)

with open(ps1_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("powershell file cleaned successfully")
