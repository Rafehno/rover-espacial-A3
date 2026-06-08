# Guia do Desenvolvedor — Rover Espacial

Este documento explica cada arquivo, cada função e como estender o sistema com novos comandos e comportamentos.

---

## Visão Geral da Arquitetura

O sistema funciona como um mini-compilador de três estágios:

```
Script de texto
      ↓
  [1] lexer.py        tokenização     — texto → lista de Tokens
      ↓
  [2] parser.py       análise         — valida gramática, expande REPEAT
      ↓
  [3] interpreter.py  execução        — roda os tokens sobre Rover + Grid
      ↓
  main.py (Flask)     API JSON        — POST /run, POST /validate
      ↓
  app.js + p5.js      animação        — consome a API, anima no canvas
```

Cada estágio é independente. Você pode testar cada um isoladamente importando o módulo diretamente em Python.

---

## Arquivos — Explicação Detalhada

---

### `models/rover.py`

Estado do rover: posição `(x, y)` e direção `(N/E/S/W)`.

O sistema de coordenadas é: **x cresce para a direita, y cresce para baixo** (y=0 é o topo do grid). Isso é convencional para grids em tela.

```
DIRECTIONS = ['N', 'E', 'S', 'W']   # ordem para rotação (índices 0,1,2,3)

DELTAS = {
    'N': (0, -1),   # Norte = y diminui (sobe na tela)
    'E': (1,  0),   # Leste = x aumenta (direita)
    'S': (0,  1),   # Sul   = y aumenta (desce na tela)
    'W': (-1, 0),   # Oeste = x diminui (esquerda)
}
```

#### `Rover.__init__(x, y, direction)`
Cria o rover na posição `(x, y)` apontando para `direction`. Valores padrão: `(0, 0, 'N')`.

#### `Rover.turn_left()`
Gira 90° à esquerda. Faz `(índice - 1) % 4` na lista `DIRECTIONS`. Exemplo: `N → W → S → E → N`.

#### `Rover.turn_right()`
Gira 90° à direita. Faz `(índice + 1) % 4`. Exemplo: `N → E → S → W → N`.

#### `Rover.next_position(steps=1)`
Retorna a posição `(x, y)` que ficaria `steps` células **à frente** sem mover o rover. Usado pelo interpreter para checar colisão antes de mover.

#### `Rover.prev_position(steps=1)`
Mesmo que `next_position`, mas na direção **oposta** (usado pelo `BACK`).

#### `Rover.to_dict()`
Serializa o estado para JSON: `{"x": ..., "y": ..., "dir": ...}`. Chamado pelo interpreter para registrar antes/depois de cada comando.

---

### `models/grid.py`

O terreno 2D onde o rover se move.

#### `Grid.__init__(width, height, obstacles)`
Cria o grid. `obstacles` é uma lista de pares `[x, y]` que é convertida para um `set` de tuplas. O set permite verificar colisão em **O(1)** em vez de percorrer uma lista.

#### `Grid.is_valid(x, y)`
Retorna `True` se `(x, y)` está dentro dos limites do grid. Verifica se `0 <= x < width` e `0 <= y < height`.

#### `Grid.has_obstacle(x, y)`
Retorna `True` se há um obstáculo exatamente em `(x, y)`.

#### `Grid.is_blocked(x, y)`
Combinação dos dois acima: retorna `True` se a célula está **fora do grid** ou **tem obstáculo**. Usada pelo `SCAN` e `IF OBSTACLE`.

#### `Grid.to_dict()`
Serializa o grid para JSON. Converte o set de tuplas de volta para lista de listas (o JSON não suporta tuplas).

---

### `models/lexer.py`

Primeira etapa do compilador. Recebe o texto bruto e devolve uma lista de `Token`.

#### Constantes

```python
COMMANDS_WITH_ARG = {'MOVE', 'BACK'}      # comandos que exigem um número
COMMANDS_NO_ARG   = {'LEFT', 'RIGHT', 'SCAN'}  # comandos sem argumento
MAX_LINES = 200    # limite de linhas do script
MAX_ARG   = 100    # limite do argumento numérico (1..100)
```

#### `class Token`
Estrutura de dados mínima: `type` (string), `value` (int, dict ou None), `line` (número da linha). O campo `line` é fundamental para mensagens de erro — sempre aponte o número da linha.

#### `Token.to_dict()`
Serializa para JSON. Usado quando o interpreter monta os steps.

