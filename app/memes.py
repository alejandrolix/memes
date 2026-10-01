import os
import base64
import json
import requests
from bs4 import BeautifulSoup
from BD import BD
from MemeRepositorio import MemeRepositorio
from Excepcion import Excepcion

# Variables de entorno
DB_HOST: str = os.getenv("DB_HOST")
DB_PORT: str = os.getenv("DB_PORT")
DB_NAME: str = os.getenv("DB_NAME")
DB_USER: str = os.getenv("DB_USER")
DB_PASSWORD: str = os.getenv("DB_PASSWORD")
OLLAMA_URL: str = os.getenv("OLLAMA_URL")
GOOGLE_CHAT_WEBHOOK_URL: str = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL")


def obtener_memes() -> list:
    try:
        response = requests.get("https://www.cuantocabron.com/")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al obtener la página: {e.response.text}")
        raise e

    soup = BeautifulSoup(response.text, "html.parser")
    datos_imagenes: list = []

    for i, img in enumerate(soup.select(".story_content img")):
        datos_imagenes.append({
            "url": img.get("src"),
            "nombre": img.get("alt"),
            "puntuacion": 0
        })

    print(f"Se encontraron {len(datos_imagenes)} imágenes en la web.")
    return datos_imagenes


def enviar_a_google_chat(imagenes) -> None:
    cards: list = []

    for i, img in enumerate(imagenes):
        nombre_split: list = img["nombre"].split(" - ")
        nombre_imagen: str

        if len(nombre_split) > 1:
            nombre_imagen = nombre_split[1]
        else:
            nombre_imagen = img["nombre"]

        card: dict = {
            "cardId": f"meme-{i}",
            "card": {
                "header": {
                    "title": "🐸 Nuevo meme"
                },
                "sections": [{
                    "widgets": [
                        {
                            "image": {
                                "imageUrl": img["url"],
                                "altText": nombre_imagen
                            }
                        },
                        {
                            "textParagraph": {
                                "text": f"<b>{nombre_imagen}</b>"
                            }
                        },
                        {
                            "buttonList": {
                                "buttons": [{
                                    "text": "🔗 Ver en CuantoCabrón",
                                    "onClick": {
                                        "openLink": {
                                            "url": img["url"]
                                        }
                                    }
                                }]
                            }
                        }
                    ]
                }]
            }
        }

        cards.append(card)

    payload: dict = {"cardsV2": cards}
    print("Enviando tarjeta(s) a Google Chat...")

    try:
        res: requests.Response = requests.post(GOOGLE_CHAT_WEBHOOK_URL, json=payload)
        res.raise_for_status()
    except requests.RequestException as e:
        raise Excepcion("Error al enviar los memes a google chat: " + e.response.text) from e

    print("Notificación enviada con éxito a Google Chat.")


