from fastapi import FastAPI, Request, HTTPException
import requests
import json
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_ID")
whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
whatsapp_api_url = f'https://graph.facebook.com/v17.0/{whatsapp_phone_id}/messages'
whatsapp_verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

app = FastAPI()

# Configura CORS si es necesario
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de LangChain
chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

@app.post("/webhook")
async def receive_message(request: Request):
    try:
        body = await request.json()
        
        if body.get("object"):
            if body.get("entry") and body["entry"][0].get("changes") and body["entry"][0]["changes"][0].get("value"):
                
                from_number = body["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
                msg_body = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

                # Normalizar número (si empieza con 549, lo cambia a 54)
                def normalizar_numero(numero: str) -> str:
                    return "541115" + numero[5:] if numero.startswith("549") else numero

                from_number = normalizar_numero(from_number)

                response = await process_message(msg_body)
                await send_whatsapp_message(from_number, response)
                return {"status": "ok"}

        return {"status": "error", "message": "Formato de mensaje no válido"}
    except Exception as e:
        print(f"Error en receive_message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error procesando el mensaje")

async def process_message(message: str):
    try:
        response = chat.predict(message)
        return response
    except Exception as e:
        print(f"Error en process_message: {str(e)}")
        return "Lo siento, hubo un error procesando tu mensaje. Por favor, intenta nuevamente."

async def send_whatsapp_message(to: str, text: str):
    try:
        print(f"Enviando mensaje a WhatsApp...{to}")
        headers = {
            "Authorization": f"Bearer {whatsapp_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "text": {"body": text}
        }
        response = requests.post(whatsapp_api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP: {str(e)}")
        if e.response is not None:
            print(f"Detalles de la respuesta: {e.response.text}")
        raise HTTPException(status_code=500, detail="Error enviando mensaje de WhatsApp")
    except Exception as e:
        print(f"Error general en send_whatsapp_message: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/webhook")
async def verify_webhook(request: Request):
    try:
        print("Verificando webhook...")
        params = request.query_params
        
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == whatsapp_verify_token:
                return int(challenge)
            raise HTTPException(status_code=403, detail="Token de verificación inválido")
        
        raise HTTPException(status_code=400, detail="Parámetros inválidos")
    except Exception as e:
        print(f"Error en verify_webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Permitir todo el tráfico en CSP
    response.headers['Content-Security-Policy'] = "default-src *; img-src *; script-src *; style-src *; font-src *;"
    return response