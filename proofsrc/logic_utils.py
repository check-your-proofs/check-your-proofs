from ast_types import Or, Not, Forall, Exists, ExistsUniq, Implies, Iff, And, Symbol
from itertools import permutations
from typing import List

def flatten_or(expr) -> List:
    """Or を平坦化して葉のリストを返す"""
    if isinstance(expr, Or):
        return flatten_or(expr.left) + flatten_or(expr.right)
    else:
        return [expr]

# alpha_equiv 内の Or 判定をこれに置き換える例
def or_equiv(e1, e2, env=None):
    """Or の順序と α同値を同時に無視して比較"""
    if env is None:
        env = {}

    # flatten してリスト化
    parts1 = flatten_or(e1)
    parts2 = flatten_or(e2)

    if len(parts1) != len(parts2):
        return False

    # 外側の env に従って α同値判定
    matched = [False] * len(parts2)
    for p1 in parts1:
        found = False
        for i, p2 in enumerate(parts2):
            if not matched[i] and alpha_equiv(p1, p2, env):
                matched[i] = True
                found = True
                break
        if not found:
            return False

    return True

def normalize_neg(e):
    if isinstance(e, Not) and isinstance(e.body, Not):
        return normalize_neg(e.body.body)
    else:
        return e

def alpha_equiv(e1, e2, env=None):
    """束縛変数の順序も無視して α同値判定"""
    if env is None:
        env = {}

    e1 = normalize_neg(e1)
    e2 = normalize_neg(e2)

    # e1, e2 が両方 Not の場合は中身を再帰的に比較
    if isinstance(e1, Not) and isinstance(e2, Not):
        return alpha_equiv(e1.body, e2.body, env)
    # 片方が Not で片方が違う場合は不一致
    if isinstance(e1, Not) != isinstance(e2, Not):
        return False

    for quantifier_type in (Forall, Exists, ExistsUniq):
        if isinstance(e1, quantifier_type) and isinstance(e2, quantifier_type):
            vars1, body1 = collect_quantifier_vars(e1, quantifier_type)
            vars2, body2 = collect_quantifier_vars(e2, quantifier_type)

            if len(vars1) != len(vars2):
                return False

            for perm in permutations(vars2):
                newenv = env.copy()
                for v1, v2 in zip(vars1, perm):
                    newenv[v1] = v2
                if alpha_equiv(body1, body2, newenv):
                    return True
            return False

    if isinstance(e1, Implies) and isinstance(e2, Implies):
        return alpha_equiv(e1.left, e2.left, env) and alpha_equiv(e1.right, e2.right, env)
    
    if isinstance(e1, Iff) and isinstance(e2, Iff):
        return alpha_equiv(e1.left, e2.left, env) and alpha_equiv(e1.right, e2.right, env)

    if isinstance(e1, And) and isinstance(e2, And):
        return alpha_equiv(e1.left, e2.left, env) and alpha_equiv(e1.right, e2.right, env)

    if isinstance(e1, Or) and isinstance(e2, Or):
        return or_equiv(e1, e2, env)

    if isinstance(e1, Symbol) and isinstance(e2, Symbol):
        if e1.name != e2.name or len(e1.args) != len(e2.args):
            return False
        for a, b in zip(e1.args, e2.args):
            mapped = env.get(a, a)
            if mapped != b:
                return False
        return True

    return False

def collect_quantifier_vars(e, quantifier_type):
    vars_ = []
    body = e
    while isinstance(body, quantifier_type):
        vars_.append(body.var)
        body = body.body
    return vars_, body

def collect_vars(expr, bound=None):
    """
    式 expr から自由変数と束縛変数の集合を返す
    戻り値: (free_vars, bound_vars)
    """
    if bound is None:
        bound = set()

    if isinstance(expr, Symbol):
        return set(arg for arg in expr.args if arg not in bound), set()

    elif isinstance(expr, Not):
        return collect_vars(expr.body, bound)

    elif isinstance(expr, (And, Or, Implies, Iff)):
        f1, b1 = collect_vars(expr.left, bound)
        f2, b2 = collect_vars(expr.right, bound)
        return f1 | f2, b1 | b2

    elif isinstance(expr, (Forall, Exists)):
        f_body, b_body = collect_vars(expr.body, bound | {expr.var})
        return f_body, b_body | {expr.var}

    else:
        return set(), set()

# === コンテキスト中の式検索 ===
def expr_in_context(expr, context):
    return any(alpha_equiv(expr, c) for c in context)

def expand_definitions(expr, context):
    if isinstance(expr, Symbol):
        if expr.name in context.definitions:
            definition = context.definitions[expr.name].formula
            vars, body = collect_quantifier_vars(definition, Forall)
            expanded = substitute(body, dict(zip(vars, expr.args))).right
            return expand_definitions(expanded, context)
        else:
            return expr
    elif isinstance(expr, Not):
        return Not(expand_definitions(expr.body, context))
    elif isinstance(expr, (And, Or, Implies, Iff)):
        left = expand_definitions(expr.left, context)
        right = expand_definitions(expr.right, context)
        return type(expr)(left, right)
    elif isinstance(expr, (Forall, Exists)):
        body = expand_definitions(expr.body, context)
        return type(expr)(expr.var, body)
    else:
        return expr

def fresh_var(var, used):
    """used に含まれない新しい変数名を作る"""
    i = 0
    new_var = f"{var}_{i}"
    while new_var in used:
        i += 1
        new_var = f"{var}_{i}"
    return new_var

def substitute(expr, mapping, used_vars=None):
    """
    expr の自由変数を mapping で置換
    束縛変数は mapping に衝突しないよう自動リネーム
    """
    if used_vars is None:
        used_vars = collect_vars(expr)[0] | set(mapping.values())

    if isinstance(expr, Symbol):
        new_args = [mapping.get(arg, arg) for arg in expr.args]
        return Symbol(expr.name, new_args)

    if isinstance(expr, Not):
        return Not(substitute(expr.body, mapping, used_vars))

    if isinstance(expr, (And, Or, Implies, Iff)):
        return type(expr)(substitute(expr.left, mapping, used_vars), substitute(expr.right, mapping, used_vars))

    if isinstance(expr, (Forall, Exists)):
        var = expr.var
        # 衝突する場合は束縛変数をリネーム
        if var in mapping.values() or var in used_vars:
            new_var = fresh_var(var, used_vars)
            used_vars.add(new_var)
            body = substitute(rename_var(expr.body, var, new_var), mapping, used_vars)
            return type(expr)(new_var, body)
        else:
            used_vars.add(var)
            return type(expr)(var, substitute(expr.body, mapping, used_vars))

    return expr

def rename_var(expr, old_var, new_var):
    """式 expr 内の束縛変数 old_var を new_var にリネーム"""
    if isinstance(expr, Symbol):
        new_args = [new_var if a == old_var else a for a in expr.args]
        return Symbol(expr.name, new_args)
    elif isinstance(expr, Not):
        return Not(rename_var(expr.body, old_var, new_var))
    elif isinstance(expr, (And, Or, Implies, Iff)):
        return type(expr)(rename_var(expr.left, old_var, new_var), rename_var(expr.right, old_var, new_var))
    elif isinstance(expr, (Forall, Exists)):
        v = new_var if expr.var == old_var else expr.var
        return type(expr)(v, rename_var(expr.body, old_var, new_var))
    return expr
