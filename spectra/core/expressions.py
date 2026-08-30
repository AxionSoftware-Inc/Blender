from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from typing import Mapping


class ExpressionError(ValueError):
    """Raised when an expression is invalid or uses unsupported syntax."""


SAFE_FUNCTIONS: dict[str, object] = {
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

SAFE_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.IfExp,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Compare,
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
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Eq,
    ast.NotEq,
)


@dataclass(frozen=True)
class Expression:
    source: str
    variables: tuple[str, ...]
    _code: object

    def evaluate(self, values: Mapping[str, float] | None = None, /, **kwargs: float) -> float:
        scope: dict[str, object] = {}
        scope.update(SAFE_FUNCTIONS)
        scope.update(SAFE_CONSTANTS)
        if values:
            scope.update(values)
        scope.update(kwargs)

        missing = [name for name in self.variables if name not in scope]
        if missing:
            raise ExpressionError(f"missing variables: {', '.join(missing)}")

        try:
            value = eval(self._code, {"__builtins__": {}}, scope)
        except (ArithmeticError, ValueError, TypeError) as exc:
            raise ExpressionError(str(exc)) from exc

        if not isinstance(value, (int, float)):
            raise ExpressionError("expression must evaluate to a real number")
        value = float(value)
        if not math.isfinite(value):
            raise ExpressionError("expression result must be finite")
        return value


def compile_expression(source: str, variables: tuple[str, ...] = ()) -> Expression:
    if not source.strip():
        raise ExpressionError("expression cannot be empty")
    if len(set(variables)) != len(variables):
        raise ExpressionError("variables must be unique")

    try:
        parsed = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(str(exc)) from exc

    allowed_symbols = set(variables) | SAFE_FUNCTIONS.keys() | SAFE_CONSTANTS.keys()
    for node in ast.walk(parsed):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ExpressionError(f"unsupported syntax: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCTIONS:
                raise ExpressionError("only approved direct function calls are allowed")
        if isinstance(node, ast.Name) and node.id not in allowed_symbols:
            raise ExpressionError(f"unknown symbol: {node.id}")

    return Expression(
        source=source,
        variables=variables,
        _code=compile(parsed, "<spectra-expression>", "eval"),
    )
