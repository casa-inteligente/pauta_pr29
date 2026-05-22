# App Chatbot

Este app fornece um chatbot interno para consulta de procedimentos da unidade. Ele usa RAG: os documentos ficam no projeto, são indexados em embeddings e, a cada pergunta, os trechos mais relevantes são enviados ao modelo no Ollama.

## Fluxo

1. Os documentos ficam em `chatbot/documentos/`.
2. O comando `indexar_chatbot` extrai o texto dos arquivos suportados.
3. O texto é dividido em partes menores.
4. Cada parte recebe um embedding pelo Ollama.
5. O índice é salvo em `chatbot/indices/procedimentos.json`.
6. A pergunta do usuário também recebe embedding.
7. O sistema busca os trechos mais parecidos e monta o prompt.
8. O Ollama gera a resposta com base no contexto recuperado.

## Pastas principais

- `chatbot/documentos/`: base de conhecimento.
- `chatbot/indices/`: índices gerados.
- `chatbot/services/indice.py`: indexação e busca por similaridade.
- `chatbot/services/extratores.py`: extração de texto.
- `chatbot/services/rag.py`: montagem do contexto e prompt.
- `chatbot/services/ollama.py`: integração com Ollama.
- `chatbot/templates/parcial/chatbot_popup.html`: interface do popup.

## Formatos suportados

- `.txt`
- `.md`
- `.pdf`
- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

Para novos procedimentos, prefira `.md`.

## Atualizar a base de dados

Adicione ou edite arquivos em:

```text
chatbot/documentos/procedimentos/
```

Depois rode :
``` python
python manage.py indexar_chatbot
``` 


Exemplo de arquivo para consulta de informação 

``` text 
# Cumprimento de alvará de soltura

## Quando usar

Use este procedimento quando houver alvará de soltura recebido por meio oficial.

## Passos

1. Conferir a identificação da pessoa privada de liberdade.
2. Verificar pendências internas.
3. Registrar a movimentação no sistema.
4. Comunicar a chefia imediata.
5. Arquivar o documento no prontuário.

## Atenção

Se houver outro mandado ativo, a soltura não deve ser cumprida antes da conferência com a autoridade competente.
``` 