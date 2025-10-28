# Sistema de Pauta Virtual - Presídio Regional de Maravilha

Sistema web desenvolvido em Django para gerenciamento de pautas e administração penitenciária do Presídio Regional de Maravilha.

## 📋 Funcionalidades

### 🏛️ Sistema de Pauta

- [x] Criação e gerenciamento de pautas virtuais
- [x] Controle de acesso e permissões
- [x] Interface responsiva e moderna
- [x] Sistema de alertas e notificações

### 👥 Gestão de Detentos

- [x] Cadastro completo de internos
- [x] Controle de regime prisional (Fechado/Semiaberto)
- [x] Geração de termos e documentos oficiais
- [x] Upload e processamento de PDFs

### 📄 Geração de Documentos

- [x] Termo de Autorização para Trabalho
- [x] Termo de Entrega de Kit Higiene
- [x] Termo de Entrega de Rouparia
- [x] Relatórios personalizados em PDF

### 🔄 Funcionalidades Avançadas

- [x] Toggle switches para seleção de regime
- [x] Upload de arquivos PDF com extração de dados
- [x] Sistema de progressão de pena
- [x] Interface administrativa completa

## 🚀 Roadmap

- [ ] App Android para visualização de pautas
- [ ] Sistema de notificações push
- [ ] Dashboard com métricas e estatísticas
- [ ] API REST para integração externa
- [ ] Sistema de backup automático

## 🛠️ Tecnologias Utilizadas

- **Backend**: Django 5.2.6
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Tailwind CSS
- **PDF Generation**: ReportLab
- **Database**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Icons**: Font Awesome
- **Python**: 3.11+

## 📦 Instalação e Configuração

### Pré-requisitos

```bash
- Python 3.11+
- pip
- virtualenv (recomendado)
```

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd pauta_pr29
```

### 2. Criar ambiente virtual

```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# ou
env\Scripts\activate     # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar banco de dados

```bash
# Aplicar migrações iniciais
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser
```

### 5. Coletar arquivos estáticos

```bash
python manage.py collectstatic
```

### 6. Executar servidor de desenvolvimento

```bash
python manage.py runserver
```

## 🔧 Comandos Úteis

### Gerenciamento de Apps

```bash
# Criar novo app
python manage.py startapp nome_do_app

# Fazer migrações após alterações no modelo
python manage.py makemigrations
python manage.py migrate
```

### Testes

```bash
# Executar todos os testes
python manage.py test

# Testes com coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Gera relatório HTML
```

### Produção

```bash
# Reiniciar serviços (produção)
sudo supervisorctl restart projeto_pauta
sudo systemctl restart apache2
```

## 📁 Estrutura do Projeto

```
projeto_pauta/
├── projeto_pauta/          # Configurações principais
├── pauta/                  # App principal de pautas
├── relação_detentos/       # App de gestão de detentos
│   ├── forms/             # Formulários organizados
│   │   ├── geradores.py   # Forms para documentos
│   │   └── django_toggle_switch.py
│   ├── templates/         # Templates HTML
│   ├── static/           # Arquivos estáticos
│   └── models.py         # Modelos de dados
├── media/                 # Uploads de arquivos
├── static/               # Arquivos estáticos coletados
└── requirements.txt      # Dependências
```

## 🎯 Recursos Destacados

### Toggle Switches Personalizados

Sistema de toggle switches para seleção intuitiva entre regimes prisionais:

- 🟠 **Laranja**: Regime Fechado
- 🟢 **Verde**: Regime Semiaberto

### Geração de PDFs Dinâmicos

- Cabeçalhos e rodapés oficiais
- Layouts responsivos
- Dados dinâmicos dos internos
- Assinaturas digitais

### Upload Inteligente de Arquivos

- Processamento automático de PDFs
- Extração de datas de progressão
- Atualização automática de registros

## 🔐 Segurança e Permissões

- Sistema de autenticação Django
- Controle de acesso baseado em grupos
- Validação de dados em formulários
- Proteção CSRF ativada

## 📊 Monitoramento e Logs

- Logs detalhados de operações
- Sistema de auditoria integrado
- Rastreamento de alterações
- Relatórios de uso

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Para suporte técnico ou dúvidas:

- Crie uma issue no GitHub
- Entre em contato com a equipe de desenvolvimento
- Consulte a documentação oficial do Django

## 🔗 Links Úteis

- [Documentação Django](https://docs.djangoproject.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [ReportLab](https://www.reportlab.com/)
- [Font Awesome](https://fontawesome.com/)

---

**Versão**: 1.0.0  
**Status**: Em desenvolvimento ativo  
**Última atualização**: Outubro 2025
