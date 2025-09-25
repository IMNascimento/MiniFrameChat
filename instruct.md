# Guia Completo: Criando um bot no **Rasa Mini Framework** (PT-Basic)

Este guia ensina **passo a passo** como usar a **interface web** do projeto para criar, treinar e conversar com um bot em português, usando o **template PT-Basic**.  
Mesmo que você **nunca tenha usado Rasa**, é só seguir as instruções abaixo.

---

## Pré-requisitos rápidos
- **Docker** instalado e funcionando (`docker run --rm hello-world`).
- **Backend** do framework rodando (UI):
  ```bash
  cd backend
  uvicorn app.main:app --host 127.0.0.1 --port 8899 --reload --env-file ./.env
  ```
- Abra no navegador: **http://127.0.0.1:8899/**

> Se estiver no Windows com WSL, acesse pelo Windows em `http://localhost:8899/` e confirme que o Docker do Windows está compartilhando os diretórios com o WSL.

---

## 1) Criar um projeto a partir do PT-Basic

1. Na UI (lado esquerdo), em **Projetos**:
   - Escreva um nome simples, exemplo: `meu-bot`.
   - Clique em **PT-Basic** (isso copia um conjunto de arquivos prontos em PT-BR).
2. Selecione o projeto recém-criado para abrir a **árvore de arquivos**.

Você verá estes arquivos principais:

```
config.yml
domain.yml
data/nlu.yml
data/rules.yml
data/stories.yml
```

---

## 2) Como **preencher** cada arquivo (com exemplos prontos)

### 2.1 `domain.yml` — **Intenções e respostas** do bot
Este arquivo lista as **intenções** (o que o usuário quer) e as **respostas** do bot.

> **O que você precisa fazer aqui?**  
> - **Adicionar/editar** o nome das intenções que seu bot reconhece.  
> - **Criar/editar** as respostas (chamadas de `utter_...`).

**Modelo pronto para copiar** (pode colar e adaptar na UI):  
```yaml
version: "3.1"

intents:
  - saudar
  - despedir
  - ajuda
  - agradecer
  - negar
  - afirmar
  - conversa_fiada
  - ofensa
  - fora_do_escopo
  # adicione novas aqui, ex.:
  # - consulta_saldo

responses:
  utter_saudar:
    - text: "Olá! 👋 Como posso te ajudar hoje?"
  utter_despedir:
    - text: "Até logo! 👋"
  utter_ajuda:
    - text: "Posso te ajudar com perguntas frequentes. Experimente: 'o que você faz?'"
  utter_agradecer:
    - text: "De nada! 🙂"
  utter_conversa_fiada:
    - text: "Haha, boa! 😄 Como posso ajudar de verdade?"
  utter_ofensa:
    - text: "Prefiro manter a conversa respeitosa. Vamos continuar? 🙂"
  utter_fora_do_escopo:
    - text: "Ainda não sei responder isso. Você pode reformular?"
  utter_nao_entendi:
    - text: "Desculpa, não entendi. Você pode perguntar de outro jeito?"

  # exemplo de nova resposta para uma nova intenção
  # utter_consulta_saldo:
  #   - text: "Para consultar seu saldo, abra o app > Minha Conta > Saldo."

session_config:
  session_expiration_time: 60
  carry_over_slots_to_new_session: true
```

> **Regra de ouro:** se você **criar uma nova intenção** (por ex. `consulta_saldo`), crie também a **resposta** `utter_consulta_saldo` (ou a ação correspondente) e **use** essa intenção em **rules** ou **stories** (veja 2.3 e 2.4).

---

### 2.2 `data/nlu.yml` — **Exemplos de frases** por intenção
Aqui você ensina o modelo a **reconhecer** cada intenção. Coloque várias frases **naturais** que as pessoas usariam.

**Modelo pronto para copiar** (edite/complete na UI):
```yaml
version: "3.1"
nlu:
  - intent: saudar
    examples: |
      - oi
      - olá
      - bom dia
      - boa tarde
      - e aí
      - fala aí

  - intent: despedir
    examples: |
      - tchau
      - até mais
      - valeu, falou
      - até logo

  - intent: ajuda
    examples: |
      - ajuda
      - pode me ajudar?
      - estou com dúvida
      - o que você faz?
      - como funciona você?

  - intent: agradecer
    examples: |
      - obrigado
      - valeu
      - brigadão

  - intent: conversa_fiada
    examples: |
      - me conta uma piada
      - quem é você?
      - como vai você?
      - beleza?

  - intent: negar
    examples: |
      - não
      - prefiro que não
      - negativo

  - intent: afirmar
    examples: |
      - sim
      - claro
      - com certeza
      - ok

  - intent: ofensa
    examples: |
      - seu bobo
      - vai te catar
      - [palavrão]

  - intent: fora_do_escopo
    examples: |
      - qual a raiz quadrada de abacaxi?
      - faça meu trabalho
      - você pode consertar meu carro?

  # Exemplo de NOVA intenção de negócio
  # - intent: consulta_saldo
  #   examples: |
  #     - quero ver meu saldo
  #     - como consulto o saldo?
  #     - qual meu saldo?
  #     - saldo por favor
  #     - consulta de saldo
```

> **Dicas:**  
> - Use **8 a 15** exemplos por intenção (quanto mais variados, melhor).  
> - Evite frases gigantes; prefira curtas e diretas.  
> - Não misture intenções diferentes no mesmo bloco.

---

