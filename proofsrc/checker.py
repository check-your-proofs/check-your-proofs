from parser import Theorem, Any, Assume, By, Definition

def check_proof(node, context=None):
    if context is None:
        context = []

    if isinstance(node, Theorem):
        print(f"Checking theorem {node.name} ...")
        return check_proof(node.proof, context)

    elif isinstance(node, Any):
        for stmt in node.body:
            if not check_proof(stmt, context):
                return False
        return True

    elif isinstance(node, Assume):
        if not node.body:
            return node.premise == node.conclusion
        else:
            for stmt in node.body:
                if not check_proof(stmt, context + [node.premise]):
                    return False
            return True

    elif isinstance(node, By):
        return True  # TODO: 推論規則の検証をここに追加

    else:
        raise ValueError(f"Unknown node type: {type(node)}")
