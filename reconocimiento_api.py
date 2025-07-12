from flask import Flask, request, jsonify
import face_recognition
import os
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Carga inicial del dataset
def cargar_dataset(ruta_dataset='dataset'):
    dataset_encodings = []
    dataset_nombres = []
    
    for persona in os.listdir(ruta_dataset):
        ruta_persona = os.path.join(ruta_dataset, persona)
        if os.path.isdir(ruta_persona):
            for imagen in os.listdir(ruta_persona):
                ruta_imagen = os.path.join(ruta_persona, imagen)
                img = face_recognition.load_image_file(ruta_imagen)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    dataset_encodings.append(encodings[0])
                    dataset_nombres.append(persona)
    
    return dataset_encodings, dataset_nombres

dataset_encodings, dataset_nombres = cargar_dataset()

@app.route("/")
def index():
    return "✅ API Reconocimiento Facial activa."

@app.route("/reconocer", methods=["POST"])
def reconocer():
    data = request.json

    if "image_url" not in data:
        return jsonify({"error": "Falta la URL de la imagen."}), 400

    image_url = data["image_url"]

    # Descargar la imagen desde la URL
    try:
        response = requests.get(image_url)
        image = face_recognition.load_image_file(BytesIO(response.content))
    except Exception as e:
        return jsonify({"error": f"Error descargando o procesando la imagen: {str(e)}"}), 400

    # Procesar la imagen descargada
    encodings_nuevos = face_recognition.face_encodings(image)

    if not encodings_nuevos:
        return jsonify({"resultado": "No se detectaron rostros en la imagen."}), 200

    # Compara el rostro con los rostros conocidos
    resultados = face_recognition.compare_faces(dataset_encodings, encodings_nuevos[0])

    if True in resultados:
        primer_match = resultados.index(True)
        nombre_detectado = dataset_nombres[primer_match]
    else:
        nombre_detectado = "Desconocido"

    return jsonify({"resultado": nombre_detectado}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
