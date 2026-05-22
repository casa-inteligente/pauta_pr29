# chatbot/services/rag.py

from .config import REGRA_RESPOSTA


def montar_contexto(trechos):
    if not trechos:
        return ""

    partes = []

    for item in trechos:
        partes.append(
            f"Fonte: {item['arquivo']} - parte {item['parte']}\n"
            f"{item['texto']}"
        )

    return "\n\n---\n\n".join(partes)


def montar_prompt(pergunta, contexto, contexto_adicional=""):
    return f"""
{REGRA_RESPOSTA}

Responda de forma objetiva, clara e em português do Brasil.
Quando útil, organize a resposta em tópicos curtos.
Não cite normas, rotinas ou passos que não estejam no contexto informado.

Contexto dos documentos da unidade:
{contexto}

Contexto adicional informado pelo usuário:
{contexto_adicional or "Não informado."}

Pergunta:
{pergunta}
""".strip()