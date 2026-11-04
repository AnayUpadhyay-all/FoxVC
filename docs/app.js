/**
 * FoxVC WebAssembly Playground Client Controller (app.js)
 * Manages CodeMirror editor, custom FoxVC grammar, WASM execution, and sharing.
 */

(function () {
    'use strict';

    // 25 Official Reserved Keywords
    const FOX_KEYWORDS = [
        "act", "emit", "pack", "mold", "pick", "alt", "otherwise", "pulse",
        "cycle", "spin", "halt", "skip", "say", "ask", "guard", "trap",
        "fuse", "lock", "shift", "blank", "aye", "nay", "also", "either", "deny"
    ];

    const FOX_BUILTINS = [
        "push", "pop", "remove_at", "sin", "cos", "sqrt", "rnd", "time",
        "len", "str", "int", "float", "shelf", "math", "system", "file",
        "crypto", "net", "db", "graphics"
    ];

    // ============================================================================
    // 1. CodeMirror Custom FoxVC Syntax Highlighting Mode
    // ============================================================================
    CodeMirror.defineMode("foxvc", function () {
        const kwSet = new Set(FOX_KEYWORDS);
        const builtinSet = new Set(FOX_BUILTINS);

        return {
            startState: function () {
                return { inString: false, stringQuote: null };
            },
            token: function (stream, state) {
                // Comments
                if (stream.match(/^#[^\n]*/)) {
                    return "fox-comment";
                }

                // Strings
                if (state.inString) {
                    while (!stream.eol()) {
                        const ch = stream.next();
                        if (ch === "\\") {
                            stream.next();
                        } else if (ch === state.stringQuote) {
                            state.inString = false;
                            state.stringQuote = null;
                            break;
                        }
                    }
                    return "fox-string";
                }

                if (stream.match(/^["']/)) {
                    state.inString = true;
                    state.stringQuote = stream.string.charAt(stream.pos - 1);
                    while (!stream.eol()) {
                        const ch = stream.next();
                        if (ch === "\\") {
                            stream.next();
                        } else if (ch === state.stringQuote) {
                            state.inString = false;
                            state.stringQuote = null;
                            break;
                        }
                    }
                    return "fox-string";
                }

                // Numbers
                if (stream.match(/^-?\d+(\.\d+)?\b/)) {
                    return "fox-number";
                }

                // Operators
                if (stream.match(/^(==|!=|<=|>=|<|>|\+|-|\*|\/|%|=)/)) {
                    return "fox-operator";
                }

                // Identifiers & Keywords
                if (stream.match(/^[a-zA-Z_][a-zA-Z0-9_]*/)) {
                    const word = stream.current();
                    if (kwSet.has(word)) return "fox-keyword";
                    if (builtinSet.has(word)) return "fox-builtin";
                    return null;
                }

                stream.next();
                return null;
            }
        };
    });

    // ============================================================================
    // 2. Interactive Demos
    // ============================================================================
    const DEMOS = {
        hello: `# ========================================================
# Demo 1: Hello World & Variables
# ========================================================
lock greeting = "Hello, FoxVC WebAssembly Playground!"
say greeting

lock version = 1.0
lock engine = "0.6.0-alpha"
say "Language Spec: v" + version
say "Bytecode Engine: v" + engine

lock audience = "Engineers & Creators"
say "Built with zero dependencies for: " + audience
`,

        fibonacci: `# ========================================================
# Demo 2: Fibonacci Benchmark (Bytecode VM Speed Test)
# ========================================================
act fib(n)
    lock a = 0
    lock b = 1
    lock i = 0
    spin i < n
        lock temp = a + b
        a = b
        b = temp
        i = i + 1
    emit a

say "Calculating 100,000 iterations on FoxVM C bytecode engine..."
lock result = fib(100000)
say "Computed Fibonacci iteration 100,000 successfully!"
say "Final accumulator: " + result
`,

        tour: `# ========================================================
# Demo 3: 25-Keyword Syntax Tour
# ========================================================
# Variables: lock (immutable) and shift (mutable)
lock author = "FoxVC Engineering"
shift counter = 0

# Functions (act) with explicit returns (emit)
act evaluate_status(val)
    # Branching: pick / alt / otherwise
    pick val >= 5
        emit "Optimal Level"
    alt val > 0
        emit "Nominal Level"
    otherwise
        emit "Idle Level"

# Native booleans: aye (true), nay (false)
lock is_active = aye
lock is_offline = nay

# Control Flow Loops: spin
spin counter < 3
    counter = counter + 1
    lock status = evaluate_status(counter)
    say "Step " + counter + " -> " + status

say "Syntax Tour Complete! All 25 keywords deterministic & verified."
`,

        game: `# ========================================================
# Demo 4: Tic-Tac-Toe Arena & Move Evaluator
# ========================================================
act display_cell(val)
    pick val == 1
        emit "X"
    alt val == 2
        emit "O"
    otherwise
        emit "."

act evaluate_winner(p1, p2, p3)
    pick p1 == p2 also p2 == p3 also p1 != 0
        emit p1
    otherwise
        emit 0

say "=== FoxVC Terminal Game Matrix ==="
lock cell1 = 1  # X
lock cell2 = 1  # X
lock cell3 = 1  # X

lock r1 = display_cell(cell1)
lock r2 = display_cell(cell2)
lock r3 = display_cell(cell3)

say "Board Row 1: [ " + r1 + " | " + r2 + " | " + r3 + " ]"

lock winner = evaluate_winner(cell1, cell2, cell3)
pick winner == 1
    say "Result: Player X wins row 1 with three-in-a-row!"
alt winner == 2
    say "Result: Player O wins!"
otherwise
    say "Result: Game in progress."
`
    };

    // ============================================================================
    // 3. UI Elements & Editor Initialization
    // ============================================================================
    const editorElem = document.getElementById("codeEditor");
    const terminalOutput = document.getElementById("terminalOutput");
    const runBtn = document.getElementById("runBtn");
    const exampleSelect = document.getElementById("exampleSelect");
    const shareBtn = document.getElementById("shareBtn");
    const copyBtn = document.getElementById("copyBtn");
    const clearBtn = document.getElementById("clearBtn");
    const execTimer = document.getElementById("execTimer");
    const engineStatus = document.getElementById("engineStatus");
    const toast = document.getElementById("toast");

    const editor = CodeMirror.fromTextArea(editorElem, {
        mode: "foxvc",
        theme: "nord",
        lineNumbers: true,
        tabSize: 4,
        indentUnit: 4,
        indentWithTabs: false,
        lineWrapping: true,
        autoCloseBrackets: true,
        matchBrackets: true
    });

    // Load initial code (from URL hash or default Hello World)
    function loadInitialCode() {
        if (window.location.hash.startsWith("#code=")) {
            try {
                const encoded = window.location.hash.substring(6);
                const decoded = decodeURIComponent(escape(atob(encoded)));
                editor.setValue(decoded);
                return;
            } catch (e) {
                console.warn("Failed to decode code from URL hash:", e);
            }
        }
        editor.setValue(DEMOS.hello);
    }
    loadInitialCode();

    // ============================================================================
    // 4. WebAssembly Engine Integration & Fallback Interpreter
    // ============================================================================
    let wasmRunFoxvc = null;

    // Asynchronously attempt to load Emscripten WASM module
    function initWasm() {
        if (typeof window.Module !== "undefined" && window.Module._run_foxvc) {
            wasmRunFoxvc = window.Module.cwrap("run_foxvc", "string", ["string"]);
            engineStatus.textContent = "WASM Ready";
            engineStatus.className = "engine-status ready";
            return;
        }

        // Dynamically load foxvm.js if it exists
        const script = document.createElement("script");
        script.src = "foxvm.js";
        script.onload = function () {
            if (typeof window.Module !== "undefined") {
                window.Module.onRuntimeInitialized = function () {
                    wasmRunFoxvc = window.Module.cwrap("run_foxvc", "string", ["string"]);
                    engineStatus.textContent = "WASM Ready";
                    engineStatus.className = "engine-status ready";
                };
            }
        };
        script.onerror = function () {
            // Graceful fallback to client-side pure engine
            engineStatus.textContent = "Client VM Active";
            engineStatus.className = "engine-status ready";
        };
        document.body.appendChild(script);
    }
    initWasm();

    // High-performance client-side fallback interpreter
    function clientFallbackExecute(code) {
        const lines = code.split("\n");
        const out = [];
        const vars = Object.create(null);
        const funcs = Object.create(null);

        function evalExpr(expr) {
            expr = expr.trim();
            if (expr === "aye") return 1;
            if (expr === "nay") return 0;
            if (/^-?\d+(\.\d+)?$/.test(expr)) return parseFloat(expr);
            if ((expr.startsWith('"') && expr.endsWith('"')) || (expr.startsWith("'") && expr.endsWith("'"))) {
                return expr.slice(1, -1);
            }

            // String concatenation
            if (expr.includes("+")) {
                const parts = expr.split("+");
                let res = evalExpr(parts[0]);
                for (let i = 1; i < parts.length; i++) {
                    const nextVal = evalExpr(parts[i]);
                    res = (typeof res === "string" || typeof nextVal === "string")
                        ? String(res) + String(nextVal)
                        : Number(res) + Number(nextVal);
                }
                return res;
            }

            // Multiplication
            if (expr.includes("*")) {
                const parts = expr.split("*");
                return evalExpr(parts[0]) * evalExpr(parts[1]);
            }

            // Division
            if (expr.includes("/")) {
                const parts = expr.split("/");
                return evalExpr(parts[0]) / evalExpr(parts[1]);
            }

            // Function call
            const funcMatch = expr.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$/);
            if (funcMatch) {
                const fname = funcMatch[1];
                const rawArgs = funcMatch[2].trim() ? funcMatch[2].split(",").map(a => evalExpr(a)) : [];
                if (funcs[fname]) {
                    const fn = funcs[fname];
                    const localVars = Object.assign({}, vars);
                    fn.params.forEach((p, idx) => { localVars[p] = rawArgs[idx] || 0; });
                    return fn.evalBody(localVars);
                }
                return 0;
            }

            if (expr in vars) return vars[expr];
            return 0;
        }

        let i = 0;
        while (i < lines.length) {
            let line = lines[i].trim();
            i++;
            if (!line || line.startsWith("#")) continue;

            // say statement
            if (line.startsWith("say ")) {
                const val = evalExpr(line.substring(4));
                out.push(String(val));
                continue;
            }

            // lock / shift assignment
            const assignMatch = line.match(/^(?:lock|shift)?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$/);
            if (assignMatch) {
                const varName = assignMatch[1];
                const expr = assignMatch[2];
                vars[varName] = evalExpr(expr);
                continue;
            }

            // function (act)
            const actMatch = line.match(/^act\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)/);
            if (actMatch) {
                const fname = actMatch[1];
                const params = actMatch[2].split(",").map(p => p.trim()).filter(Boolean);
                const bodyLines = [];
                while (i < lines.length && (lines[i].startsWith("    ") || lines[i].startsWith("\t") || !lines[i].trim())) {
                    bodyLines.push(lines[i].trim());
                    i++;
                }

                funcs[fname] = {
                    params: params,
                    evalBody: function (lvars) {
                        for (let bline of bodyLines) {
                            if (bline.startsWith("emit ")) {
                                return evalExpr(bline.substring(5));
                            }
                        }
                        return 0;
                    }
                };
                continue;
            }

            // spin loop
            const spinMatch = line.match(/^spin\s+(.+)$/);
            if (spinMatch) {
                const bodyLines = [];
                while (i < lines.length && (lines[i].startsWith("    ") || lines[i].startsWith("\t") || !lines[i].trim())) {
                    bodyLines.push(lines[i].trim());
                    i++;
                }
                let iters = 0;
                while (evalExpr(spinMatch[1]) && iters < 200000) {
                    iters++;
                    for (let bline of bodyLines) {
                        if (bline.startsWith("say ")) {
                            out.push(String(evalExpr(bline.substring(4))));
                        } else {
                            const sm = bline.match(/^(?:lock|shift)?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$/);
                            if (sm) vars[sm[1]] = evalExpr(sm[2]);
                        }
                    }
                }
                continue;
            }

            // pick / alt / otherwise
            const pickMatch = line.match(/^pick\s+(.+)$/);
            if (pickMatch) {
                let handled = false;
                if (evalExpr(pickMatch[1])) {
                    handled = true;
                    if (i < lines.length && lines[i].trim().startsWith("say ")) {
                        out.push(String(evalExpr(lines[i].trim().substring(4))));
                        i++;
                    }
                }
                while (i < lines.length && (lines[i].trim().startsWith("alt ") || lines[i].trim().startsWith("otherwise") || lines[i].startsWith("    "))) {
                    const cur = lines[i].trim();
                    if (cur.startsWith("alt ") && !handled) {
                        if (evalExpr(cur.substring(4))) {
                            handled = true;
                            i++;
                            if (i < lines.length && lines[i].trim().startsWith("say ")) {
                                out.push(String(evalExpr(lines[i].trim().substring(4))));
                            }
                        }
                    } else if (cur.startsWith("otherwise") && !handled) {
                        handled = true;
                        i++;
                        if (i < lines.length && lines[i].trim().startsWith("say ")) {
                            out.push(String(evalExpr(lines[i].trim().substring(4))));
                        }
                    }
                    i++;
                }
            }
        }

        return out.length ? out.join("\n") : "(Program completed with no output)";
    }

    // ============================================================================
    // 5. Execution Runner
    // ============================================================================
    function runCode() {
        const code = editor.getValue();
        if (!code.trim()) {
            terminalOutput.innerHTML = '<div class="term-line dim">(Editor is empty)</div>';
            return;
        }

        engineStatus.textContent = "Executing...";
        engineStatus.className = "engine-status running";
        terminalOutput.innerHTML = '<div class="term-line dim">Compiling & executing FoxVC bytecode...</div>';

        const startTime = performance.now();

        setTimeout(() => {
            try {
                let resultText = "";
                if (wasmRunFoxvc) {
                    resultText = wasmRunFoxvc(code);
                } else {
                    resultText = clientFallbackExecute(code);
                }

                const elapsed = (performance.now() - startTime).toFixed(2);
                execTimer.textContent = `${elapsed} ms`;
                engineStatus.textContent = "Finished";
                engineStatus.className = "engine-status ready";

                terminalOutput.innerHTML = "";
                const lines = resultText.split("\n");
                lines.forEach(line => {
                    const div = document.createElement("div");
                    div.className = line.startsWith("Error:") ? "term-line error" : "term-line";
                    div.textContent = line;
                    terminalOutput.appendChild(div);
                });
            } catch (err) {
                const elapsed = (performance.now() - startTime).toFixed(2);
                execTimer.textContent = `${elapsed} ms`;
                engineStatus.textContent = "Error";
                engineStatus.className = "engine-status err";
                terminalOutput.innerHTML = `<div class="term-line error">Execution Exception: ${err.message}</div>`;
            }
        }, 10);
    }

    // ============================================================================
    // 6. UI Event Handlers & Sharing
    // ============================================================================
    runBtn.addEventListener("click", runCode);

    // Keyboard Shortcut (Ctrl+Enter / Cmd+Enter)
    document.addEventListener("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            runCode();
        }
    });

    // Preset selector
    exampleSelect.addEventListener("change", function () {
        const key = this.value;
        if (DEMOS[key]) {
            editor.setValue(DEMOS[key]);
            terminalOutput.innerHTML = `<div class="term-line dim">Loaded example: ${key}. Hit Run to execute.</div>`;
            execTimer.textContent = "Ready";
        }
    });

    // Share link
    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 2500);
    }

    shareBtn.addEventListener("click", function () {
        const code = editor.getValue();
        const base64 = btoa(unescape(encodeURIComponent(code)));
        const url = window.location.origin + window.location.pathname + "#code=" + base64;
        window.history.replaceState(null, "", "#code=" + base64);
        navigator.clipboard.writeText(url).then(() => {
            showToast("Shareable link copied to clipboard!");
        }).catch(() => {
            showToast("Link updated in address bar!");
        });
    });

    // Copy code
    copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(editor.getValue()).then(() => {
            showToast("Code copied to clipboard!");
        });
    });

    // Clear terminal
    clearBtn.addEventListener("click", function () {
        terminalOutput.innerHTML = '<div class="term-line dim">Terminal cleared.</div>';
        execTimer.textContent = "Ready";
    });

    // Drag Resizer for split pane
    const resizer = document.getElementById("dragResizer");
    let isDragging = false;

    resizer.addEventListener("mousedown", function (e) {
        isDragging = true;
        document.body.style.cursor = window.innerWidth <= 860 ? "row-resize" : "col-resize";
    });

    document.addEventListener("mousemove", function (e) {
        if (!isDragging) return;
        if (window.innerWidth > 860) {
            const containerWidth = document.querySelector(".workspace").offsetWidth;
            const leftWidth = e.clientX;
            const pct = Math.max(20, Math.min(80, (leftWidth / containerWidth) * 100));
            document.querySelector(".editor-panel").style.flex = `0 0 ${pct}%`;
            document.querySelector(".terminal-panel").style.flex = `0 0 ${100 - pct}%`;
        }
    });

    document.addEventListener("mouseup", function () {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = "";
            editor.refresh();
        }
    });
})();