#### `tokenize(script)`
Processa o script linha a linha:

1. Rejeita scripts com mais de `MAX_LINES` linhas (retorna erro imediato).
2. Para cada linha: remove espaços, ignora linhas vazias e comentários (`#`).
3. Faz `upper()` + `split()` para ser case-insensitive.
4. Identifica o comando (primeira palavra) e despacha para o bloco correto:
   - `IF` → valida `IF OBSTACLE <cmd>`, cria `Token('IF_OBSTACLE', {'type': ..., 'value': ...}, line)`
   - `REPEAT` → valida `REPEAT n {`, cria dois tokens: `Token('REPEAT', n, line)` + `Token('LBRACE', None, line)`
   - `}` → cria `Token('RBRACE', None, line)`
   - `COMMANDS_WITH_ARG` → valida e cria `Token(command, n, line)`
   - `COMMANDS_NO_ARG` → valida e cria `Token(command, None, line)`
   - else → erro "Comando desconhecido"

Retorna `(tokens, errors)`. Erros não interrompem o processamento — o lexer coleta todos os erros do script de uma vez.

---

### `models/parser.py`

Segunda etapa. Recebe os tokens do lexer e os transforma na lista final que o interpreter vai executar.

Responsabilidade principal: **expandir `REPEAT` em tempo de análise**, mantendo o interpreter simples.

#### `parse(tokens, lex_errors)`
Ponto de entrada. Adiciona os erros léxicos existentes à lista, chama `_expand_repeats`, verifica programa vazio, e retorna `(success, errors, tokens_expandidos)`.

> **Importante**: a assinatura retorna **3 valores** — quem chama deve fazer:
> ```python
> success, errors, tokens = parse(tokens, lex_errors)
> ```

#### `_expand_repeats(tokens, errors)`
Percorre a lista de tokens e substitui cada bloco `REPEAT n { ... }` por `n` cópias do conteúdo:

```
REPEAT 3 {     →   MOVE 1
  MOVE 1       →   MOVE 1
}              →   MOVE 1
```

Suporta **aninhamento**: um `REPEAT` dentro de outro é expandido recursivamente. Erros comuns detectados:
- `REPEAT` sem `{` na sequência → "REPEAT sem '{' correspondente"
- `REPEAT` sem `}` correspondente → "REPEAT sem '}' de fechamento"
- `}` solto → "'}' sem REPEAT correspondente"

---

### `models/interpreter.py`

Terceira etapa. Recebe a lista de tokens (já expandida) e os executa um por um sobre o rover e o grid.

#### `interpret(tokens, rover, grid)`
Loop principal. Para cada token:
1. Salva o estado do rover antes (`before`)
2. Chama `_execute(token, rover, grid)`
3. Salva o estado depois (`after`)
4. Monta um dict de step com `command`, `value`, `line`, `before`, `after`, `success`, `message`, `scan_result`, `sub_command`, `if_fired`
5. Monta uma linha de log legível

Retorna `(steps, log)`. O `steps` é a lista que o frontend usa para animar.

#### `_execute(token, rover, grid)`
Despacha para a função certa baseado em `token.type`:
- `MOVE` → `_move(rover, grid, n, forward=True)`
- `BACK` → `_move(rover, grid, n, forward=False)`
- `LEFT` → `rover.turn_left()`
- `RIGHT` → `rover.turn_right()`
- `SCAN` → `rover.next_position()` + `grid.is_blocked()`
- `IF_OBSTACLE` → checa `grid.is_blocked(next_pos)`, executa sub-token se bloqueado

#### `_move(rover, grid, steps, forward)`
Move o rover célula a célula (em vez de teletransportar). A cada passo:
1. Calcula a próxima célula (`next_position` ou `prev_position`)
2. Verifica se é válida (`is_valid`)
3. Verifica se tem obstáculo (`has_obstacle`)
4. Se livre, atualiza `rover.x, rover.y`
5. Se bloqueado, para e retorna `success=False` com quantos passos foram dados

Isso permite animar cada célula individualmente no frontend.

---

### `main.py`

Servidor Flask. Serve as páginas HTML e expõe a API.

#### Rotas de páginas
`/`, `/docs`, `/about` → servem os arquivos HTML da pasta `frontend/html/`.
`/css/<filename>`, `/js/<filename>` → servem os arquivos estáticos.

#### `_err(message, code=400)`
Helper para retornar um JSON de erro padronizado. Todos os campos da resposta são preenchidos com valores vazios/nulos para que o frontend não precise tratar ausência de chaves.

