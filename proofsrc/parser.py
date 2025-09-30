from dataclasses import dataclass
from typing import List, Union
from lexer import Token, lex

import logging
logger = logging.getLogger(__name__)

# === DSL ノード定義 ===
@dataclass
class Atom:
    type: str
    name: str
    arity: int

@dataclass
class Theorem:
    name: str
    conclusion: object
    proof: list

@dataclass
class Check:
    conclusion: object   # Expr AST

@dataclass
class Assume:
    premise: object      # Expr AST
    conclusion: object   # Expr AST
    body: list

@dataclass
class Any:
    vars: List[str]
    conclusion: object
    body: list

@dataclass
class Divide:
    fact: object
    conclusion: object
    cases: list

@dataclass
class Case:
    premise: object
    conclusion: object
    body: list

@dataclass
class Some:
    vars: List[str]
    premise: object
    conclusion: object
    body: list

@dataclass
class Deny:
    premise: object
    body: list

@dataclass
class Contradict:
    contradiction: object

@dataclass
class Explode:
    conclusion: object

@dataclass
class Apply:
    fact: object
    env: dict
    premise: object
    conclusion: object

@dataclass
class Lift:
    fact: object
    env: dict
    conclusion: object

@dataclass
class Definition:
    name: str
    body: str  # TODO: 式パーサーに統合可能

@dataclass
class Symbol:
    name: str
    args: list[str]

@dataclass
class Forall:
    var: str
    body: object

@dataclass
class Exists:
    var: str
    body: object

@dataclass
class Implies:
    left: object
    right: object

@dataclass
class And:
    left: object
    right: object

@dataclass
class Or:
    left: object
    right: object

@dataclass
class Not:
    body: object

@dataclass
class Iff:
    left: object
    right: object

@dataclass
class Bottom:
    pass

# === パーサー本体 ===
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type=None):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected EOF")
        if expected_type and tok.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {tok.type}")
        self.pos += 1
        return tok

    def parse_file(self):
        self.declared_atoms = {}  # name -> Atom
        ast = []
        while self.peek():
            tok = self.peek()
            if tok.type == "ATOM":
                ast.append(self.parse_atom())
            elif tok.type == "THEOREM":
                ast.append(self.parse_theorem())
            elif tok.type == "DEFINITION":
                ast.append(self.parse_definition())
            else:
                raise SyntaxError(f"Unexpected token {tok}")
        return ast

    def parse_atom(self):
        self.consume("ATOM")
        tok = self.peek()
        if tok.type == "PREDICATE":
            self.consume(tok.type)
            name = self.consume("IDENT").value
            self.consume("ARITY")
            arity = int(self.consume("NUMBER").value)
            atom = Atom(type=tok.type, name=name, arity=arity)
            self.declared_atoms[name] = atom
            return atom
        else:
            raise SyntaxError(f"Unexpected token {tok}")

    def parse_theorem(self):
        self.consume("THEOREM")
        name = self.consume("IDENT").value
        conclusion = self.parse_expr()
        self.consume("LBRACE")
        proof = self.parse_block()
        self.consume("RBRACE")
        return Theorem(name=name, conclusion=conclusion, proof=proof)

    def parse_check(self):
        self.consume("CHECK")
        # conclusion 部分の式を読む
        conclusion = self.parse_expr()
        return Check(conclusion=conclusion)

    def parse_block(self):
        body = []
        while True:
            tok = self.peek()
            if not tok or tok.type == "RBRACE":
                break
            if tok.type == "ANY":
                body.append(self.parse_any())
            elif tok.type == "ASSUME":
                body.append(self.parse_assume())
            elif tok.type == "DIVIDE":
                body.append(self.parse_divide())
            elif tok.type == "CHECK":
                body.append(self.parse_check())
            elif tok.type == "SOME":
                body.append(self.parse_some())
            elif tok.type == "DENY":
                body.append(self.parse_deny())
            elif tok.type == "CONTRADICT":
                body.append(self.parse_contradict())
            elif tok.type == "EXPLODE":
                body.append(self.parse_explode())
            elif tok.type == "APPLY":
                body.append(self.parse_apply())
            elif tok.type == "LIFT":
                body.append(self.parse_lift())
            else:
                raise SyntaxError(f"Unexpected token in block: {tok}")
        return body

    def parse_any(self):
        self.consume("ANY")
        vars_ = []
        while True:
            tok = self.consume("IDENT")
            vars_.append(tok.value)
            if self.peek().type == "COMMA":
                self.consume("COMMA")
                continue
            break
        self.consume("CONCLUDE")
        conclusion = self.parse_expr()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return Any(vars=vars_, conclusion=conclusion, body=body)

    def parse_assume(self):
        self.consume("ASSUME")
        premise = self.parse_expr()
        self.consume("CONCLUDE")
        conclusion = self.parse_expr()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return Assume(premise=premise, conclusion=conclusion, body=body)
    
    def parse_divide(self):
        self.consume("DIVIDE")
        fact = self.parse_expr()
        self.consume("CONCLUDE")
        conclusion = self.parse_expr()
        cases = []
        while self.peek().type == "CASE":
            cases.append(self.parse_case(conclusion))
        if len(cases) < 2:
            raise SyntaxError("At least two cases are necessary")
        return Divide(fact=fact, conclusion=conclusion, cases=cases)
    
    def parse_case(self, conclusion):
        self.consume("CASE")
        premise = self.parse_expr()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return Case(premise=premise, conclusion=conclusion, body=body)
    
    def parse_some(self):
        self.consume("SOME")
        vars_ = []
        while True:
            tok = self.consume("IDENT")
            vars_.append(tok.value)
            if self.peek().type == "COMMA":
                self.consume("COMMA")
                continue
            break
        self.consume("SUCH")
        premise = self.parse_expr()
        self.consume("CONCLUDE")
        conclusion = self.parse_expr()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return Some(vars=vars_, premise=premise, conclusion=conclusion, body=body)
    
    def parse_deny(self):
        self.consume("DENY")
        premise = self.parse_expr()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return Deny(premise=premise, body=body)
    
    def parse_contradict(self):
        self.consume("CONTRADICT")
        contradiction = self.parse_expr()
        return Contradict(contradiction=contradiction)
    
    def parse_explode(self):
        self.consume("EXPLODE")
        conclusion = self.parse_expr()
        return Explode(conclusion=conclusion)
    
    def parse_apply(self):
        self.consume("APPLY")
        fact = self.parse_expr()
        if self.peek().type == "FOR":
            self.consume("FOR")
            env = {}
            while True:
                bound = self.consume("IDENT").value
                self.consume("COLON")
                free = self.consume("IDENT").value
                env[bound] = free
                if self.peek().type == "COMMA":
                    self.consume("COMMA")
                    continue
                break
        else:
            env = None
        if self.peek().type == "WITH":
            self.consume("WITH")
            premise = self.parse_expr()
        else:
            premise = None
        if env is None and premise is None:
            raise SyntaxError("APPLY needs FOR or WITH")
        self.consume("CONCLUDE")
        conclusion = self.parse_expr()
        return Apply(fact=fact, env=env, premise=premise, conclusion=conclusion)
    
    def parse_lift(self):
        self.consume("LIFT")
        fact = self.parse_expr()
        self.consume("FOR")
        env = {}
        while True:
            bound = self.consume("IDENT").value
            self.consume("COLON")
            free = self.consume("IDENT").value
            env[bound] = free
            if self.peek().type == "COMMA":
                self.consume("COMMA")
                continue
            break
        self.consume("CONCLUDE")
        conclusion = self.parse_expr()
        return Lift(fact=fact, env=env, conclusion=conclusion)

    def parse_definition(self):
        self.consume("DEFINITION")
        name = self.consume("IDENT").value
        self.consume("LBRACE")
        # とりあえず文字列で保持（後で expr_parser に流せるよう拡張）
        body_tok = []
        while self.peek() and self.peek().type != "RBRACE":
            body_tok.append(self.consume())
        self.consume("RBRACE")
        return Definition(name=name, body=" ".join(t.value for t in body_tok))

    def parse_primary(self):
        tok = self.peek()
        if tok.type == "IDENT":
            atom_name = self.consume("IDENT").value
            if atom_name not in self.declared_atoms:
                raise SyntaxError("atom is not found")
            self.consume("LPAREN")
            args = [self.consume("IDENT").value]
            while self.peek().type == "COMMA":
                self.consume("COMMA")
                args.append(self.consume("IDENT").value)
            if len(args) != self.declared_atoms[atom_name].arity:
                raise SyntaxError("arity is different")
            self.consume("RPAREN")
            return Symbol(atom_name, args)

        elif tok.type == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expr()
            self.consume("RPAREN")
            return expr
        
        elif tok.type == "NOT":
            self.consume("NOT")
            self.consume("LPAREN")
            body = self.parse_recursion()
            self.consume("RPAREN")
            return Not(body)

        elif tok.type == "FORALL":
            vars = []
            while self.peek().type == "FORALL":
                self.consume("FORALL")
                vars.append(self.consume("IDENT").value)
            self.consume("LPAREN")
            body = self.parse_recursion()
            self.consume("RPAREN")
            for var in reversed(vars):
                body = Forall(var, body)
            return body

        elif tok.type == "EXISTS":
            vars = []
            while self.peek().type == "EXISTS":
                self.consume("EXISTS")
                vars.append(self.consume("IDENT").value)
            self.consume("LPAREN")
            body = self.parse_recursion()
            self.consume("RPAREN")
            for var in reversed(vars):
                body = Exists(var, body)
            return body

        else:
            raise SyntaxError(f"Unexpected token: {tok}")

    def parse_expr(self):
        if self.peek().type == "BOT":
            self.consume("BOT")
            return Bottom()
        else:
            return self.parse_recursion()

    def parse_recursion(self):
        return self.parse_implies()

    def parse_implies(self):
        left = self.parse_and()
        while self.peek().type in ("IMPLIES", "IFF"):
            op = self.peek().type
            self.consume(op)
            right = self.parse_and()
            if op == "IMPLIES":
                left = Implies(left, right)
            elif op == "IFF":
                left = Iff(left, right)
        return left

    def parse_and(self):
        left = self.parse_primary()
        while self.peek().type in ("AND", "OR"):
            op = self.peek().type
            self.consume(op)
            right = self.parse_primary()
            if op == "AND":
                left = And(left, right)
            elif op == "OR":
                left = Or(left, right)
        return left