### 2.3 `data/rules.yml` — **Regras** determinísticas
Regras dizem “se a intenção for X, responda Y”. Ótimo para saudações, despedidas, ajuda, ofensa e fallback.

**Modelo pronto para copiar**:
```yaml
version: "3.1"
rules:
  - rule: Responder saudação
    steps:
      - intent: saudar
      - action: utter_saudar

  - rule: Responder despedida
    steps:
      - intent: despedir
      - action: utter_despedir

  - rule: Ajudar quando pedem ajuda
    steps:
      - intent: ajuda
      - action: utter_ajuda

  - rule: Responder agradecimento
    steps:
      - intent: agradecer
      - action: utter_agradecer

  - rule: Anti-ofensa
    steps:
      - intent: ofensa
      - action: utter_ofensa

  - rule: Fora do escopo
    steps:
      - intent: fora_do_escopo
      - action: utter_fora_do_escopo

  # Fallback genérico (quando o modelo não entende)
  - rule: Fallback
    steps:
      - intent: nlu_fallback
      - action: utter_nao_entendi

  # Exemplo para nova intenção:
  # - rule: Consulta de saldo
  #   steps:
  #     - intent: consulta_saldo
  #     - action: utter_consulta_saldo
```

> Se aparecer aviso “intent X não usada”, adicione uma **rule** como acima ou use em **stories**.

---

### 2.4 `data/stories.yml` — **Fluxos** de conversas
Stories ensinam sequências. Ex.: usuário saúda → pede ajuda → bot responde ajuda.

**Modelo pronto para copiar**:
```yaml
version: "3.1"
stories:
  - story: Fluxo de saudação e ajuda
    steps:
      - intent: saudar
      - action: utter_saudar
      - intent: ajuda
      - action: utter_ajuda

  # Exemplo com intenção nova
  # - story: Saldo após saudação
  #   steps:
  #     - intent: saudar
  #     - action: utter_saudar
  #     - intent: consulta_saldo
  #     - action: utter_consulta_saldo
```

> Para começar, **rules** já resolvem bastante. Use **stories** para deixar as conversas mais “naturais” em sequência.

---

### 2.5 `config.yml` — pipeline e políticas (já vem OK)
Você pode manter como está; só ajuste `epochs` se tiver muito mais/menos dados.

**Modelo recomendado**:
```yaml
language: pt

pipeline:
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: word
  - name: DIETClassifier
    epochs: 60
    constrain_similarities: true
  - name: EntitySynonymMapper
  - name: ResponseSelector

policies:
  - name: MemoizationPolicy
  - name: RulePolicy
    core_fallback_threshold: 0.3
    core_fallback_action_name: "utter_nao_entendi"
  - name: TEDPolicy
    epochs: 40
```

---

## 3) Treinar, Iniciar e Conversar (pela UI)

1. **Edite** os arquivos (domain, nlu, rules, stories) e **clique em Salvar** em cada um.
2. Clique **Train** (veja os **Logs**).  
   - Sucesso típico: `Your Rasa model is trained and saved at 'models/....tar.gz'`.
3. No campo **Porta**, digite `5005` (ou outra livre) e clique **Start**.  
   - O **Status** deve mostrar: `Rodando em :5005 (docker)`.
4. Vá ao painel **Chat** e teste: `oi`, `ajuda`, `tchau`, algo fora do escopo etc.

---

## 4) Testes pela linha de comando (opcional)

**Webhook direto no Rasa** (deve responder com uma mensagem do bot):
```bash
curl -s -X POST "http://127.0.0.1:5005/webhooks/rest/webhook" \
  -H "Content-Type: application/json" \
  -d '{"sender":"test","message":"oi"}'
```

**API do backend**:
```bash
# status
curl -s http://127.0.0.1:8899/api/projects/meu-bot/status

# start/stop
curl -s -X POST "http://127.0.0.1:8899/api/projects/meu-bot/inference/start" \
  -H "Content-Type: application/json" -d '{"port": 5005}'

curl -s -X POST "http://127.0.0.1:8899/api/projects/meu-bot/inference/stop"
```

---

## 5) Problemas comuns e soluções

**A) “intent X não usada”**  
→ Falta criar uma **rule** ou **story** que use a intenção. Veja §2.3/§2.4.

**B) Chat diz “Inferência não está rodando”**  
1. Veja **Status** na UI.  
2. Teste o webhook direto (ver §4).  
3. Se precisar, limpe e reinicie:
   ```bash
   docker rm -f rasa-meu-bot || true
   ```
   E clique **Start** de novo.

**C) Modelo não encontrado**  
→ Treine primeiro (**Train**), depois **Start**.

**D) Porta ocupada**  
→ Use outra (5006, 5007…).

**E) Avisos SQLAlchemy**  
→ Avisos conhecidos da linha 3.x do Rasa. Não impedem o uso.

---

## 6) Checklist rápido (para não esquecer)

- [ ] Adicionei minhas **intenções** em `domain.yml` e criei as **responses** `utter_...`?  
- [ ] Coloquei **8–15 exemplos** por intenção em `data/nlu.yml`?  
- [ ] Criei **rules** para intenções simples e **stories** para fluxos?  
- [ ] **Salvei** tudo e cliquei **Train**?  
- [ ] Cliquei **Start** na porta correta?  
- [ ] Testei no **Chat** e também via **webhook**?

Pronto! Agora você consegue **preencher** os arquivos pela UI e publicar bots simples sem complicação. Boa construção! 💙
