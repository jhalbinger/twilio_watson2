from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)
contextos = {}

@app.route("/")
def index():
    return "✅ Microservicio conectado a Watson Assistant v1 con soporte de audio"

@app.route("/webhook", methods=["POST"])
def webhook():
    mensaje = request.form.get("Body", "").strip()
    numero_completo = request.form.get("From", "")
    numero_limpio = numero_completo.replace("whatsapp:", "")
    tipo_mensaje = request.form.get("NumMedia", "0")

    if not mensaje:
        return "⚠️ No se recibió ningún mensaje de texto."

    respuesta = enviar_a_watson(mensaje, numero_limpio)
    return respuesta

def enviar_a_watson(mensaje, session_id):
    url = "https://api.us-south.assistant.watson.cloud.ibm.com/instances/dbec99ff-fe74-43a5-989c-2ef686aa7c9f/v1/workspaces/bc5f4504-d219-4792-aea5-cfbdb2c0b0f7/message?version=2021-06-14"
    auth = ("apikey", "O7cWhbMQ1oJPx-IpcxNVMXxy8nGa2L7fz873rOG_4bcA")
    contexto_prev = contextos.get(session_id, {})
    contexto_prev["telefono"] = session_id

    payload = {
        "input": {"text": mensaje},
        "context": contexto_prev
    }

    response = requests.post(url, json=payload, auth=auth)

    if response.status_code == 200:
        data = response.json()
        contextos[session_id] = data.get("context", {})
        try:
            return "\n".join(data["output"]["text"])
        except (KeyError, IndexError):
            return "⚠️ Watson no devolvió una respuesta válida."
    else:
        print("❌ Error al contactar a Watson:", response.status_code)
        return "⚠️ Ocurrió un error al contactar al bot."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
