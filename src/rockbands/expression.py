"""A tiny, safe evaluator for ratio formulas.

Every ratio is stored once as a string such as ``"(S1/S2)/(N/R)"``. Keeping the
formula as data lets the package

* work out which spectral bands a ratio needs (``required_names``),
* translate it to any sensor's native band ids (``helpers.translate``),
* evaluate it on numpy / xarray / dask arrays without ``eval``.

Only ``+ - * / **``, unary minus, numbers, band names and ``abs/sqrt/log`` are allowed.
"""

from __future__ import annotations

import ast
import operator
from functools import lru_cache
from typing import Any, Mapping

import numpy as np

from .errors import ExpressionError, MissingBandError
from .utils.arrays import mask_nonfinite

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCTIONS = {"abs": np.abs, "sqrt": np.sqrt, "log": np.log}


@lru_cache(maxsize=None)
def _parse(expression: str) -> ast.expr:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"cannot parse formula {expression!r}: {exc.msg}") from exc
    _validate(tree.body, expression)
    return tree.body


def _validate(node: ast.AST, expression: str) -> None:
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        _validate(node.left, expression)
        _validate(node.right, expression)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        _validate(node.operand, expression)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        pass
    elif isinstance(node, ast.Name):
        pass
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and not node.keywords:
        for arg in node.args:
            _validate(arg, expression)
    else:
        raise ExpressionError(f"unsupported syntax {type(node).__name__} in formula {expression!r}")


def required_names(expression: str) -> tuple[str, ...]:
    """Band names used by a formula, in order of first appearance."""
    names: list[tuple[int, str]] = []

    def walk(node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            names.append((node.col_offset, node.id))
        elif isinstance(node, ast.Call):
            for arg in node.args:
                walk(arg)
        else:
            for child in ast.iter_child_nodes(node):
                walk(child)

    walk(_parse(expression))
    seen: dict[str, None] = {}
    for _, name in sorted(names, key=lambda item: item[0]):
        seen.setdefault(name, None)
    return tuple(seen)


def _eval(node: ast.AST, variables: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        try:
            return variables[node.id]
        except KeyError:
            raise MissingBandError(f"no array supplied for {node.id!r}") from None
    if isinstance(node, ast.UnaryOp):
        return _UNARYOPS[type(node.op)](_eval(node.operand, variables))
    if isinstance(node, ast.BinOp):
        return _BINOPS[type(node.op)](_eval(node.left, variables), _eval(node.right, variables))
    if isinstance(node, ast.Call):
        return _FUNCTIONS[node.func.id](*[_eval(a, variables) for a in node.args])  # type: ignore[attr-defined]
    raise ExpressionError(f"unsupported syntax {type(node).__name__}")  # pragma: no cover


def evaluate(expression: str, variables: Mapping[str, Any]) -> Any:
    """Evaluate ``expression``; division by zero yields NaN instead of inf or a warning."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return mask_nonfinite(_eval(_parse(expression), variables))
