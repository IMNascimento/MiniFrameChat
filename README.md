# MiniFrameChat

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Introdução

**MiniFrameChat** é um mini framework que integra o **Rasa** rodando em **Docker** (Python 3.10) com um **backend FastAPI**.  
Ele permite criar, treinar e executar chatbots de forma simples e organizada, já com template em português incluso.

## Funcionalidades

- Integração entre Rasa (NLU/Dialog) e FastAPI.
- Treinamento de bots via API.
- Execução do Rasa dentro de containers Docker.
- Criação de múltiplos projetos isolados (multi-bots).
- UI simples embutida (`/`) e documentação automática da API (`/docs`).

## Pré-requisitos

Antes de começar, certifique-se de ter as seguintes ferramentas instaladas:

- **Docker** (verifique com `docker --version`)
- **Python 3.10+** (apenas para rodar o backend FastAPI)

## Instalação

Siga as etapas abaixo para configurar o projeto em sua máquina local:

1. Clone o repositório:
    ```bash
    git clone https://github.com/IMNascimento/miniframechat.git
    ```
2. Navegue até o diretório `backend`:
    ```bash
    cd miniframechat/backend
    ```
3. Crie e ative o ambiente virtual:
    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Linux/MacOS
    .venv\Scripts\activate      # Windows
    ```
4. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## Uso

Após instalar as dependências, rode o backend FastAPI:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8899 --reload --env-file ./.env
```

- Acesse a UI simples: [http://127.0.0.1:8899/](http://127.0.0.1:8899/)  
- Acesse a documentação da API: [http://127.0.0.1:8899/docs](http://127.0.0.1:8899/docs)

### Template incluso (PT-BR)

Já incluso no repositório o projeto:  
`workspace/pt-basic-bot`

Para criar outro projeto com o template via API:

```bash
curl -X POST http://127.0.0.1:8899/api/projects \
     -H "Content-Type: application/json" \
     -d '{"name":"meu-bot","template":"pt-basic"}'
```

### Como funciona por trás

- **Treinar**:
  ```bash
  docker run --rm -v <workspace/projeto>:/app -w /app rasa/rasa:3.6.20-full rasa train
  ```
- **Rodar**:
  ```bash
  docker run -d --name rasa-<proj> -p <porta>:5005 \
    -v <workspace/projeto>:/app -w /app rasa/rasa:3.6.20-full \
    rasa run --enable-api --cors * --port 5005 --model models
  ```
- **Parar**:
  ```bash
  docker stop rasa-<proj> && docker rm rasa-<proj>
  ```

⚙️ Configure o arquivo `backend/.env` para trocar a imagem (`RASA_IMAGE`)  
ou desativar Docker (`USE_DOCKER=0`) se quiser rodar o Rasa local.

## Contribuindo

Contribuições são bem-vindas!  
Por favor, siga as diretrizes em `CONTRIBUTING.md` para enviar um Pull Request.

## Licença

Distribuído sob a licença MIT.  
Veja o arquivo [LICENSE](LICENSE) para mais informações.

## Autores

- **IMNascimento** - Desenvolvedor Principal - [GitHub](https://github.com/IMNascimento)

## Agradecimentos

- [Rasa](https://rasa.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)