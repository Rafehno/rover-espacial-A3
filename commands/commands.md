# Linguagem de Comandos — Rover Espacial

## Gramática Formal (GLC)

```
programa    → comando+
comando     → cmd_move | cmd_back | cmd_left | cmd_right | cmd_scan
            | cmd_if | cmd_repeat

cmd_move    → "MOVE" NUMERO
cmd_back    → "BACK" NUMERO
cmd_left    → "LEFT"
cmd_right   → "RIGHT"
cmd_scan    → "SCAN"

cmd_if      → "IF" "OBSTACLE" subcmd
subcmd      → cmd_move | cmd_back | cmd_left | cmd_right | cmd_scan

cmd_repeat  → "REPEAT" NUMERO "{" comando+ "}"

NUMERO      → [1-9][0-9]*
```

---

## Comandos Disponíveis

| Comando    | Sintaxe                   | Descrição                                                        | Exemplo              |
|------------|---------------------------|------------------------------------------------------------------|----------------------|
| Avançar    | `MOVE n`                  | Avança n casas na direção atual                                  | `MOVE 3`             |
| Recuar     | `BACK n`                  | Recua n casas na direção oposta                                  | `BACK 2`             |
| Girar esq. | `LEFT`                    | Gira 90° à esquerda                                              | `LEFT`               |
| Girar dir. | `RIGHT`                   | Gira 90° à direita                                               | `RIGHT`              |
| Detectar   | `SCAN`                    | Detecta obstáculo na célula imediatamente à frente               | `SCAN`               |
| Condicional| `IF OBSTACLE <cmd>`       | Executa `<cmd>` somente se houver bloqueio (obstáculo ou borda) à frente | `IF OBSTACLE LEFT`   |
| Repetir    | `REPEAT n {` … `}`        | Executa o bloco n vezes; blocos podem ser aninhados              | `REPEAT 4 {` … `}`  |

---

## Regras de Sintaxe

- Cada comando ocupa **uma linha**
- Comandos são **case-insensitive** — `MOVE` = `move` = `Move`
- `n` deve ser um inteiro **positivo** entre 1 e 100
- Linhas em branco são **ignoradas**
- Comentários com `#` são **ignorados** (resto da linha)
- Em `REPEAT n {`, o `{` deve estar na **mesma linha** que `REPEAT`
- O `}` de fechamento deve estar **sozinho** em sua linha
- `IF OBSTACLE` considera **bordas e obstáculos** como bloqueio

---

## Comportamento em Bordas e Colisões

- Se o rover atingir a **borda do grid**, o movimento é cancelado e registrado no log
- Se houver um **obstáculo** no caminho, o rover para e o evento é registrado
- `SCAN` verifica apenas a célula **imediatamente à frente** (1 casa)
- `IF OBSTACLE` avalia a mesma condição de `SCAN` no momento da execução

---

## Exemplos de Scripts

### Missão básica
```
MOVE 3
RIGHT
MOVE 2
SCAN
LEFT
MOVE 1
```

### Desvio com IF OBSTACLE
```
MOVE 2
IF OBSTACLE LEFT   # vira se há bloqueio à frente
MOVE 3
IF OBSTACLE RIGHT
MOVE 2
```

### Patrulha com REPEAT
```
REPEAT 4 {
  MOVE 2
  RIGHT
}
```

### REPEAT aninhado
```
REPEAT 3 {
  REPEAT 2 {
    MOVE 1
    RIGHT
  }
  LEFT
}
```

### IF OBSTACLE dentro de REPEAT
```
REPEAT 5 {
  IF OBSTACLE LEFT
  MOVE 1
}
```

---

## Erros Detectados pelo Compilador

| Tipo                      | Exemplo                   | Mensagem gerada                                           |
|---------------------------|---------------------------|-----------------------------------------------------------|
| Comando desconhecido      | `FLY 3`                   | Comando desconhecido: 'FLY'                               |
| Argumento ausente         | `MOVE`                    | 'MOVE' requer exatamente um argumento numérico            |
| Argumento inválido        | `MOVE -1`                 | 'MOVE' requer inteiro entre 1 e 100, recebeu '-1'         |
| Argumento indesejado      | `LEFT 2`                  | 'LEFT' não aceita argumentos                              |
| IF mal formado            | `IF LEFT`                 | Sintaxe: IF OBSTACLE \<comando\>                          |
| Sub-comando inválido      | `IF OBSTACLE FLY`         | Comando desconhecido após IF OBSTACLE: 'FLY'              |
| REPEAT sem chave          | `REPEAT 3`                | REPEAT requer '{' na mesma linha: REPEAT n {              |
| REPEAT sem fechamento     | `REPEAT 3 {` sem `}`      | REPEAT sem '}' de fechamento                              |
| Chave solta               | `}` sem REPEAT            | '}' sem REPEAT correspondente                             |
| Programa vazio            | *(arquivo em branco)*     | Programa vazio: nenhum comando encontrado                 |
