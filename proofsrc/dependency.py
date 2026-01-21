from lexer import Token, lex
from token_stream import TokenStream
import os
from lsprotocol import types as lsp
from pygls import uris

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lsp_server import ProofLanguageServer

def get_content(target_path: str, ls: "ProofLanguageServer | None" = None) -> str:
    if ls is None:
        f = open(target_path)
        src = f.read()
        f.close()
        return src
    else:
        for uri, doc in ls.workspace.text_documents.items():
            path = uris.to_fs_path(uri)
            if path is None:
                continue
            if path == target_path:
                return doc.source
        f = open(target_path)
        src = f.read()
        f.close()
        return src

class DependencyResolver:
    def __init__(self):
        self.resolved_files: list[str] = []
        self.tokens_cache: dict[str, list[Token]] = {}
        self.source_cache: dict[str, str] = {}
        self.visiting_files: set[str] = set()
        self.diagnostics: dict[str, list[lsp.Diagnostic]] = {}

    def add_lsp_error(self, token: Token, message: str):
        uri = uris.from_fs_path(token.file)
        if uri is None:
            return
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=token.line - 1, character=token.column - 1),
                end=lsp.Position(line=token.end_line - 1, character=token.end_column - 1)
            ),
            message=message,
            source="DependencySolver",
            severity=lsp.DiagnosticSeverity.Error
        )
        if uri not in self.diagnostics:
            self.diagnostics[uri] = []
        self.diagnostics[uri].append(diag)

    def resolve(self, path: str, ls: "ProofLanguageServer | None" = None):
        if path in self.resolved_files:
            # print(f"Skipping {path}")
            return
        self.visiting_files.add(path)
        # print(f"Visiting {path}")
        src = get_content(path, ls)
        tokens, _ = lex(path, src)
        self.tokens_cache[path] = tokens
        self.source_cache[path] = src
        stream = TokenStream(tokens)
        while True:
            token = stream.peek()
            if token.type == "INCLUDE":
                stream.consume("INCLUDE")
                token = stream.peek()
                if token.type == "STRING":
                    token = stream.consume("STRING")
                    new_path = os.path.join(os.path.dirname(path), token.value)
                    if not os.path.exists(new_path):
                        self.add_lsp_error(token, f"File not found: {new_path}")
                    elif new_path in self.visiting_files:
                        self.add_lsp_error(token, f"Cyclic dependency: {new_path}")
                    else:
                        self.resolve(new_path)
            elif token.type == "EOF":
                break
            else:
                stream.consume(token.type)
        self.visiting_files.remove(path)
        self.resolved_files.append(path)
        # print(f"Resolved {path}")

    def get_result(self) -> tuple[list[str], dict[str, list[Token]]]:
        return self.resolved_files, self.tokens_cache

if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    resolver = DependencyResolver()
    resolver.resolve(path)
    resolved_files, tokens_cache = resolver.get_result()
    for file in resolved_files:
        print(f"file: {file}, length of tokens: {len(tokens_cache[file])}")
