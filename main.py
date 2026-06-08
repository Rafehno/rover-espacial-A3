import os
from flask import Flask, request, jsonify, send_from_directory

from models.lexer import tokenize
from models.parser import parse
from models.interpreter import interpret
from models.rover import Rover
from models.grid import Grid

app = Flask(__name__)

FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")
_VALID_DIRS = {'N', 'E', 'S', 'W'}


# ── Páginas estáticas ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(os.path.join(FRONTEND, "html"), "index.html")


@app.route("/docs")
def docs():
    return send_from_directory(os.path.join(FRONTEND, "html"), "docs.html")


@app.route("/about")
def about():
    return send_from_directory(os.path.join(FRONTEND, "html"), "about.html")


@app.route("/css/<path:filename>")
def css(filename):
    return send_from_directory(os.path.join(FRONTEND, "css"), filename)


@app.route("/js/<path:filename>")
def js(filename):
    return send_from_directory(os.path.join(FRONTEND, "js"), filename)


# ── Helpers ───────────────────────────────────────────────────────────────────

# Resposta de erro padronizada para a API
def _err(message, code=400):
    return jsonify({
        "success": False,
        "errors": [{"line": 0, "message": message}],
        "steps": [], "log": [], "final_state": None, "grid": None,
    }), code


# Valida e limpa o payload de /run antes de criar Rover e Grid
def _validate_run(data):
    errors = []

    width = data.get("width",  10)
    height = data.get("height", 10)

    if not isinstance(width,  int) or not (5 <= width <= 20):
        errors.append(
            {"line": 0, "message": f"width deve ser inteiro entre 5 e 20 (recebido: {width!r})"})
    if not isinstance(height, int) or not (5 <= height <= 20):
        errors.append(
            {"line": 0, "message": f"height deve ser inteiro entre 5 e 20 (recebido: {height!r})"})
    if errors:
        return errors, None

    start_x = data.get("start_x",   0)
    start_y = data.get("start_y",   0)
    start_dir = data.get("start_dir", "N")

    if not isinstance(start_x, int) or not (0 <= start_x < width):
        errors.append(
            {"line": 0, "message": f"start_x deve ser inteiro entre 0 e {width - 1}"})
    if not isinstance(start_y, int) or not (0 <= start_y < height):
        errors.append(
            {"line": 0, "message": f"start_y deve ser inteiro entre 0 e {height - 1}"})
    if start_dir not in _VALID_DIRS:
        errors.append(
            {"line": 0, "message": f"start_dir inválido: '{start_dir}' — use N, E, S ou W"})

    raw_obs = data.get("obstacles", [])
    if not isinstance(raw_obs, list):
        errors.append({"line": 0, "message": "obstacles deve ser uma lista"})
        raw_obs = []

    obstacles = [
        obs for obs in raw_obs
        if (isinstance(obs, (list, tuple)) and len(obs) == 2
            and isinstance(obs[0], int) and isinstance(obs[1], int)
            and 0 <= obs[0] < width and 0 <= obs[1] < height)
    ]

    if errors:
        return errors, None

    return [], {
        "width": width, "height": height,
        "start_x": start_x, "start_y": start_y,
        "start_dir": start_dir,
        "obstacles": obstacles,
        "script": data.get("script", ""),
    }


# ── API ───────────────────────────────────────────────────────────────────────

# Valida a sintaxe do script sem executá-lo
@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json(force=True)
    if data is None:
        return _err("Corpo da requisição deve ser JSON válido")
    tokens, lex_errors = tokenize(data.get("script", ""))
    success, errors, _ = parse(tokens, lex_errors)
    return jsonify({"success": success, "errors": errors})


# Executa o script e retorna o histórico de passos para animação
@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(force=True)
    if data is None:
        return _err("Corpo da requisição deve ser JSON válido")

    val_errors, clean = _validate_run(data)
    if val_errors:
        return jsonify({
            "success": False, "errors": val_errors,
            "steps": [], "log": [], "final_state": None, "grid": None,
        }), 400

    tokens, lex_errors = tokenize(clean["script"])
    success, errors, tokens = parse(tokens, lex_errors)
    if not success:
        return jsonify({
            "success": False, "errors": errors,
            "steps": [], "log": [], "final_state": None, "grid": None,
        })

    rover = Rover(x=clean["start_x"], y=clean["start_y"],
                  direction=clean["start_dir"])
    grid = Grid(width=clean["width"],
                height=clean["height"], obstacles=clean["obstacles"])

    steps, log = interpret(tokens, rover, grid)

    return jsonify({
        "success": True, "errors": [],
        "steps": steps,
        "log": log,
        "final_state": rover.to_dict(),
        "grid": grid.to_dict(),
    })


if __name__ == "__main__":
    app.run(debug=False)