#### `_validate_run(data)`
Valida e sanitiza o payload do `POST /run` antes de criar `Rover` e `Grid`:
- `width` e `height`: inteiros entre 5 e 20
- `start_x`, `start_y`: inteiros dentro dos limites do grid
- `start_dir`: deve ser `N`, `E`, `S` ou `W`
- `obstacles`: lista de pares `[x, y]` dentro do grid (pares inválidos são silenciosamente descartados)

Retorna `(erros, dados_limpos)`. Se `erros` for vazio, `dados_limpos` contém tudo tipado e validado.

#### `validate()` — `POST /validate`
Tokeniza e faz parse do script, retorna `{"success": bool, "errors": [...]}`. Não executa nada.

#### `run()` — `POST /run`
Fluxo completo: valida payload → tokeniza → faz parse → executa → retorna steps + log + estado final + grid.

---

### `frontend/js/app.js`

Todo o lado do cliente. Divide-se em blocos:

#### Estado global
```javascript
let obstacles = [];       // posições [[x,y], ...] dos obstáculos
let roverState = {...};   // posição e direção atuais do rover na tela
let gridConfig = {...};   // largura e altura do grid
let trail = new Set();    // células visitadas como "x,y" — O(1) lookup
let subStepsAll = [];     // lista flat de micro-passos para animação
let subStepIdx = 0;       // índice do próximo micro-passo a executar
let animPaused = false;   // flag de pausa
```

#### `cellSize()`
Calcula o lado de cada célula em pixels para caber no canvas (`p.width` e `p.height`). Usa `p.width`/`p.height` — **não** `wrapper.clientWidth` — para ser consistente com `gridOffset()`.

#### `gridOffset(cell)`
Calcula os offsets `ox`, `oy` para centralizar o grid no canvas.

#### `p.setup()`
Inicializa o canvas p5.js. Usa `requestAnimationFrame` para adiar um resize inicial e deixar o layout flex se acomodar antes de renderizar.

#### `p.draw()`
Chamado a cada `redraw()`. Redesenha o grid inteiro: fundo, rastro, obstáculos, rover.

#### `p.mousePressed()`
Detecta clique no canvas e alterna obstáculo na célula clicada. Bloqueia colocar obstáculo na célula do rover.

#### `drawGrid(p, cell, ox, oy)`
Renderiza todas as células: cor de fundo, rastro azul, cor de obstáculo. Depois chama `drawRover`.

#### `drawRover(p, col, row, dir, cell, ox, oy)`
Desenha o rover como um círculo com triângulo apontando para a direção atual. A rotação é feita com `p.rotate()` e os ângulos mapeados por direção.

#### `buildSubSteps(apiSteps, logLines)`
**Função crítica para a animação.** A API retorna um passo por comando (`MOVE 3` = 1 step). Esta função expande para micro-passos de 1 célula cada, para a animação ser fluida.

- `MOVE`/`BACK` com sucesso → expande em `dist` passos de 1 célula
- `IF_OBSTACLE` com sub-comando de movimento → mesma expansão
- Qualquer outro comando → 1 único micro-passo (rotação, scan, bloqueio)

#### `applySubStep(sub)`
Aplica um micro-passo: adiciona a posição anterior ao rastro, atualiza `roverState`, redesenha o canvas, exibe a linha de log correspondente.

#### `runSubSteps()`
Loop de animação com `setTimeout`. A cada iteração aplica um micro-passo e agenda o próximo com o delay do slider de velocidade.

#### `validateScript()` / `runScript()`
Chamam `POST /validate` e `POST /run` respectivamente. `runScript` monta o payload com as configurações do formulário, processa a resposta e inicia a animação.

#### `validateInputs()`
Valida os campos do formulário no lado do cliente antes de enviar para a API (evita round-trip desnecessário).

---

## Como Adicionar um Novo Comando

O processo é sempre o mesmo: **lexer → interpreter → app.js (se tiver animação visual)**. O parser só precisa ser alterado se o novo comando tiver estrutura de bloco (como `REPEAT`).

### Exemplo 1 — `STRAFE n` (mover de lado)

O rover se move `n` células perpendicular à sua direção atual, sem girar.

**Passo 1 — `models/lexer.py`**

Adicione `'STRAFE'` ao set de comandos com argumento:

```python
COMMANDS_WITH_ARG = {'MOVE', 'BACK', 'STRAFE'}
```

