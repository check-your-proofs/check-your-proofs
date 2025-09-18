const vscode = require('vscode');

let decorationsEnabled = true;
let decorationTypes = {};

function updateDecorations(editor) {
    if (!editor) return;

    // 既存デコレーションをクリア
    Object.values(decorationTypes).forEach(type => type.dispose());
    decorationTypes = {};

    if (!decorationsEnabled) return;

    const symbols = {
        '\\\\wedge': '∧',
        '\\\\to': '→',
        '\\\\leftrightarrow': '↔',
        '\\\\forall': '∀',
        '\\\\in': '∈',
        '\\\\subset': '⊂'
    };

    const text = editor.document.getText();

    for (const [pattern, symbol] of Object.entries(symbols)) {
        const regex = new RegExp(pattern, 'g');
        const ranges = [];

        let match;
        while ((match = regex.exec(text)) !== null) {
            ranges.push(new vscode.Range(
                editor.document.positionAt(match.index),
                editor.document.positionAt(match.index + match[0].length)
            ));
        }

        const decorationType = vscode.window.createTextEditorDecorationType({
            before: {
                contentText: symbol,
            },
            fontFamily: 'Cambria Math',
            // 元テキストをゼロ幅で隠す
            rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed,
            opacity: '0',
            letterSpacing: '-999em' // 強制的に詰める
        });

        editor.setDecorations(decorationType, ranges);
        decorationTypes[pattern] = decorationType;
    }
}

function activate(context) {
    let disposable = vscode.commands.registerCommand('dsl-proof-syntax.toggleSymbols', () => {
        decorationsEnabled = !decorationsEnabled;
        updateDecorations(vscode.window.activeTextEditor);
    });

    context.subscriptions.push(disposable);

    vscode.window.onDidChangeActiveTextEditor(editor => {
        updateDecorations(editor);
    }, null, context.subscriptions);

    vscode.workspace.onDidChangeTextDocument(event => {
        if (vscode.window.activeTextEditor && event.document === vscode.window.activeTextEditor.document) {
            updateDecorations(vscode.window.activeTextEditor);
        }
    }, null, context.subscriptions);
}

function deactivate() {}

module.exports = { activate, deactivate };
