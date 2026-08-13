# Manifesto SHA-256: Guia de Integridade de Ficheiros em Linux

Um **manifesto SHA-256** é um ficheiro de texto simples que funciona como um "cartório digital". Ele regista a assinatura única (hash) de cada ficheiro para que possa verificar, no futuro, se algum conteúdo foi alterado, corrompido ou modificado sem o seu consentimento.

---

## 📜 Estrutura do Manifesto

Quando abre um ficheiro de manifesto (geralmente chamado `manifest.sha256`), a estrutura segue este padrão estrito de duas colunas:

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  relatorio_final.pdf
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2  dados_brutos.csv
7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069  configuracao.txt
```

* **Coluna da Esquerda:** O hash SHA-256 (64 caracteres hexadecimais únicos).
* **Coluna da Direita:** O caminho e o nome do ficheiro correspondente.

---

## 🛠️ Comandos Essenciais (Terminal Linux)

### 1. Criar o Manifesto Inicial
Para gerar o manifesto com todos os ficheiros da pasta atual:
```bash
sha256sum * > manifest.sha256
```

Se precisar de incluir **subpastas** de forma recursiva (ignorando o próprio manifesto):
```bash
find . -type f -not -name "manifest.sha256" -exec sha256sum {} + > manifest.sha256
```

### 2. Adicionar Novos Ficheiros no Futuro
Para acrescentar novos ficheiros à lista sem apagar os registos antigos, use o operador de anexação (`>>`):
```bash
sha256sum novo_documento.docx >> manifest.sha256
```

### 3. Verificar a Integridade
Para validar se os ficheiros continuam exatamente iguais aos registos do manifesto:
```bash
sha256sum -c manifest.sha256
```

#### Respostas do Terminal:
* **`OK`**: O ficheiro está intacto e seguro.
* **`FALHOU` (ou `FAILED`)**: O conteúdo do ficheiro foi modificado ou corrompido.
* **`AVISO`**: O ficheiro listado foi apagado ou movido.

---

## 💡 Regras de Ouro para a Conferência

* **Sensibilidade ao Byte:** Se alterar um único espaço ou ponto num ficheiro, o hash SHA-256 muda completamente (Efeito Avalanche).
* **Segurança do Manifesto:** O ficheiro `manifest.sha256` deve ser protegido. Se um atacante modificar um ficheiro e também atualizar o manifesto, a fraude não será detetada.
* **Nomes dos Ficheiros:** Se renomear um ficheiro, o comando de verificação indicará que ele não foi encontrado. O SHA-256 valida o conteúdo, mas depende do nome correto para localizar o alvo.
