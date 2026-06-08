# Arquitetura do Sistema

## Pipeline de compilação

```
Script do usuário
      ↓
  lexer.py        → tokenização (análise léxica)
      ↓
  parser.py       → validação sintática + expansão de REPEAT
      ↓
  interpreter.py  → execução sobre rover + grid
      ↓
  main.py (Flask) → API JSON  →  POST /run, POST /validate
      ↓
  app.js + p5.js  → animação visual
```

## Módulos

| Arquivo           | Responsabilidade                                              |
|-------------------|---------------------------------------------------------------|
| `lexer.py`        | Transforma texto em tokens; valida palavras e argumentos      |
| `parser.py`       | Verifica a gramática; expande `REPEAT n { }` em tokens planos |
| `interpreter.py`  | Executa tokens sobre `Rover` e `Grid`; gera steps + log      |
| `rover.py`        | Estado do rover: posição (x, y) e direção (N/E/S/W)          |
| `grid.py`         | Grade 2D com obstáculos (lookup O(1) via set)                 |
| `main.py`         | Servidor Flask: rotas de páginas e endpoints da API           |
| `app.js`          | Fetch da API, animação com p5.js, controles de UI             |

## API

- `POST /run` — executa o script; retorna `steps`, `log`, `final_state`, `grid`
- `POST /validate` — valida a sintaxe sem executar; retorna `success`, `errors`

## Formato de resposta `/run`

```json
{
  "success": true,
  "steps": [
    {
      "command": "MOVE",
      "value": 3,
      "line": 1,
      "before": { "x": 0, "y": 0, "dir": "N" },
      "after":  { "x": 0, "y": 3, "dir": "N" },
      "success": true,
      "message": "Moveu 3 passo(s) para frente",
      "scan_result": null,
      "sub_command": null,
      "if_fired": null
    }
  ],
  "log": ["Linha 1 | MOVE 3 → Moveu 3 passo(s) para frente"],
  "final_state": { "x": 0, "y": 3, "dir": "N" },
  "grid": { "width": 10, "height": 10, "obstacles": [] }
}
```
