# Rover Espacial

Simulador de rover com linguagem de comandos própria — trabalho prático A3 de **Teoria da Computação e Compiladores** · Unicuritiba · Entrega: 08/06/2025.

---

## O que é

Um sistema web que permite escrever scripts em uma linguagem simples e ver o rover se mover em um grid 2D animado, passo a passo. O projeto implementa as três etapas clássicas de um compilador:

1. **Análise léxica** (`lexer.py`) — tokeniza o script
2. **Análise sintática** (`parser.py`) — valida a gramática e expande blocos `REPEAT`
3. **Interpretação** (`interpreter.py`) — executa os comandos sobre o rover e o grid

---

## Linguagem de Comandos

| Comando              | Descrição                                         | Exemplo              |
|----------------------|---------------------------------------------------|----------------------|
| `MOVE n`             | Avança n casas na direção atual                   | `MOVE 3`             |
| `BACK n`             | Recua n casas                                     | `BACK 2`             |
| `LEFT`               | Gira 90° à esquerda                               | `LEFT`               |
| `RIGHT`              | Gira 90° à direita                                | `RIGHT`              |
| `SCAN`               | Detecta obstáculo à frente                        | `SCAN`               |
| `IF OBSTACLE <cmd>`  | Executa `<cmd>` se há bloqueio à frente           | `IF OBSTACLE LEFT`   |
| `REPEAT n { … }`     | Repete o bloco n vezes (suporta aninhamento)      | `REPEAT 4 { … }`     |

Comentários com `#`, case-insensitive, linhas em branco ignoradas.
Referência completa: [`commands/commands.md`](commands/commands.md)

---

## Arquitetura

```
Script do usuário
      ↓
  lexer.py        → tokenização (análise léxica)
      ↓
  parser.py       → validação sintática + expansão de REPEAT
      ↓
  interpreter.py  → execução sobre rover + grid
      ↓
  main.py (Flask) → API JSON
      ↓
  app.js + p5.js  → animação visual
```

**Endpoints da API:**
- `POST /run` — executa o script, retorna steps + log
- `POST /validate` — valida a sintaxe sem executar

---

## Estrutura de Diretórios

```
rover-espacial_A3/
├── main.py                   ← servidor Flask
├── requirements.txt
├── models/
│   ├── lexer.py              ← tokenização
│   ├── parser.py             ← validação sintática + expansão de REPEAT
│   ├── interpreter.py        ← execução dos comandos
│   ├── rover.py              ← estado do rover (x, y, direção)
│   └── grid.py               ← grade 2D + obstáculos
├── frontend/
│   ├── html/                 ← index.html, docs.html, about.html
│   ├── css/                  ← bootstrap.min.css, style.css
│   └── js/                   ← p5.min.js, bootstrap.bundle.min.js, app.js
├── commands/
│   └── commands.md           ← spec formal da linguagem (GLC)
└── docs/
    ├── linguagem.md          ← resumo da linguagem
    ├── arquitetura.md        ← arquitetura e formato da API
    └── exemplos.md           ← exemplos de scripts
```

---

## Stack

| Camada       | Tecnologia               |
|--------------|--------------------------|
| Servidor     | Flask 3.x · Python 3.10+ |
| Visualização | p5.js 1.9                |
| UI / Layout  | Bootstrap 5.3 (local)    |
| Comunicação  | Fetch API · JSON         |

---

## Como rodar

```bash
# 1. Clonar o repositório
git clone <url-do-repo>
cd rover-espacial_A3

# 2. Criar ambiente virtual (opcional mas recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Rodar o servidor
python main.py

# 5. Acessar em
# http://localhost:5000
```

---

## Equipe

| Nome              | RA         |
|-------------------|------------|
| Diogo Varela      | 172316253  |
| Gabriel Fernandes | 172317728  |
| João Brasil       | 172311360  |
| Gabriel Klein     | 172312555  |
| João Demech       | 172311321  |
| Breno da Silva    | 172416094  |
