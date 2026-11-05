import os
import re
from pathlib import Path
from threading import Lock
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="LUMINA AI")
lock = Lock()
state = {"on": False, "mode": "simulacion"}

class Command(BaseModel):
    action: str

class Chat(BaseModel):
    message: str
    history: list[dict] = []

def status():
    with lock:
        return dict(state)

def execute(action):
    with lock:
        if action == "on": state["on"] = True
        elif action == "off": state["on"] = False
        elif action != "status": raise ValueError("Acción inválida")
        return dict(state)

@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

@app.get("/api/status")
def get_status():
    return status()

@app.post("/api/control")
def control(command: Command):
    if command.action not in ("on", "off", "status"):
        return {"error": "Acción inválida", **status()}
    return execute(command.action)

def offline_reply(text):
    t = text.lower().strip()
    if re.search(r"\b(apaga|apagar|desactiva|desactivar|quita la luz)\b", t):
        execute("off")
        return "Listo, he apagado el foco virtual.", "off"
    if re.search(r"\b(enciende|encender|prende|prender|activa|activar|ilumina)\b", t) or "está oscuro" in t or "esta oscuro" in t:
        execute("on")
        return "Claro, he encendido el foco virtual.", "on"
    if re.search(r"\b(estado|encendido|apagado|cómo está|como esta|luz prendida)\b", t):
        return f"El foco virtual está {'encendido' if status()['on'] else 'apagado'}.", "status"
    return "Soy Lumina. En modo demostración puedes pedirme encender, apagar o consultar el estado del foco. Para conversar libremente configura la API de IA.", None

@app.post("/api/chat")
def chat(body: Chat):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        reply, action = offline_reply(body.message)
        return {"reply": reply, "action": action, "ai_mode": "demo", **status()}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, timeout=20.0)
        tools = [{"type":"function", "function": {"name":"controlar_foco", "description":"Consultar o cambiar el estado del foco virtual cuando el usuario lo solicite claramente.", "parameters":{"type":"object","properties":{"accion":{"type":"string","enum":["on","off","status"]}},"required":["accion"],"additionalProperties":False}}}]
        system = "Eres Lumina, asistente conversacional en español. Controlas un foco VIRTUAL simulado, nunca afirmes que es físico. Si el usuario solicita encender, apagar o consultar el foco, usa controlar_foco. Para peticiones ambiguas pide aclaración. Responde breve y naturalmente. Estado inicial actual: " + ("encendido" if status()["on"] else "apagado")
        messages = [{"role":"system","content":system}]
        for h in body.history[-12:]:
            if h.get("role") in ("user","assistant") and isinstance(h.get("content"), str):
                messages.append({"role":h["role"],"content":h["content"][:1000]})
        messages.append({"role":"user","content":body.message[:2000]})
        result = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=messages, tools=tools, tool_choice="auto")
        msg = result.choices[0].message
        actions=[]
        if msg.tool_calls:
            import json
            messages.append(msg.model_dump(exclude_none=True))
            for call in msg.tool_calls:
                action = json.loads(call.function.arguments).get("accion")
                if call.function.name != "controlar_foco" or action not in ("on", "off", "status"):
                    outcome = "Acción inválida"
                else:
                    actions.append(action)
                    outcome = "El foco virtual está " + ("encendido" if execute(action)["on"] else "apagado")
                messages.append({"role":"tool","tool_call_id":call.id,"content":outcome})
            final = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=messages)
            reply = final.choices[0].message.content or "Operación realizada."
        else:
            reply = msg.content or "¿Puedes repetirlo?"
        return {"reply":reply,"action":actions[-1] if actions else None,"ai_mode":"openai",**status()}
    except Exception as exc:
        return {"reply":"No pude conectar con el servicio de IA. Puedes usar los botones o el modo demostración sin clave.","error":type(exc).__name__,"ai_mode":"error",**status()}
