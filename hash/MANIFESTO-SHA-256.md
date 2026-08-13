# Manifesto SHA-256: Guia de Integridade de Ficheiros em Linux

Um **manifesto SHA-256** é um ficheiro de texto simples que funciona como um "cartório digital". Ele regista a assinatura única (hash) de cada ficheiro para que possa verificar, no futuro, se algum conteúdo foi alterado, corrompido ou modificado sem o seu consentimento.

---

## 📜 Estrutura do Manifesto

Quando abre um ficheiro de manifesto (geralmente chamado `manifest.sha256`), a estrutura segue este padrão estrito de duas colunas:
