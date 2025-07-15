from flask import Flask, request
import requests
import os
from io import BytesIO
from PIL import Image
import face_recognition

app = Flask(__name__)
contextos = {}

# === CONFIGURACIONES ===
DATASET_DIR = os.path.join(os.getcwd(), "dataset")  # Dataset local
WATSON_URL = "https://api.us-south.assistant.watson.cloud.ibm.com/v1/workspaces/32377d24-84c4-43aa-9c12-4f0a2a21de42/message?version=2021-06-14"
WATSON_AUTH = ("apikey", "O7cWhbMQ1oJPx-IpcxNVMXxy8nGa2L7fz873rOG_4bcA")

# === CARGAR DATASET ===
def cargar_dataset():
    encodings = []
    nombres = []
    for persona in os.listdir(DATASET_DIR):
        ruta_persona = os.path.join(DATASET_DIR, persona)
        if os.path.isdir(ruta_persona):
            for archivo in os.listdir(ruta_persona):
                ruta_imagen = os.path.join(ruta_persona, archivo)
                img = face_recognition.load_image_file(ruta_imagen)
                face_encs = face_recognition.face_encodings(img)
                if face_encs:
                    encodings.append(face_encs[0])
                    nombres.append(persona)
    return encodings, nombres

dataset_encodings, dataset_nombres = cargar_dataset()
print(f"✅ Dataset cargado con {len(dataset_encodings)} rostros conocidos.")

@app.route("/")
def index():
    return "✅ Microservicio conectado a WhatsApp + Watson + Reconocimiento facial"

# === WEBHOOK DE WHATSAPP ===
@app.route("/webhook", methods=["POST"])
def webhook():
    numero_completo = request.form.get("From", "")
    numero_limpio = numero_completo.replace("whatsapp:", "")

    # Si es imagen
    media_url = request.form.get("MediaUrl0")
    media_type = request.form.get("MediaContentType0")

    if media_url and media_type and "image" in media_type:
        print(f"📸 Imagen recibida desde {numero_limpio}: {media_url}")
        resultado = procesar_imagen_whatsapp(media_url)
        return responder_whatsapp(resultado)

    # Si es texto normal
    mensaje = request.form.get("Body", "").strip()
    print(f"📨 WhatsApp ({numero_limpio}) envió: {mensaje}")
    respuesta_watson = enviar_a_watson(mensaje, numero_limpio)
    return responder_whatsapp(respuesta_watson)

def responder_whatsapp(texto):
    return f"<Response><Message>{texto}</Message></Response>", 200, {'Content-Type': 'text/xml'}

# === PROCESAR IMAGEN RECIBIDA ===
def procesar_imagen_whatsapp(media_url):
    try:
        # Descargar la imagen de WhatsApp
        response = requests.get(media_url)
        image = face_recognition.load_image_file(BytesIO(response.content))
        encodings_nuevos = face_recognition.face_encodings(image)

        if not encodings_nuevos:
            return "No se detectó ningún rostro en la imagen enviada."

        # Comparar con dataset
        resultados = face_recognition.compare_faces(dataset_encodings, encodings_nuevos[0])
        if True in resultados:
            idx = resultados.index(True)
            return f"✅ Reconocí a {dataset_nombres[idx]}"
        else:
            return "❌ No encontré coincidencias en el dataset."
    except Exception as e:
        return f"⚠️ Error procesando la imagen: {str(e)}"

# === ENVIAR TEXTO A WATSON ===
def enviar_a_watson(mensaje, session_id):
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