def main() -> None:
    NUM_MAX_IMAGENES: int = 3

    datos_imagenes: list = obtener_memes()

    try:
        conexion = BD.abrir_conexion(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    except Excepcion as e:
        print(e.mensaje)
        raise

    meme_repositorio: MemeRepositorio = MemeRepositorio(conexion)

    for imagen in datos_imagenes:
        try:
            existe_meme: bool = meme_repositorio.existe_meme(imagen['nombre'], imagen['url'])
        except Excepcion as e:
            print(e.mensaje)
            raise

        if existe_meme:
            continue

        print(f"Nueva imagen detectada: {imagen["url"]}")

        try:
            img_base64: str = obtener_imagen_base64(imagen["url"])
        except Excepcion as e:
            print(e.mensaje)
            raise

        try:
            analisis: dict = obtener_analisis_imagen(img_base64)
        except Excepcion as e:
            print(e.mensaje)
            raise

        analisis_string: str = json.dumps(analisis, ensure_ascii=False)

        try:
            meme_repositorio.guardar_meme(imagen['nombre'], imagen['url'], analisis_string)
        except Excepcion as e:
            print(e.mensaje)
            raise

        imagen["puntuacion"] = analisis["score"]
        print("--")

    imgs_ordenadas: list = sorted(datos_imagenes, key=lambda item: item["puntuacion"], reverse=True)

    if all(imagen["puntuacion"] == 0 for imagen in imgs_ordenadas):
        print("No hay memes con puntuación mayor a 0")
        return

    if len(imgs_ordenadas) < NUM_MAX_IMAGENES:
        print("No hay suficientes imágenes para enviar")
        return
    
    top_3_mejores_imgs: list = imgs_ordenadas[:NUM_MAX_IMAGENES]

    try:
        enviar_a_google_chat(top_3_mejores_imgs)
    except Excepcion as e:
        print(e.mensaje)
        raise

    try:
        BD.cerrar_conexion()
    except Excepcion as e:
        print(e.mensaje)
        raise


def obtener_imagen_base64(url: str) -> str:
    try:
        img_res: requests.Response = requests.get(url)
        img_res.raise_for_status()                    
    except requests.RequestException as e:
        raise Excepcion(f"Error descargando imagen {url}: {e.response.text}") from e

    return base64.b64encode(img_res.content).decode("utf-8")


def obtener_analisis_imagen(base64_img: str) -> str:
    print("Obteniendo análisis de la imagen...")
    prompt: str = """Actúa como un humorista experto en analizar memes e imágenes humorísticas.

                    Tu tarea es analizar la imagen y determinar qué elementos generan humor y cuánto funciona el chiste.

                    Analiza la imagen siguiendo estos pasos:

                    1. CONTEXTO VISUAL
                    - Describe brevemente qué aparece en la imagen.
                    - Identifica personas, objetos, situaciones, expresiones, acciones y elementos relevantes.

                    2. TEXTO
                    - Extrae el texto visible en la imagen.
                    - Explica qué significado tiene dentro del contexto del meme.
                    - Si no hay texto, indícalo.

                    3. ELEMENTOS HUMORÍSTICOS
                    Identifica concretamente qué elementos pueden resultar graciosos:
                    - Situación absurda o inesperada.
                    - Contraste entre imagen y texto.
                    - Ironía.
                    - Sarcasmo.
                    - Incongruencia.
                    - Exageración.
                    - Juego de palabras.
                    - Referencia cultural.
                    - Expresión facial o corporal.
                    - Situación cotidiana con la que alguien puede identificarse.
                    - Giro inesperado.
                    - Humor negro o provocador, si existe.
                    
                    No inventes elementos que no estén presentes en la imagen.

                    4. MECANISMO DEL CHISTE
                    Explica brevemente por qué esos elementos pueden producir humor y cuál es el mecanismo principal del chiste.

                    5. ORIGINALIDAD
                    Evalúa si la idea parece:
                    - muy predecible,
                    - convencional,
                    - original,
                    - o especialmente ingeniosa.

                    6. POTENCIA HUMORÍSTICA
                    Evalúa cuánto potencial tiene la imagen para provocar una reacción de humor.

                    7. PUNTUACIÓN
                    Asigna una puntuación entre 0 y 10:

                    Asigna una puntuación de 0 a 10:
                    0 = nada gracioso
                    5 = moderadamente gracioso
                    10 = extremadamente gracioso

                    IMPORTANTE:
                    - La puntuación debe representar la eficacia humorística de la imagen, no la calidad técnica de la fotografía.
                    - No otorgues una puntuación alta simplemente porque la imagen sea extraña.
                    - No inventes contexto que no puedas observar.
                    - No penalices una imagen simplemente porque el humor dependa de una referencia cultural.
                    - Si el humor depende de una referencia que no puedes identificar con suficiente certeza, indícalo.
                    - Sé crítico: no intentes hacer que todas las imágenes parezcan graciosas.
                    - La puntuación debe ser coherente con tu análisis.
                    - Devuelve únicamente JSON válido.
                    - No escribas explicaciones fuera del JSON.

                    FORMATO EXACTO:

                    {
                    "description": "Descripción breve de la imagen",
                    "text": "Texto visible o null",
                    "humorous_elements": [
                        {
                        "element": "Elemento humorístico",
                        "explanation": "Por qué puede resultar gracioso"
                        }
                    ],
                    "humor_mechanism": "Mecanismo principal del humor",
                    "originality": "muy_baja | baja | media | alta | muy_alta",
                    "humor_strength": "muy_baja | baja | media | alta | muy_alta",
                    "score": 0,
                    "score_explanation": "Explicación breve de la puntuación"
                    }"""

    datos: dict = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [base64_img],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096
        }
    }

    try:
        respuesta: requests.Response = requests.post(f"{OLLAMA_URL}/generate", json=datos)
        respuesta.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al hacer la petición a Ollama: {e.response.text}")
        raise e

    json_respuesta: dict = respuesta.json()
    print("Tokens de entrada:", json_respuesta["prompt_eval_count"])
    print("Tokens devueltos:", json_respuesta["eval_count"])
    print("total tokens: ", json_respuesta["prompt_eval_count"] + json_respuesta["eval_count"])

    respuesta_analisis: dict = json.loads(json_respuesta["response"])
    print("Descripción obtenida de la imagen:", respuesta_analisis)

    return respuesta_analisis


if __name__ == "__main__":
    main()