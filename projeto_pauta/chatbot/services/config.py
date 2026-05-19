# chatbot/services/config.py

REGRA_RESPOSTA = """
Responda apenas com base nos procedimentos da unidade fornecidos no contexto.
Se a resposta não estiver nos documentos, informe que não encontrou o procedimento cadastrado.
"""

EXTENSOES_SUPORTADAS = {
    ".txt",
    ".md",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}