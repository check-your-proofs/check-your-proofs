from dataclasses import dataclass
from typing import List, Union

# ノード定義
@dataclass
class By:
    target: str
    definition: str
    using: List[str]

@dataclass
class Assume:
    premise: str
    conclusion: str
    body: List[Union['By', 'Any', 'Assume']]

@dataclass
class Any:
    vars: List[str]
    body: List[Union[By, Assume, 'Any']]

@dataclass
class Definition:
    name: str
    body: str

@dataclass
class Theorem:
    name: str
    statement: str
    proof: Any

# --- パース関数（暫定・前に作ったものを流用して拡張）

def parse_by(line: str) -> By:
    lhs, rest = line.split(" by ", 1)
    target = lhs.strip()
    definition, rest = rest.split(" using ", 1)
    definition = definition.strip()
    rest = rest.strip()
    if rest.startswith("(") and rest.endswith(")"):
        rest = rest[1:-1]
    using = [u.strip() for u in rest.split(",")]
    return By(target=target, definition=definition, using=using)

def parse_block(lines, i=0):
    """再帰的にany/assumeブロックを読む"""
    body = []
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("any "):
            vars_part, _ = line[4:].split("{", 1)
            vars_ = [v.strip() for v in vars_part.split(",")]
            sub_body, i = parse_block(lines, i+1)
            body.append(Any(vars=vars_, body=sub_body))
        elif line.startswith("assume "):
            inside = line[7:]
            premise, rest = inside.split("conclude", 1)
            conclusion, _ = rest.split("{", 1)
            premise = premise.strip()
            conclusion = conclusion.strip()
            sub_body, i = parse_block(lines, i+1)
            body.append(Assume(premise=premise, conclusion=conclusion, body=sub_body))
        elif " by " in line:
            body.append(parse_by(line))
            i += 1
        elif line.startswith("}"):
            return body, i+1
        else:
            i += 1
    return body, i

def parse_file(path: str):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("\n\n")
    ast = []

    for block in blocks:
        block = block.strip()
        if block.startswith("definition"):
            header, body = block.split("{", 1)
            name = header.split()[1].strip()
            body = body.rsplit("}", 1)[0].strip()
            ast.append(Definition(name=name, body=body))
        elif block.startswith("theorem"):
            header, body = block.split("{", 1)

            # theorem の名前を取る
            name = header.split()[1].split("(")[0].strip()

            # theorem の本文部分
            body = body.rsplit("}", 1)[0].strip()
            lines = [l.strip() for l in body.splitlines() if l.strip()]

            # 最初の行が statement
            statement = lines[0]

            # proof { ... } の部分を抽出
            if lines[1].startswith("proof"):
                proof_lines = lines[2:-1]  # proof { と最後の } を除外
                proof_body, _ = parse_block(proof_lines)
                proof = proof_body[0]
            else:
                proof = None  # proof がまだ書かれてない場合にも対応

            ast.append(Theorem(name=name, statement=statement, proof=proof))
    return ast
