from parser import Theorem, Any, Assume, By, Conclude, Expr, And, Implies, Forall

def split_conjunction(expr: Expr) -> list[Expr]:
    if isinstance(expr, And):
        return split_conjunction(expr.left) + split_conjunction(expr.right)
    else:
        return [expr]

def expr_in_context(expr: Expr, context: list[Expr]) -> bool:
    return any(expr == c for c in context)
    
def derivable(conclusion: str, context: list[str]) -> bool:
    return conclusion in context

def check_proof(node, context, derived, indent=0):
    sp = "  " * indent

    # --- Theorem ---
    if isinstance(node, Theorem):
        print(f"{sp}Theorem {node.name}")
        local_context = []
        local_derived = []
        if not check_proof(node.proof, local_context, local_derived, indent + 1):
            return False
        # 定理のゴールは proof.conclusion に入っている
        goal = node.proof.conclusion
        if expr_in_context(goal, local_derived):
            print(f"{sp}✔ Theorem {node.name} proved: {goal}")
            return True
        else:
            print(f"{sp}❌ Theorem {node.name} failed: goal {goal} not in {local_derived}")
            return False

    # --- Conclude ---
    elif isinstance(node, Conclude):
        print(f"{sp}>> Checking Conclude {node.conclusion}")
        local_context = list(context)
        local_derived = list(derived)
        for stmt in node.body:
            if not check_proof(stmt, local_context, local_derived, indent + 1):
                return False
        if expr_in_context(node.conclusion, local_derived):
            print(f"{sp}✔ Conclude goal {node.conclusion} derived")
            derived.append(node.conclusion)
            return True
        else:
            print(f"{sp}❌ Conclude goal {node.conclusion} not found in derived={local_derived}")
            return False

    # --- Assume ---
    elif isinstance(node, Assume):
        print(f"{sp}>> Checking Assume premise={node.premise}, goal={node.conclusion}")
        new_context = context + split_conjunction(node.premise)

        if not node.body:
            if expr_in_context(node.conclusion, new_context):
                implication = Implies(node.premise, node.conclusion)
                derived.append(implication)
                print(f"{sp}✔ Derived implication {implication}")
                return True
            else:
                print(f"{sp}❌ Cannot derive {node.conclusion} from {new_context}")
                return False
        else:
            local_derived = list(derived)
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
        local_derived = list(derived)
        for stmt in node.body:
            if not check_proof(stmt, local_context, local_derived, indent + 1):
                return False

        # local_derived に入っている最後の式を ∀化する
        if local_derived:
            formula = local_derived[-1]
            for v in reversed(node.vars):
                formula = Forall(v, formula)
            derived.append(formula)
            print(f"{sp}✔ Generalized to {formula}")
        return True
