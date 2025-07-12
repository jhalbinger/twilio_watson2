from flask import Flask, request
import requests

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
        return "⚠️ No se recibió texto para procesar."

    respuesta = enviar_a_watson(mensaje, numero_limpio)
    return respuesta

def enviar_a_watson(mensaje, session_id):
    url = "https://api.us-south.assistant.watson.cloud.ibm.com/v1/workspaces/a17b54a3-ea98-4362-9766-c76e17484475/message?version=2021-06-14"
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
    app.run()
