import * as vscode from "vscode";
import * as path from "path";
import { LanguageClient, ServerOptions, LanguageClientOptions } from "vscode-languageclient/node";

interface PreviewResponse {
    html: string;
}

let client: LanguageClient;
let mediaPath: vscode.Uri;
let panel: vscode.WebviewPanel | undefined;

export function activate(context: vscode.ExtensionContext) {
    const pythonPath = context.asAbsolutePath(path.join(".venv", "Scripts", "python.exe"));

    const serverModule = context.asAbsolutePath(path.join("proofsrc", "lsp_server.py"));

    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: [serverModule],
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: "file", language: "proof" }],
    };

    client = new LanguageClient("proofLSP", "Proof Language Server", serverOptions, clientOptions);

    console.log("Proof LSP Client starting...");
    client.start();

    mediaPath = vscode.Uri.joinPath(context.extensionUri, "html");

    const previewCommand = vscode.commands.registerCommand("dsl-proof.showPreview", () => {
        if (vscode.window.activeTextEditor) {
            if (!panel) {
                panel = vscode.window.createWebviewPanel(
                    "proofPreview",
                    "Proof Preview",
                    vscode.ViewColumn.Two,
                    {
                        enableScripts: true,
                        localResourceRoots: [mediaPath]
                    }
                );
                panel.onDidDispose(() => { panel = undefined; }, null, context.subscriptions);
            }
            updateWebView(vscode.window.activeTextEditor.document);
        }
    });

    context.subscriptions.push(previewCommand);

    vscode.workspace.onDidSaveTextDocument(document => {
        if (panel && document === vscode.window.activeTextEditor?.document) {
            updateWebView(document);
        }
    });

    vscode.window.onDidChangeTextEditorSelection(async (e) => {
        if (panel) {
            panel.webview.html = await client.sendRequest<string>("proof/getProofInfo", {
                uri: e.textEditor.document.uri.toString(),
                position: e.textEditor.selection.active
            });
        }
    });
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) { return undefined; }
    return client.stop();
}

async function updateWebView(document: vscode.TextDocument) {
    if (!panel) { return; }

    const response = await client.sendRequest<PreviewResponse>("proof/getPreviewHtml", {
        uri: document.uri.toString()
    });

    const scriptUri = panel.webview.asWebviewUri(vscode.Uri.joinPath(mediaPath, "script.js"));
    const cssUri = panel.webview.asWebviewUri(vscode.Uri.joinPath(mediaPath, "style_mathjax.css"));
    let html = response.html;
    html = html.replace("script.js", scriptUri.toString());
    html = html.replace("style_mathjax.css", cssUri.toString());
    panel.webview.html = html;
}
