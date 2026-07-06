import ast
import math


SAFE_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
}


SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.FloorDiv,
)


class FormulaValidationError(ValueError):
    pass


def _validate_ast(node, variables):
    for child in ast.walk(node):
        if not isinstance(child, ALLOWED_AST_NODES):
            raise FormulaValidationError(
                f"Unsupported syntax: {type(child).__name__}"
            )
        if isinstance(child, ast.Call):
            if not isinstance(child.func, ast.Name):
                raise FormulaValidationError("Only direct function calls are allowed")
            if child.func.id not in SAFE_FUNCTIONS:
                raise FormulaValidationError(
                    f"Function '{child.func.id}' is not allowed"
                )
        if isinstance(child, ast.Name):
            if child.id not in variables and child.id not in SAFE_FUNCTIONS and child.id not in SAFE_CONSTANTS:
                raise FormulaValidationError(
                    f"Unknown symbol '{child.id}'"
                )


def compile_formula(expression, variables):
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise FormulaValidationError(str(exc)) from exc

    _validate_ast(parsed, set(variables))
    code = compile(parsed, "<spectra-formula>", "eval")

    def evaluator(**kwargs):
        scope = {}
        scope.update(SAFE_FUNCTIONS)
        scope.update(SAFE_CONSTANTS)
        scope.update(kwargs)
        return eval(code, {"__builtins__": {}}, scope)

    return evaluator


def extract_symbols(expression):
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise FormulaValidationError(str(exc)) from exc

    symbols = set()
    for child in ast.walk(parsed):
        if isinstance(child, ast.Name):
            if child.id not in SAFE_FUNCTIONS and child.id not in SAFE_CONSTANTS:
                symbols.add(child.id)
    return sorted(symbols)


def parse_parameter_values(parameter_string):
    values = {}
    if not parameter_string.strip():
        return values

    for raw_chunk in parameter_string.split(","):
        chunk = raw_chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise FormulaValidationError(
                f"Invalid parameter chunk '{chunk}'. Use name=value format."
            )
        name, raw_value = chunk.split("=", 1)
        name = name.strip()
        raw_value = raw_value.strip()
        if not name.isidentifier():
            raise FormulaValidationError(f"Invalid parameter name '{name}'")
        try:
            values[name] = float(raw_value)
        except ValueError as exc:
            raise FormulaValidationError(
                f"Parameter '{name}' must be numeric"
            ) from exc
    return values


def detect_parameters(expression):
    return [
        symbol for symbol in extract_symbols(expression)
        if symbol not in {"x", "y", "t"}
    ]


def parameter_animation_value(frame_current, settings):
    frame_start = min(settings.parameter_frame_start, settings.parameter_frame_end)
    frame_end = max(settings.parameter_frame_start, settings.parameter_frame_end)
    if frame_end == frame_start:
        return settings.animated_parameter_end

    frame = min(max(frame_current, frame_start), frame_end)
    factor = (frame - frame_start) / (frame_end - frame_start)
    return settings.animated_parameter_start + (
        settings.animated_parameter_end - settings.animated_parameter_start
    ) * factor


def resolve_parameter_scope(frame_current, settings):
    parameter_scope = parse_parameter_values(settings.parameter_values)
    for parameter_name in detect_parameters(settings.expression):
        parameter_scope.setdefault(parameter_name, 0.0)

    if settings.parameter_animation_enabled and settings.animated_parameter.strip():
        parameter_scope[settings.animated_parameter.strip()] = parameter_animation_value(
            frame_current, settings
        )
    return parameter_scope
