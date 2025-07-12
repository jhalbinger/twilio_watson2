from flask import Flask, request
import requests

app = Flask(__name__)
contextos = {}

@app.route("/")
def index():
    return "✅ Microservicio conectado a Watson Assistant v1"

@app.route("/webhook", methods=["POST"])
def webhook():
    mensaje = request.form.get("Body", "").strip()
    numero_completo = request.form.get("From", "")
    numero_limpio = numero_completo.replace("whatsapp:", "")

    print(f"📨 WhatsApp ({numero_limpio}) envió: {mensaje}")

    respuesta_watson = enviar_a_watson(mensaje, numero_limpio)

    print(f"🤖 Watson respondió: {respuesta_watson}")

    return f"<Response><Message>{respuesta_watson}</Message></Response>", 200, {'Content-Type': 'text/xml'}

def enviar_a_watson(mensaje, session_id):
    url = "https://api.us-south.assistant.watson.cloud.ibm.com/v1/workspaces/32377d24-84c4-43aa-9c12-4f0a2a21de42/message"
    auth = ("apikey", "O7cWhbMQ1oJPx-IpcxNVMXxy8nGa2L7fz873rOG_4bcA")

    contexto_prev = contextos.get(session_id, {})
    contexto_prev["telefono"] = session_id

    payload = {
        "input": {"text": mensaje},
        "context": contexto_prev
    }

    try:
        response = requests.post(url, json=payload, auth=auth)

        if response.status_code == 200:
            data = response.json()
            contextos[session_id] = data.get("context", {})
            textos = data.get("output", {}).get("text", [])
            if textos:
                return "\n".join(textos)
            else:
                print("⚠️ Watson no devolvió texto")
                return "🤖 Watson no envió ninguna respuesta."
        else:
            print("❌ Error de Watson:", response.status_code, response.text)
            return "⚠️ No pude contactar al bot."

    except Exception as e:
        print("💥 Error inesperado:", str(e))
        return "⚠️ Error interno del servidor."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
