from parser import Theorem, Any, Assume, By, Conclude

def split_conjunction(expr: str):
    if "\\wedge" in expr:
        return [part.strip() for part in expr.split("\\wedge")]
    else:
        return [expr]
    
def derivable(conclusion: str, context: list[str]) -> bool:
    return conclusion in context

def check_proof(node, context=None, depth=0):
    if context is None:
        context = []

    indent = "  " * depth
    print(f"{indent}>> Checking {type(node).__name__} with context: {context}")

    if isinstance(node, Theorem):
        print(f"{indent}Theorem {node.name}")
        return check_proof(node.proof, context, depth+1)

    elif isinstance(node, Any):
        local_context = context.copy()
        for stmt in node.body:
            if not check_proof(stmt, local_context, depth+1):
                return False
        # 全称化
        if local_context:
            last = local_context[-1]
            for var in reversed(node.vars):
                last = f"\\forall {var}{last}"
            context.append(last)
            print(f"{indent}Added universal: {last}")
        return True
    
    elif isinstance(node, Assume):
        local_context = context + [node.premise]
        print(f"{indent}Assume {node.premise} ... goal {node.conclusion}")
        for stmt in node.body:
            if not check_proof(stmt, local_context, depth+1):
                return False
        implication = f"({node.premise}\\to {node.conclusion})"
        context.append(implication)
        print(f"{indent}Added implication: {implication}")
        return True

    elif isinstance(node, By):
        print(f"{indent}By-step: {node}")
        # TODO: definition 参照や推論規則の処理を追加
        return True  

    elif isinstance(node, Conclude):
        local_context = context[:]
        for stmt in node.body:
            if not check_proof(stmt, local_context, depth+1):
                return False
        print(f"{indent}Conclude requires: {node.conclusion}")
        return node.conclusion in local_context

    else:
        raise ValueError(f"Unknown node type: {type(node)}")
