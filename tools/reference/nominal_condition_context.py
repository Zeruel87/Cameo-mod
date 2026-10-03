"""Small, non-executing evaluator for an explicitly empty condition context.

Only logical operators and integer comparisons are supported. Unknown syntax is
unresolved, never silently false. This does not resolve factory condition grants.
"""
import ast
import operator
import re

IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]*')
COMPARISONS = {ast.Eq: operator.eq, ast.NotEq: operator.ne,
               ast.Lt: operator.lt, ast.LtE: operator.le,
               ast.Gt: operator.gt, ast.GtE: operator.ge}


def identifiers(expression):
    return set(IDENTIFIER.findall(expression or '')) - {'true', 'false'}


def evaluate_context(expression, conditions):
    if expression is None or not expression.strip():
        return True
    # Quoting, functions, indexing, arithmetic and other language features are
    # outside this reviewed subset. Never pass source expressions to eval().
    if not re.fullmatch(r'[A-Za-z0-9_.\-!<>=&|()\s]+', expression):
        return None
    if any(type(v) is not int for v in conditions.values()):
        return None
    text = IDENTIFIER.sub(lambda m: str(1 if m[0] == 'true' else conditions.get(m[0], 0)), expression)
    text = re.sub(r'!(?!=)', ' not ', text).replace('&&', ' and ').replace('||', ' or ')

    def value(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not value(node.operand)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -value(node.operand)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            parts = [bool(value(x)) for x in node.values]
            return all(parts) if isinstance(node.op, ast.And) else any(parts)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in COMPARISONS:
            return COMPARISONS[type(node.ops[0])](value(node.left), value(node.comparators[0]))
        raise ValueError('unsupported condition syntax')

    try:
        return bool(value(ast.parse(text.strip(), mode='eval').body))
    except (SyntaxError, ValueError, TypeError):
        return None


def empty_context(expression):
    return evaluate_context(expression, {})