# === ヘルパー関数 ===
def parse_file_from_source(src: str):
    tokens = lex(src)
    parser = Parser(tokens)
    return parser.parse_file()

def pretty(node, indent=0):
    sp = "  " * indent  # インデント幅2スペース
    if isinstance(node, Atom):
        logger.debug(f"{sp}[Atom] type: {node.type}")
        logger.debug(f"{sp}       name: {node.name}")
        logger.debug(f"{sp}       arity: {node.arity}")

    elif isinstance(node, Theorem):
        logger.debug(f"{sp}[Theorem] name: {node.name}")
        logger.debug(f"{sp}          conclusion: {pretty_expr(node.conclusion)}")
        for stmt in node.proof:
            pretty(stmt, indent + 1)

    elif isinstance(node, Check):
        logger.debug(f"{sp}[Check] {pretty_expr(node.conclusion)}")

    elif isinstance(node, Any):
        logger.debug(f"{sp}[Any] vars: {', '.join(node.vars)}")
        logger.debug(f"{sp}      conclusion: {pretty_expr(node.conclusion)}")
        for stmt in node.body:
            pretty(stmt, indent + 1)

    elif isinstance(node, Assume):
        logger.debug(f"{sp}[Assume] premise: {pretty_expr(node.premise)}")
        logger.debug(f"{sp}         conclusion: {pretty_expr(node.conclusion)}")
        for stmt in node.body:
            pretty(stmt, indent + 1)
    
    elif isinstance(node, Divide):
        logger.debug(f"{sp}[Divide] fact: {pretty_expr(node.fact)}")
        logger.debug(f"{sp}         conclusion: {pretty_expr(node.conclusion)}")
        for stmt in node.cases:
            pretty(stmt, indent + 1)

    elif isinstance(node, Case):
        logger.debug(f"{sp}[Case] case: {pretty_expr(node.premise)}")
        logger.debug(f"{sp}       conclusion: {pretty_expr(node.conclusion)}")
        for stmt in node.body:
            pretty(stmt, indent + 1)
    
    elif isinstance(node, Some):
        logger.debug(f"{sp}[Some] vars: {','.join(node.vars)}")
        logger.debug(f"{sp}       premise: {pretty_expr(node.premise)}")
        logger.debug(f"{sp}       conclusion: {pretty_expr(node.conclusion)}")
        for stmt in node.body:
            pretty(stmt, indent + 1)
    
    elif isinstance(node, Deny):
        logger.debug(f"{sp}[Deny] premise: {pretty_expr(node.premise)}")
        for stmt in node.body:
            pretty(stmt, indent + 1)
    
    elif isinstance(node, Contradict):
        logger.debug(f"{sp}[Contradict] contradiction: {pretty_expr(node.contradiction)}")

    elif isinstance(node, Explode):
        logger.debug(f"{sp}[Explode] conclusion: {pretty_expr(node.conclusion)}")

    elif isinstance(node, Apply):
        logger.debug(f"{sp}[Apply] fact: {pretty_expr(node.conclusion)}")
        if node.env is not None:
            logger.debug(f"{sp}        env: {node.env}")
        if node.premise is not None:
            logger.debug(f"{sp}        premise: {pretty_expr(node.premise)}")
        logger.debug(f"{sp}        conclusion: {pretty_expr(node.conclusion)}")
    
    elif isinstance(node, Lift):
        logger.debug(f"{sp}[Lift] fact: {pretty_expr(node.fact)}")
        logger.debug(f"{sp}       env: {node.env}")
        logger.debug(f"{sp}       conclusion: {pretty_expr(node.conclusion)}")

    elif isinstance(node, Definition):
        logger.debug(f"{sp}Definition {node.name}: {node.body}")

    else:
        raise TypeError(f"Unsupported node type: {type(node)}")

def pretty_expr(expr):
    if isinstance(expr, Symbol):
        return f"{expr.name}({",".join(expr.args)})"
    if isinstance(expr, Implies):
        return f"{pretty_expr(expr.left)} \\to {pretty_expr(expr.right)}"
    if isinstance(expr, And):
        return f"{pretty_expr(expr.left)} \\wedge {pretty_expr(expr.right)}"
    if isinstance(expr, Or):
        return f"{pretty_expr(expr.left)} \\vee {pretty_expr(expr.right)}"
    if isinstance(expr, Not):
        return f"\\neg({pretty_expr(expr.body)})"
    if isinstance(expr, Forall):
        return f"\\forall {expr.var}({pretty_expr(expr.body)})"
    if isinstance(expr, Exists):
        return f"\\exists {expr.var}({pretty_expr(expr.body)})"
    if isinstance(expr, Bottom):
        return "\\bot"
    raise TypeError(f"Unsupported node type: {type(expr)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    import sys
    path = sys.argv[1]
    f = open(path)
    src = f.read()
    f.close()
    ast = parse_file_from_source(src)
    for node in ast:
        pretty(node)
