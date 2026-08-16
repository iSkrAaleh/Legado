import openai
from django.conf import settings
import math

import os

openai.api_key = os.environ.get("OPENAI_API_KEY", "AQUI_TU_CLAVE_LOCAL_SI_QUIERES")

def generar_embedding(texto):
    """
    Toma un texto string y devuelve una lista de 1536 floats llamando a la API de OpenAI.
    """
    try:
        respuesta = openai.Embedding.create(
            input=texto,
            model="text-embedding-ada-002"
        )
        return respuesta['data'][0]['embedding']
    except Exception as e:
        print(f"Error generando embedding: {e}")
        return None

def cosine_similarity(vec1, vec2):
    """
    Calcula la similitud del coseno entre dos listas de floats.
    Retorna un valor entre -1 y 1 (1 = exactos).
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)
