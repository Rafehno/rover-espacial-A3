# Análise sintática: valida a estrutura do programa e expande blocos REPEAT
def parse(tokens, lex_errors):
    errors = list(lex_errors)
    tokens, errors = _expand_repeats(tokens, errors)

    if not tokens and not errors:
        errors.append(
            {"line": 0, "message": "Programa vazio: nenhum comando encontrado"})

    success = len(errors) == 0
    return success, errors, tokens


# Expande recursivamente blocos REPEAT n { ... } em sequências planas de tokens
def _expand_repeats(tokens, errors):
    result = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok.type == 'REPEAT':
            if i + 1 >= len(tokens) or tokens[i + 1].type != 'LBRACE':
                errors.append({"line": tok.line, "message": "REPEAT sem '{' correspondente"})
                i += 1
                continue
            i += 2
            body = []
            depth = 1
            while i < len(tokens):
                if tokens[i].type == 'LBRACE':
                    depth += 1
                    body.append(tokens[i])
                    i += 1
                elif tokens[i].type == 'RBRACE':
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                    body.append(tokens[i])
                    i += 1
                else:
                    body.append(tokens[i])
                    i += 1
            else:
                errors.append({"line": tok.line, "message": "REPEAT sem '}' de fechamento"})
                break
            expanded_body, errors = _expand_repeats(body, errors)
            for _ in range(tok.value):
                result.extend(expanded_body)

        elif tok.type in ('LBRACE', 'RBRACE'):
            errors.append({"line": tok.line, "message": "'}' sem REPEAT correspondente"})
            i += 1

        else:
            result.append(tok)
            i += 1

    return result, errors
