# Linguagem de Comandos

Ver referência completa em [`commands/commands.md`](../commands/commands.md).

## Resumo rápido

| Comando              | O que faz                                         |
|----------------------|---------------------------------------------------|
| `MOVE n`             | Avança n casas                                    |
| `BACK n`             | Recua n casas                                     |
| `LEFT` / `RIGHT`     | Gira 90° à esquerda / direita                     |
| `SCAN`               | Detecta obstáculo à frente                        |
| `IF OBSTACLE <cmd>`  | Executa `<cmd>` se há bloqueio à frente           |
| `REPEAT n { … }`     | Repete o bloco n vezes                            |

- Case-insensitive, comentários com `#`, limites: n entre 1–100, máx. 200 linhas.
