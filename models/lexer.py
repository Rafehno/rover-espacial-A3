COMMANDS_WITH_ARG = {'MOVE', 'BACK'}
COMMANDS_NO_ARG   = {'LEFT', 'RIGHT', 'SCAN'}

MAX_LINES = 200
MAX_ARG   = 100


# Unidade mínima extraída do script: tipo, valor numérico e linha de origem
class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def to_dict(self):
        return {"type": self.type, "value": self.value, "line": self.line}


# Análise léxica: transforma o texto do script em uma lista de Tokens
def tokenize(script):
    tokens = []
    errors = []

    all_lines = script.splitlines()

    if len(all_lines) > MAX_LINES:
        errors.append({"line": 0, "message": f"Script muito longo: máximo {MAX_LINES} linhas (recebido {len(all_lines)})"})
        return tokens, errors

    for line_num, raw_line in enumerate(all_lines, start=1):
        line = raw_line.strip()

        if not line or line.startswith('#'):
            continue

        line = line.split('#')[0].strip()
        parts = line.upper().split()
        command = parts[0]

        if command == 'IF':
            if len(parts) < 3 or parts[1] != 'OBSTACLE':
                errors.append({"line": line_num, "message": "Sintaxe: IF OBSTACLE <comando>"})
                continue
            sub_cmd = parts[2]
            if sub_cmd in COMMANDS_WITH_ARG:
                if len(parts) != 4:
                    errors.append({"line": line_num, "message": f"IF OBSTACLE {sub_cmd} requer exatamente um argumento numérico"})
                    continue
                try:
                    n = int(parts[3])
                    if n < 1 or n > MAX_ARG:
                        raise ValueError
                    tokens.append(Token('IF_OBSTACLE', {'type': sub_cmd, 'value': n}, line_num))
                except ValueError:
                    errors.append({"line": line_num, "message": f"IF OBSTACLE {sub_cmd} requer inteiro entre 1 e {MAX_ARG}, recebeu '{parts[3]}'"})
            elif sub_cmd in COMMANDS_NO_ARG:
                if len(parts) != 3:
                    errors.append({"line": line_num, "message": f"IF OBSTACLE {sub_cmd} não aceita argumentos"})
                    continue
                tokens.append(Token('IF_OBSTACLE', {'type': sub_cmd, 'value': None}, line_num))
            else:
                errors.append({"line": line_num, "message": f"Comando desconhecido após IF OBSTACLE: '{parts[2]}'"})

        elif command == 'REPEAT':
            if len(parts) < 2:
                errors.append({"line": line_num, "message": "REPEAT requer um número de repetições"})
                continue
            try:
                n = int(parts[1])
                if n < 1 or n > MAX_ARG:
                    raise ValueError
            except ValueError:
                errors.append({"line": line_num, "message": f"REPEAT requer inteiro entre 1 e {MAX_ARG}, recebeu '{parts[1]}'"})
                continue
            if len(parts) < 3 or parts[2] != '{':
                errors.append({"line": line_num, "message": "REPEAT requer '{' na mesma linha: REPEAT n {"})
                continue
            if len(parts) > 3:
                errors.append({"line": line_num, "message": "Nada deve vir após '{' na linha REPEAT"})
                continue
            tokens.append(Token('REPEAT', n, line_num))
            tokens.append(Token('LBRACE', None, line_num))

        elif command == '{':
            errors.append({"line": line_num, "message": "'{' isolado — use REPEAT n { para iniciar um bloco"})

        elif command == '}':
            if len(parts) != 1:
                errors.append({"line": line_num, "message": "'}' não aceita argumentos"})
                continue
            tokens.append(Token('RBRACE', None, line_num))

        elif command in COMMANDS_WITH_ARG:
            if len(parts) != 2:
                errors.append({"line": line_num, "message": f"'{command}' requer exatamente um argumento numérico"})
                continue
            try:
                n = int(parts[1])
                if n < 1 or n > MAX_ARG:
                    raise ValueError
                tokens.append(Token(command, n, line_num))
            except ValueError:
                errors.append({"line": line_num, "message": f"'{command}' requer inteiro entre 1 e {MAX_ARG}, recebeu '{parts[1]}'"})

        elif command in COMMANDS_NO_ARG:
            if len(parts) != 1:
                errors.append({"line": line_num, "message": f"'{command}' não aceita argumentos"})
                continue
            tokens.append(Token(command, None, line_num))

        else:
            errors.append({"line": line_num, "message": f"Comando desconhecido: '{parts[0]}'"})

    return tokens, errors