Isso é suficiente — o código de tokenização já trata todos os comandos desse set automaticamente.

**Passo 2 — `models/rover.py`**

Adicione um dicionário com as direções laterais:

```python
STRAFE_RIGHT = {'N': (1,0), 'E': (0,1), 'S': (-1,0), 'W': (0,-1)}
STRAFE_LEFT  = {'N': (-1,0), 'E': (0,-1), 'S': (1,0), 'W': (0,1)}
```

Ou adicione um método ao Rover:

```python
def strafe_position(self, steps=1, right=True):
    deltas = STRAFE_RIGHT if right else STRAFE_LEFT
    dx, dy = deltas[self.direction]
    return self.x + dx * steps, self.y + dy * steps
```

**Passo 3 — `models/interpreter.py`**

Adicione um case em `_execute`:

```python
if token.type == 'STRAFE':
    return _strafe(rover, grid, token.value)
```

Implemente `_strafe` (similar a `_move`, mas usando a posição lateral):

```python
def _strafe(rover, grid, steps):
    moved = 0
    deltas = {'N': (1,0), 'E': (0,1), 'S': (-1,0), 'W': (0,-1)}
    dx, dy = deltas[rover.direction]
    for _ in range(steps):
        nx, ny = rover.x + dx, rover.y + dy
        if not grid.is_valid(nx, ny):
            return {"success": False, "message": f"Bloqueado: borda em ({nx},{ny}) após {moved} passo(s)"}
        if grid.has_obstacle(nx, ny):
            return {"success": False, "message": f"Bloqueado: obstáculo em ({nx},{ny}) após {moved} passo(s)"}
        rover.x, rover.y = nx, ny
        moved += 1
    return {"success": True, "message": f"Deslizou {moved} passo(s) para o lado"}
```

**Passo 4 — `frontend/js/app.js`**

Em `buildSubSteps`, adicione `'STRAFE'` na condição de expansão:

```javascript
const directMove = (step.command === 'MOVE' || step.command === 'BACK' || step.command === 'STRAFE');
```

O cálculo de `dx/dy` atual usa a direção do rover + `step.command`. Para `STRAFE` o delta lateral é diferente, então adicione um bloco específico:

```javascript
if (step.command === 'STRAFE' && step.success) {
    const STRAFE_DELTAS = { N: [1,0], E: [0,1], S: [-1,0], W: [0,-1] };
    const [dx, dy] = STRAFE_DELTAS[step.before.dir] || [0, 0];
    // ... mesmo loop de expansão de MOVE
}
```

---

### Exemplo 2 — `TURN_AROUND` (girar 180°)

Sem argumento, gira o rover 180° de uma vez.

**Passo 1 — `models/lexer.py`**

```python
COMMANDS_NO_ARG = {'LEFT', 'RIGHT', 'SCAN', 'TURN_AROUND'}
```

**Passo 2 — `models/interpreter.py`**

```python
if token.type == 'TURN_AROUND':
    rover.turn_right()
    rover.turn_right()
    return {"success": True, "message": f"Virou 180° → {rover.direction}"}
```

Pronto. O lexer e parser não precisam de nenhuma alteração.

---

### Exemplo 3 — `TELEPORT x y` (teletransporte)

Move o rover direto para `(x, y)` se a célula estiver livre.

**Passo 1 — `models/lexer.py`**

`TELEPORT` tem dois argumentos, o que exige um bloco dedicado (como `IF`). Adicione dentro de `tokenize`:

```python
elif command == 'TELEPORT':
    if len(parts) != 3:
        errors.append({"line": line_num, "message": "Sintaxe: TELEPORT x y"})
        continue
    try:
        tx, ty = int(parts[1]), int(parts[2])
        tokens.append(Token('TELEPORT', {'x': tx, 'y': ty}, line_num))
    except ValueError:
        errors.append({"line": line_num, "message": "TELEPORT requer dois inteiros: TELEPORT x y"})
```

**Passo 2 — `models/interpreter.py`**

```python
if token.type == 'TELEPORT':
    tx, ty = token.value['x'], token.value['y']
    if not grid.is_valid(tx, ty):
        return {"success": False, "message": f"TELEPORT fora do grid: ({tx},{ty})"}
    if grid.has_obstacle(tx, ty):
        return {"success": False, "message": f"TELEPORT bloqueado por obstáculo em ({tx},{ty})"}
    rover.x, rover.y = tx, ty
    return {"success": True, "message": f"Teletransportado para ({tx},{ty})"}
```

