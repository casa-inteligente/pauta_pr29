# chatbot/services/extratores.py

from pathlib import Path

import pytesseract
from PIL import Image
from pypdf import PdfReader


def extrair_texto_txt_md(caminho):
    return caminho.read_text(encoding="utf-8", errors="ignore")


def extrair_texto_pdf(caminho):
    partes = []
    reader = PdfReader(str(caminho))

    for pagina in reader.pages:
        texto = pagina.extract_text() or ""
        if texto.strip():
            partes.append(texto.strip())

    return "\n\n".join(partes)


def extrair_texto_imagem(caminho):
    imagem = Image.open(caminho)
    return pytesseract.image_to_string(imagem, lang="por").strip()


def extrair_texto_documento(caminho):
    caminho = Path(caminho)
    extensao = caminho.suffix.lower()

    if extensao in {".txt", ".md"}:
        return extrair_texto_txt_md(caminho)

    if extensao == ".pdf":
        return extrair_texto_pdf(caminho)

    if extensao in {".jpg", ".jpeg", ".png", ".webp"}:
        return extrair_texto_imagem(caminho)

    return ""