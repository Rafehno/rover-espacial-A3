from models.lexer import Token


# Executa os tokens sobre o rover e grid, retornando o histórico de passos para animação
def interpret(tokens, rover, grid):
    steps = []
    log = []

    for token in tokens:
        before = rover.to_dict()
        result = _execute(token, rover, grid)
        after = rover.to_dict()

        steps.append({
            "command": token.type,
            "value": token.value,
            "line": token.line,
            "before": before,
            "after": after,
            "success": result["success"],
            "message": result["message"],
            "scan_result": result.get("scan_result"),
            "sub_command": result.get("sub_command"),
            "if_fired": result.get("if_fired"),
        })

        if token.type == 'IF_OBSTACLE':
            if result.get('if_fired'):
                sub_val = token.value['value']
                log.append(f"Linha {token.line} | IF OBSTACLE → obstáculo, executou {token.value['type']} {sub_val or ''} → {result['message']}")
            else:
                log.append(f"Linha {token.line} | IF OBSTACLE → livre, nenhuma ação")
        else:
            log.append(f"Linha {token.line} | {token.type} {token.value or ''} → {result['message']}")

    return steps, log


# Despacha o token para a função de execução correta
def _execute(token, rover, grid):
    if token.type == 'MOVE':
        return _move(rover, grid, token.value, forward=True)
    if token.type == 'BACK':
        return _move(rover, grid, token.value, forward=False)
    if token.type == 'LEFT':
        rover.turn_left()
        return {"success": True, "message": f"Girou à esquerda → {rover.direction}"}
    if token.type == 'RIGHT':
        rover.turn_right()
        return {"success": True, "message": f"Girou à direita → {rover.direction}"}
    if token.type == 'SCAN':
        nx, ny = rover.next_position()
        blocked = grid.is_blocked(nx, ny)
        msg = "Obstáculo detectado à frente" if blocked else "Caminho livre à frente"
        return {"success": True, "message": msg, "scan_result": blocked}
    if token.type == 'IF_OBSTACLE':
        nx, ny = rover.next_position()
        if grid.is_blocked(nx, ny):
            sub = Token(token.value['type'], token.value['value'], token.line)
            result = _execute(sub, rover, grid)
            result['if_fired'] = True
            result['sub_command'] = token.value['type']
            return result
        return {"success": True, "message": "Caminho livre — IF não executado", "if_fired": False, "sub_command": None}


# Move o rover célula a célula, parando ao bater em borda ou obstáculo
def _move(rover, grid, steps, forward):
    moved = 0

    for _ in range(steps):
        nx, ny = rover.next_position() if forward else rover.prev_position()

        if not grid.is_valid(nx, ny):
            return {"success": False, "message": f"Bloqueado: borda do grid em ({nx},{ny}) após {moved} passo(s)"}
        if grid.has_obstacle(nx, ny):
            return {"success": False, "message": f"Bloqueado: obstáculo em ({nx},{ny}) após {moved} passo(s)"}

        rover.x, rover.y = nx, ny
        moved += 1

    direction = "frente" if forward else "trás"
    return {"success": True, "message": f"Moveu {moved} passo(s) para {direction}"}