**Passo 3 — `frontend/js/app.js`**

`TELEPORT` não tem animação de movimento célula-a-célula — é um salto. Cai automaticamente no bloco `else` de `buildSubSteps`, que cria um único micro-passo do antes para o depois. Não precisa de nenhuma alteração.

---

### Exemplo 4 — `IF FREE <cmd>` (executar se o caminho está livre)

Inverso do `IF OBSTACLE`: executa o sub-comando **somente se não houver bloqueio** à frente.

**Passo 1 — `models/lexer.py`**

No bloco `if command == 'IF':`, a verificação atual é `parts[1] != 'OBSTACLE'`. Adicione suporte para `FREE`:

```python
if command == 'IF':
    if len(parts) < 3 or parts[1] not in ('OBSTACLE', 'FREE'):
        errors.append(...)
        continue
    condition = parts[1]  # 'OBSTACLE' ou 'FREE'
    sub_cmd = parts[2]
    # ... mesma validação de sub_cmd
    token_type = 'IF_OBSTACLE' if condition == 'OBSTACLE' else 'IF_FREE'
    tokens.append(Token(token_type, {'type': sub_cmd, 'value': n}, line_num))
```

**Passo 2 — `models/interpreter.py`**

```python
if token.type == 'IF_FREE':
    nx, ny = rover.next_position()
    if not grid.is_blocked(nx, ny):   # nota: condição invertida
        sub = Token(token.value['type'], token.value['value'], token.line)
        result = _execute(sub, rover, grid)
        result['if_fired'] = True
        result['sub_command'] = token.value['type']
        return result
    return {"success": True, "message": "Caminho bloqueado — IF FREE não executado", "if_fired": False, "sub_command": None}
```

**Passo 3 — `frontend/js/app.js`**

Em `buildSubSteps`, adicione `'IF_FREE'` ao lado de `'IF_OBSTACLE'`:

```javascript
const ifMove = (step.command === 'IF_OBSTACLE' || step.command === 'IF_FREE') &&
               step.if_fired && (step.sub_command === 'MOVE' || step.sub_command === 'BACK');
```

---

## Tabela de Referência — Onde Mexer por Tipo de Alteração

| O que você quer fazer                          | Arquivos a alterar                                 |
|------------------------------------------------|----------------------------------------------------|
| Novo comando simples (sem argumento)           | `lexer.py` (add ao set) + `interpreter.py`         |
| Novo comando com 1 argumento numérico          | `lexer.py` (add ao set) + `interpreter.py`         |
| Novo comando com sintaxe especial              | `lexer.py` (bloco dedicado) + `interpreter.py`     |
| Novo comando com estrutura de bloco            | `lexer.py` + `parser.py` + `interpreter.py`        |
| Animação de movimento novo                     | `app.js` (`buildSubSteps`)                         |
| Novo visual no grid (ex: tipos de terreno)     | `grid.py` + `app.js` (`drawGrid`)                  |
| Mudar limites (tamanho do grid, max linhas)    | `main.py` (`_validate_run`) + `lexer.py`           |
| Nova rota na API                               | `main.py`                                          |
| Novo campo na resposta do `/run`               | `interpreter.py` (`interpret`) + `app.js`          |

---

## Pontos de Atenção

**`parse()` retorna 3 valores**
```python
# CORRETO
success, errors, tokens = parse(tokens, lex_errors)

# ERRADO (vai dar ValueError: too many values to unpack)
success, errors = parse(tokens, lex_errors)
```

**`Token.value` para `IF_OBSTACLE` é um dict, não um int**
```python
token.value = {'type': 'MOVE', 'value': 3}
# para acessar: token.value['type'], token.value['value']
```

**O interpreter só recebe tokens expandidos**
Depois que `parser.py` processa, os tokens de `REPEAT`/`LBRACE`/`RBRACE` não existem mais na lista. O interpreter nunca vê `REPEAT`.

**`before` e `after` no step são snapshots**
São dicts com `{x, y, dir}` capturados antes e depois de `_execute`. Se o comando não move o rover (ex: `SCAN`), `before == after`.

**Coordenadas: y cresce para baixo**
`(0, 0)` é o canto superior esquerdo. Norte = `y - 1`. Isso é padrão para grids em tela mas contraintuitivo para quem pensa em coordenadas cartesianas.
