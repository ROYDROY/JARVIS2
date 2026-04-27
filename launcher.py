from interpreter import interpreter
system_msg = open("C:\\JARVIS2\\system.md", "r", encoding="utf-8").read()
interpreter.system_message = system_msg
interpreter.llm.model = "ollama/qwen2.5:7b-instruct-q5_K_M"
interpreter.llm.context_window = 8192
interpreter.llm.max_tokens = 2048
interpreter.auto_run = False
interpreter.chat()
