# chatbot/services/indice.py

import json
from pathlib import Path

import numpy as np
from django.conf import settings

from .config import EXTENSOES_SUPORTADAS
from .extratores import extrair_texto_documento
from .ollama import gerar_embedding


ARQUIVO_INDICE = "procedimentos.json"


def caminho_indice():
    return Path(settings.CHATBOT_INDICE_DIR) / ARQUIVO_INDICE


def dividir_texto(texto, tamanho=1200, sobreposicao=200):
    texto = " ".join(texto.split())

    if not texto:
        return []

    partes = []
    inicio = 0

    while inicio < len(texto):
        fim = inicio + tamanho
        parte = texto[inicio:fim].strip()

        if parte:
            partes.append(parte)

        if fim >= len(texto):
            break

        inicio = fim - sobreposicao

    return partes


def listar_documentos():
    documentos_dir = Path(settings.CHATBOT_DOCUMENTOS_DIR)
    documentos_dir.mkdir(parents=True, exist_ok=True)

    arquivos = []

    for caminho in documentos_dir.rglob("*"):
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_SUPORTADAS:
            arquivos.append(caminho)

    return arquivos


def salvar_indice(registros):
    indice_dir = Path(settings.CHATBOT_INDICE_DIR)
    indice_dir.mkdir(parents=True, exist_ok=True)

    with caminho_indice().open("w", encoding="utf-8") as arquivo:
        json.dump(registros, arquivo, ensure_ascii=False, indent=2)


def carregar_indice():
    arquivo_indice = caminho_indice()

    if not arquivo_indice.exists():
        return []

    with arquivo_indice.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def indexar_documentos():
    registros = []

    for caminho in listar_documentos():
        texto = extrair_texto_documento(caminho)

        if not texto.strip():
            continue

        partes = dividir_texto(texto)

        for posicao, parte in enumerate(partes, start=1):
            embedding = gerar_embedding(parte)

            registros.append({
                "arquivo": str(caminho.relative_to(settings.CHATBOT_DOCUMENTOS_DIR)),
                "parte": posicao,
                "texto": parte,
                "embedding": embedding,
            })

    salvar_indice(registros)
    return registros


def similaridade_cosseno(vetor_a, vetor_b):
    a = np.array(vetor_a, dtype=np.float32)
    b = np.array(vetor_b, dtype=np.float32)

    divisor = np.linalg.norm(a) * np.linalg.norm(b)

    if divisor == 0:
        return 0

    return float(np.dot(a, b) / divisor)


def buscar_trechos_relevantes(pergunta, top_k=4):
    registros = carregar_indice()

    if not registros:
        return []

    embedding_pergunta = gerar_embedding(pergunta)
    pontuados = []

    for registro in registros:
        score = similaridade_cosseno(
            embedding_pergunta,
            registro["embedding"],
        )
        pontuados.append((score, registro))

    pontuados.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            **registro,
            "score": score,
        }
        for score, registro in pontuados[:top_k]
    ]