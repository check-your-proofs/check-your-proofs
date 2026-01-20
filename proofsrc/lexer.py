import re
from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: str
    file: str
    pos: int
    line: int
    column: int
    end_line: int
    end_column: int

    def info(self):
        return f"[{self.file}:{self.line}:{self.column}]"

KEYWORDS = {"theorem", "definition", "any", "assume", "conclude", "divide", "case", "some", "such", "deny", "contradict", "explode", "apply", "for", "lift", "primitive", "predicate", "arity", "axiom", "invoke", "expand", "constant", "by", "pad", "split", "connect", "existence", "uniqueness", "autoexpand", "function", "equality", "reflection", "replacement", "substitute", "characterize", "show", "tex", "as", "template", "leftward", "rightward", "include", "assert", "fold", "membership"}

SYMBOLS = {
    "{": "LBRACE",
    "}": "RBRACE",
    ":": "COLON",
    ",": "COMMA",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "|": "SLASH",
    ".": "DOT",
    "_": "UNDERSCORE",
}

def lex(path: str) -> tuple[list[Token], str]:
    f = open(path)
    src = f.read()
    f.close()
    tokens: list[Token] = []
    i = 0
    line = 1
    line_start_pos = 0
    while i < len(src):
        column = i - line_start_pos + 1
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            line_start_pos = i
            continue
        if c.isspace():
            i += 1
            continue
        if src[i:i+2] == "/*":
            start_i = i
            start_line = line
            start_column = column
            i += 2
            while i < len(src) and src[i:i+2] != "*/":
                if src[i] == "\n":
                    line += 1
                    line_start_pos = i + 1
                i += 1
            if i >= len(src):
                tokens.append(Token("UNTERMINATED_COMMENT", src[start_i:], path, start_i, start_line, start_column, line, i - line_start_pos + 1))
                break
            i += 2
            continue
        if c in SYMBOLS:
            tokens.append(Token(SYMBOLS[c], c, path, i, line, column, line, column + 1))
            i += 1
        elif src[i:].startswith("\\lambda^P"):
            length = len("\\lambda^P")
            tokens.append(Token("LAMBDA_PRED", "\\lambda^P", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\lambda^F"):
            length = len("\\lambda^F")
            tokens.append(Token("LAMBDA_FUN", "\\lambda^F", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\forall^P"):
            length = len("\\forall^P")
            tokens.append(Token("FORALL_PRED_TMPL", "\\forall^P", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\forall^F"):
            length = len("\\forall^F")
            tokens.append(Token("FORALL_FUN_TMPL", "\\forall^F", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\forall"):
            length = len("\\forall")
            tokens.append(Token("FORALL", "\\forall", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\exists!"):
            length = len("\\exists!")
            tokens.append(Token("EXISTS_UNIQ", "\\exists!", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\exists"):
            length = len("\\exists")
            tokens.append(Token("EXISTS", "\\exists", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\wedge"):
            length = len("\\wedge")
            tokens.append(Token("AND", "\\wedge", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\vee"):
            length = len("\\vee")
            tokens.append(Token("OR", "\\vee", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\neg"):
            length = len("\\neg")
            tokens.append(Token("NOT", "\\neg", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\to"):
            length = len("\\to")
            tokens.append(Token("IMPLIES", "\\to", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\leftrightarrow"):
            length = len("\\leftrightarrow")
            tokens.append(Token("IFF", "\\leftrightarrow", path, i, line, column, line, column + length))
            i += length
        elif src[i:].startswith("\\bot"):
            length = len("\\bot")
            tokens.append(Token("BOT", "\\bot", path, i, line, column, line, column + length))
            i += length
        elif src[i] == '"':
            start_i = i
            i += 1
            content_start_i = i
            while i < len(src) and src[i] != "\n" and src[i] != '"':
                i += 1
            content_end_i = i
            if i >= len(src) or src[i] == "\n":
                tokens.append(Token("UNTERMINATED_STRING", src[content_start_i:content_end_i], path, start_i, line, column, line, column + (i - start_i)))
            else:
                i += 1
                tokens.append(Token("STRING", src[content_start_i:content_end_i], path, start_i, line, column, line, column + (i - start_i)))
        else:
            m = re.match(r"(\\[A-Za-z][A-Za-z0-9_]*)|([A-Za-z_][A-Za-z0-9_]*'*)", src[i:])
            if m:
                text = m.group(0)
                if text in KEYWORDS:
                    tokens.append(Token(text.upper(), text, path, i, line, column, line, column + len(text)))
                else:
                    tokens.append(Token("IDENT", text, path, i, line, column, line, column + len(text)))
                i += len(text)
            else:
                m = re.match(r"\d+", src[i:])
                if m:
                    text = m.group(0)
                    tokens.append(Token("NUMBER", text, path, i, line, column, line, column + len(text)))
                    i += len(text)
                else:
                    error_token = Token("INVALID_CHARACTER", src[i], path, i, line, column, line, column + 1)
                    tokens.append(error_token)
                    i += 1
    column = len(src) - line_start_pos + 1
    tokens.append(Token("EOF", "", path, i, line, column, line, column))
    return tokens, src

if __name__ == "__main__":
    import sys
    path = sys.argv[1]

    import os
    import logging

    logger = logging.getLogger("proof")
    logger.setLevel(logging.DEBUG)

    # 標準出力用ハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # ファイル出力用ハンドラ
    file_handler = logging.FileHandler(os.path.join("logs", os.path.basename(path).replace(".proof", "_lexer.log")), mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 共通フォーマット
    formatter = logging.Formatter("[%(filename)s] %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # ハンドラ登録
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    tokens, _ = lex(path)
    for t in tokens:
        logger.debug(t)
