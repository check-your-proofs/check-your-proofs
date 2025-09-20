from parser import Theorem, Any, Assume, By, Conclude, Expr, And, Implies

def split_conjunction(expr: Expr) -> list[Expr]:
    if isinstance(expr, And):
        return split_conjunction(expr.left) + split_conjunction(expr.right)
    else:
        return [expr]

def expr_in_context(expr: Expr, context: list[Expr]) -> bool:
    return any(expr == c for c in context)
    
def derivable(conclusion: str, context: list[str]) -> bool:
    return conclusion in context

def check_proof(node, context=None, indent=0):
    if context is None:
        context = []

    sp = "  " * indent

    # --- Theorem ---
    if isinstance(node, Theorem):
        print(f"{sp}Checking theorem {node.name} ...")
        ok = check_proof(node.proof, context, indent + 1)
        if ok:
            print(f"{sp}✔ Theorem {node.name} OK")
        else:
            print(f"{sp}❌ Theorem {node.name} Failed")
        return ok

    # --- Conclude ---
    elif isinstance(node, Conclude):
        print(f"{sp}>> Checking Conclude with context: {[str(c) for c in context]}")
        local_context = context[:]
        for stmt in node.body:
            if not check_proof(stmt, local_context, indent + 1):
                return False
        ok = expr_in_context(node.conclusion, local_context)
        if ok:
            print(f"{sp}✔ Conclude matched: {node.conclusion}")
        else:
            print(f"{sp}❌ Conclude requires: {node.conclusion}")
        return ok

    # --- Assume ---
    elif isinstance(node, Assume):
        print(f"{sp}>> Checking Assume premise={node.premise}, goal={node.conclusion}")
        new_context = context + split_conjunction(node.premise)
        if not node.body:
            ok = expr_in_context(node.conclusion, new_context)
            if ok:
                print(f"{sp}✔ Derived directly: {node.conclusion}")
                context.append(Implies(node.premise, node.conclusion))
            else:
                print(f"{sp}❌ Cannot derive {node.conclusion} from {new_context}")
            return ok
        else:
            for stmt in node.body:
                if not check_proof(stmt, new_context, indent + 1):
                    return False
            implication = Implies(node.premise, node.conclusion)
            context.append(implication)
            print(f"{sp}✔ Added implication: {implication}")
            return True

    # --- Any ---
    elif isinstance(node, Any):
        print(f"{sp}>> Checking Any {node.vars}")
        for stmt in node.body:
            if not check_proof(stmt, context, indent + 1):
                return False
        return True

    # --- By ---
    elif isinstance(node, By):
        print(f"{sp}By {node.definition} (skipped for now)")
        return True

    else:
        print(f"{sp}Unknown node: {node}")
        return False
