# Exemplos de Scripts

## Missão básica
```
MOVE 3
RIGHT
MOVE 2
SCAN
LEFT
MOVE 1
```

## Patrulha em L
```
MOVE 4
RIGHT
MOVE 4
RIGHT
MOVE 4
```

## Desvio com IF OBSTACLE
```
MOVE 2
IF OBSTACLE LEFT   # vira se há bloqueio à frente
MOVE 3
IF OBSTACLE RIGHT
MOVE 2
```

## Patrulha circular com REPEAT
```
REPEAT 4 {
  MOVE 2
  RIGHT
}
```

## REPEAT aninhado
```
REPEAT 3 {
  REPEAT 2 {
    MOVE 1
    RIGHT
  }
  LEFT
}
```

## Navegação autônoma
```
REPEAT 5 {
  IF OBSTACLE LEFT
  MOVE 1
}
```

## Exploração com scan
```
SCAN
MOVE 2
LEFT
SCAN
MOVE 3
RIGHT
MOVE 1
SCAN
```
