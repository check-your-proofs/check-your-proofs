from ast_types import Context, Term, Var, Con, Fun, Compound, Formula, Symbol, Not, And, Or, Implies, Iff, Forall, Exists, ExistsUniq, pretty_expr
from logic_utils import alpha_equiv

class EGraph:
    def __init__(self):
        self.parent: dict[Term, Term] = {}

    def find(self, x: Term) -> Term:
        if x not in self.parent:
            self.parent[x] = x
        elif self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: Term, y: Term):
        px = self.find(x)
        py = self.find(y)
        if px != py:
            p = px if str(px) < str(py) else py
            self.parent[py] = p
            self.parent[px] = p

    def show_parents(self):
        print("EGraph parent mapping:")
        for child, parent in self.parent.items():
            print(f"{pretty_expr(child)} -> {pretty_expr(parent)}")

    def show_tree(self):
        tree: dict[Term, list[Term]] = {}
        for x in self.parent:
            p = self.parent[x]
            if p not in tree:
                tree[p] = []
            if x != p:
                tree[p].append(x)
        print("EGraph tree view:")
        for p in tree:
            if self.parent[p] == p:
                print(pretty_expr(p))
                childs = tree.get(p, [])
                for i, child in enumerate(childs):
                    prefix = "└─" if i == len(childs) - 1 else "├─"
                    print(prefix + pretty_expr(child))

def recurse_term(g: EGraph, t: Term) -> Term:
    t = g.find(t)
    if isinstance(t, (Con, Var)):
        return t
    elif isinstance(t, Compound):
        return Compound(t.fun, tuple(recurse_term(g, arg) for arg in t.args))
    else:
        raise Exception(f"Unexpected term: {t}")

def recurse_formula(g: EGraph, f: Formula) -> Formula:
    if isinstance(f, Symbol):
        return Symbol(f.name, [recurse_term(g, arg) for arg in f.args])
    elif isinstance(f, (Not)):
        return Not(recurse_formula(g, f))
    elif isinstance(f, (And, Or, Implies, Iff)):
        return type(f)(recurse_formula(g, f))
    elif isinstance(f, (Forall, Exists, ExistsUniq)):
        return type(f)(f.var, recurse_formula(f.body))
    else:
        raise Exception(f"Unexpected formula: {f}")

def equal_norm(f1: Formula, f2: Formula, context: Context, show: bool = False):
    g = EGraph()
    for f in context.formulas:
        if isinstance(f, Symbol) and f.name == context.equality.equal.name:
            g.union(f.args[0], f.args[1])

    f1_norm = recurse_formula(g, f1)
    f2_norm = recurse_formula(g, f2)

    if show:
        g.show_parents()
        print()
        g.show_tree()
        print()

    return f1_norm, f2_norm

if __name__ == "__main__":
    x = Var("x")
    y = Var("y")
    z = Var("z")
    w = Var("w")
    v = Var("v")
    pair = Fun("pair")
    pair_yy = Compound(pair, (y, y))
    pair_xy = Compound(pair, (x, y))
    pair_zz = Compound(pair, (z, z))
    pair_zw = Compound(pair, (z, w))

    from ast_types import Equality, DefPre
    formulas = [Symbol("equal", [pair_yy, pair_zz]),
                Symbol("equal", [x, y]),
                Symbol("equal", [z, w]),
                Symbol("equal", [w, v])]
    equality = Equality(DefPre("equal", None, None, False), None, None)
    context = Context(formulas, False, {}, {}, {}, {}, {}, {}, {}, equality)

    f1 = Symbol("in", [z, pair_xy])
    f2 = Symbol("in", [z, pair_zw])
    f1_norm, f2_norm = equal_norm(f1, f2, context, True)
    print(f"f1: {pretty_expr(f1)}")
    print(f"f2: {pretty_expr(f2)}")
    print(f"f1_norm: {pretty_expr(f1_norm)}")
    print(f"f2_norm: {pretty_expr(f2_norm)}")
    print(f"alpha_equiv(f1_norm, f2_norm): {alpha_equiv(f1_norm, f2_norm)}")
