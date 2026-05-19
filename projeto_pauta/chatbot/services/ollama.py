# chatbot/services/ollama.py

import json
import requests
from django.conf import settings


def gerar_embedding(texto):
    payload_novo = {
        "model": settings.CHATBOT_MODELO_EMBEDDING,
        "input": texto,
    }

    resposta = requests.post(
        f"{settings.CHATBOT_OLLAMA_URL}/api/embed",
        json=payload_novo,
        timeout=120,
    )

    if resposta.status_code == 200:
        dados = resposta.json()
        embeddings = dados.get("embeddings", [])

        if not embeddings:
            raise ValueError("Ollama não retornou embedding no endpoint /api/embed.")

        return embeddings[0]

    payload_antigo = {
        "model": settings.CHATBOT_MODELO_EMBEDDING,
        "prompt": texto,
    }

    resposta_antiga = requests.post(
        f"{settings.CHATBOT_OLLAMA_URL}/api/embeddings",
        json=payload_antigo,
        timeout=120,
    )

    if resposta_antiga.status_code == 200:
        dados = resposta_antiga.json()
        embedding = dados.get("embedding")

        if not embedding:
            raise ValueError("Ollama não retornou embedding no endpoint /api/embeddings.")

        return embedding

    raise RuntimeError(
        "Erro ao gerar embedding no Ollama. "
        f"/api/embed: {resposta.status_code} - {resposta.text} | "
        f"/api/embeddings: {resposta_antiga.status_code} - {resposta_antiga.text}"
    )

def stream_resposta(prompt, config):
    resposta = requests.post(
        f"{settings.CHATBOT_OLLAMA_URL}/api/generate",
        json={
            "model": settings.CHATBOT_MODELO_PADRAO,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.1,
                "num_ctx": config["num_ctx"],
                "num_predict": config["num_predict"],
            },
        },
        stream=True,
        timeout=180,
    )
    resposta.raise_for_status()

    for linha in resposta.iter_lines():
        if not linha:
            continue

        dados = json.loads(linha.decode("utf-8"))
        trecho = dados.get("response", "")

        if trecho:
            yield trecho