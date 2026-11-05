# LUMINA AI — Prototipo de software

Software web para controlar un foco **simulado** con botones, chat y voz. No controla hardware todavía.

## Requisitos
- Python 3.10 o superior
- Google Chrome o Microsoft Edge (recomendado para reconocimiento de voz)
- Internet para reconocimiento de voz según navegador y para usar OpenAI

## Instalación (Windows / PowerShell)

```powershell
cd lumina_ai
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Si PowerShell bloquea la activación, usa directamente `.venv\Scripts\python.exe -m pip install -r requirements.txt` y `.venv\Scripts\python.exe -m uvicorn main:app --reload`.

Abre http://127.0.0.1:8000 en Chrome o Edge y concede permiso al micrófono.

## Activar IA real (opcional)

Copia `.env.example` como `.env`, añade tu clave en `OPENAI_API_KEY` y reinicia el servidor. No compartas `.env` ni subas la clave a GitHub. La API puede generar costos. Sin clave, la aplicación usa un intérprete de comandos sencillo, **no una IA conversacional real**.

## Prueba para la exposición
1. Abre la página y muestra el estado apagado.
2. Pulsa Encender y Apagar.
3. Di «enciende el foco» y «¿cuál es el estado del foco?» (Chrome/Edge, micrófono permitido).
4. Con API configurada, prueba «está oscuro, ¿me ayudas?» y una conversación libre.
5. Explica que el siguiente paso es sustituir el simulador por peticiones Wi-Fi al ESP32.

## Arquitectura futura
Navegador (voz y chat) → FastAPI (IA y validación) → ESP32 (HTTP por Wi-Fi) → relé → foco. La versión actual conserva el estado en memoria y lo pierde al reiniciar el servidor. Para conocer el estado físico real será necesaria realimentación o un sensor.

## Seguridad
El prototipo no debe exponerse a Internet sin autenticación. Nunca conectar tensión de red a una protoboard; el montaje de 110/220 V requiere supervisión cualificada y protecciones adecuadas.
