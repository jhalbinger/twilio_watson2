from flask import Flask, request
import requests
import os

app = Flask(__name__)

# === CONFIGURACIONES DE WATSON ===
WATSON_URL = "https://api.us-south.assistant.watson.cloud.ibm.com/v1/workspaces/32377d24-84c4-43aa-9c12-4f0a2a21de42/message?version=2021-06-14"
WATSON_AUTH = ("apikey", "O7cWhbMQ1oJPx-IpcxNVMXxy8nGa2L7fz873rOG_4bcA")

# Memoria temporal de contextos
contextos = {}

@app.route("/")
def index():
    return "✅ Microservicio conectado a WhatsApp + Watson (solo texto)"

# === WEBHOOK QUE RECIBE WHATSAPP ===
@app.route("/webhook", methods=["POST"])
def webhook():
    numero_completo = request.form.get("From", "")
    numero_limpio = numero_completo.replace("whatsapp:", "")
    mensaje = request.form.get("Body", "").strip()

    print(f"📨 WhatsApp ({numero_limpio}) envió: {mensaje}")

    # Enviar mensaje a Watson y obtener respuesta
    respuesta_watson = enviar_a_watson(mensaje, numero_limpio)

    print(f"🤖 Watson respondió: {respuesta_watson}")

    return responder_whatsapp(respuesta_watson)

# === ENVÍA EL TEXTO A WATSON ASSISTANT ===
def enviar_a_watson(mensaje, session_id):
    # Recuperar contexto anterior
    contexto_prev = contextos.get(session_id, {})
    contexto_prev["telefono"] = session_id

    payload = {
        "input": {"text": mensaje},
        "context": contexto_prev
    }

    try:
        response = requests.post(WATSON_URL, json=payload, auth=WATSON_AUTH)

        if response.status_code == 200:
            data = response.json()
            contextos[session_id] = data.get("context", {})
            textos = data.get("output", {}).get("text", [])
            return "\n".join(textos) if textos else "🤖 Watson no envió ninguna respuesta."
        else:
            print("❌ Error de Watson:", response.status_code, response.text)
            return "⚠️ No pude contactar al bot."

    except Exception as e:
        print("💥 Error inesperado:", str(e))
        return "⚠️ Error interno del servidor."

# === RESPUESTA PARA TWILIO/WHATSAPP ===
def responder_whatsapp(texto):
    return f"<Response><Message>{texto}</Message></Response>", 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
