/**
 * FoxVC VS Code Extension Controller (extension.js)
 * Registers commands to run, build, format, and connect to foxvc lsp.
 */

const vscode = require('vscode');
const { spawn } = require('child_process');

function activate(context) {
    // 1. Run Current FoxVC Script
    const runDisposable = vscode.commands.registerCommand('foxvc.run', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active FoxVC document.');
            return;
        }
        const filePath = editor.document.fileName;
        const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('FoxVC Terminal');
        terminal.show();
        terminal.sendText(`foxvc run "${filePath}"`);
    });

    // 2. Build Native Executable
    const buildDisposable = vscode.commands.registerCommand('foxvc.build', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const filePath = editor.document.fileName;
        const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('FoxVC Terminal');
        terminal.show();
        terminal.sendText(`foxvc build "${filePath}"`);
    });

    // 3. Format Document (foxvc fmt)
    const formatDisposable = vscode.commands.registerCommand('foxvc.format', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const filePath = editor.document.fileName;
        const proc = spawn('foxvc', ['fmt', filePath, '-w']);
        proc.on('close', (code) => {
            if (code === 0) {
                vscode.window.showInformationMessage('FoxVC: Document formatted cleanly.');
            }
        });
    });

    // 4. Run Test Suite (foxvc test)
    const testDisposable = vscode.commands.registerCommand('foxvc.test', function () {
        const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('FoxVC Tests');
        terminal.show();
        terminal.sendText('foxvc test');
    });

    context.subscriptions.push(runDisposable, buildDisposable, formatDisposable, testDisposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
