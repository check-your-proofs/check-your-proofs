from parser import Theorem, Any, Assume, Conclude, Expr, And, Implies, Forall

# --- ユーティリティ関数 ---

def split_conjunction(expr: Expr) -> list[Expr]:
    """
    A ∧ B を [A, B] に分解する（再帰的に処理）
    """
    if isinstance(expr, And):
        return split_conjunction(expr.left) + split_conjunction(expr.right)
    else:
        return [expr]

def expr_in_context(expr: Expr, context: list[Expr]) -> bool:
    """
    context 内に expr が含まれているかどうかを判定
    """
    return any(expr == c for c in context)

def derivable(expr: Expr, context: list[Expr]) -> bool:
    """
    context から式 expr が導けるかどうかを判定する。
    and_intro / and_elim 相当の処理もここで吸収。
    """
    if expr_in_context(expr, context):
        return True
    # ∧ の除去: (A ∧ B) から A または B を導出
    for c in context:
        if isinstance(c, And):
            if expr == c.left or expr == c.right:
                return True
    # ∧ の導入: A, B が両方 context にあれば A ∧ B を導出
    if isinstance(expr, And):
        if derivable(expr.left, context) and derivable(expr.right, context):
            return True
    return False

# --- 証明チェッカー本体 ---

def check_proof(node, context, derived, indent=0):
    sp = "  " * indent

    # --- Theorem ---
    if isinstance(node, Theorem):
        print(f"{sp}Theorem {node.name}")
        local_context = []
        local_derived = []
        if not check_proof(node.proof, local_context, local_derived, indent + 1):
            return False
        goal = node.proof.conclusion
        if derivable(goal, local_derived):
            print(f"{sp}✔ Theorem {node.name} proved: {goal}")
            return True
        else:
            print(f"{sp}❌ Theorem {node.name} failed: goal {goal} not in {local_derived}")
            return False

    # --- Conclude ---
    elif isinstance(node, Conclude):
        print(f"{sp}>> Checking Conclude {node.conclusion}")
        local_context = list(context)
        local_derived = []
        for stmt in node.body:
            if not check_proof(stmt, local_context, local_derived, indent + 1):
                return False
        if derivable(node.conclusion, local_derived):
            print(f"{sp}✔ Conclude goal {node.conclusion} derived")
            derived.append(node.conclusion)
            return True
        else:
            print(f"{sp}❌ Conclude goal {node.conclusion} not derivable (derived={local_derived})")
            return False

    # --- Assume ---
    elif isinstance(node, Assume):
        print(f"{sp}>> Checking Assume premise={node.premise}, goal={node.conclusion}")
        new_context = context + split_conjunction(node.premise)

        if not node.body:
            # ボディがない場合: 前提から直接ゴールを導けるかを確認
            if derivable(node.conclusion, new_context):
                implication = Implies(node.premise, node.conclusion)
                derived.append(implication)
                print(f"{sp}✔ Derived implication {implication}")
                return True
            else:
                print(f"{sp}❌ Cannot derive {node.conclusion} from {new_context}")
                return False
        else:
            # ボディがある場合: ローカルに検証し、閉じるときに含意を追加
            local_derived = []
            for stmt in node.body:
                if not check_proof(stmt, new_context, local_derived, indent + 1):
                    return False
            implication = Implies(node.premise, node.conclusion)
            derived.append(implication)
            print(f"{sp}✔ Discharged {node.premise}, added {implication} to derived")
            return True

    # --- Any ---
    elif isinstance(node, Any):
        print(f"{sp}>> Entering Any {node.vars}")
        local_context = list(context)
        local_derived = []
        for stmt in node.body:
            if not check_proof(stmt, local_context, local_derived, indent + 1):
                return False

        # local_derived の最後の式を ∀ で一般化
        if local_derived:
            formula = local_derived[-1]
            for v in reversed(node.vars):
                formula = Forall(v, formula)
            derived.append(formula)
            print(f"{sp}✔ Generalized to {formula}")
        return True

    else:
        print(f"{sp}⚠ Unsupported node {node}")
        return False