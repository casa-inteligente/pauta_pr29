from django.shortcuts import render

# Create your views here.
# chatbot/views.py

from django.conf import settings
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services.indice import buscar_trechos_relevantes
from .services.ollama import stream_resposta
from .services.rag import montar_contexto, montar_prompt


def chatbot_popup(request):
    return render(request, "parcial/chatbot_popup.html")


@require_POST
def chatbot_responder(request):
    pergunta = request.POST.get("pergunta", "").strip()
    modo_contexto = request.POST.get("modo_contexto", "equilibrada")
    contexto_adicional = request.POST.get("contexto_adicional", "").strip()

    if not pergunta:
        return StreamingHttpResponse(
            iter(["Informe uma pergunta para consultar os procedimentos."]),
            content_type="text/plain; charset=utf-8",
        )

    configs = settings.CHATBOT_MODOS_CONTEXTO
    config = configs.get(modo_contexto, configs["equilibrada"])

    trechos = buscar_trechos_relevantes(
        pergunta=pergunta,
        top_k=config["top_k"],
    )

    if not trechos:
        return StreamingHttpResponse(
            iter(["Não encontrei esse procedimento nos documentos cadastrados da unidade."]),
            content_type="text/plain; charset=utf-8",
        )

    contexto = montar_contexto(trechos)
    prompt = montar_prompt(
        pergunta=pergunta,
        contexto=contexto,
        contexto_adicional=contexto_adicional,
    )

    return StreamingHttpResponse(
        stream_resposta(prompt, config),
        content_type="text/plain; charset=utf-8",
    )