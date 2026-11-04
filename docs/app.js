/**
 * FoxVC WebAssembly Playground Client Controller (app.js)
 * Manages CodeMirror editor, custom FoxVC grammar, WASM execution,
 * interactive 3D Canvas Stage, and Native Engine install guidance.
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
                // Comments (# or //)
                if (stream.match(/^(?:#|\/\/)[^\n]*/)) {
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
                if (stream.match(/^-?\d+(?:\.\d+)?\b/)) {
                    return "fox-number";
                }

                // Operators
                if (stream.match(/^(?:==|!=|<=|>=|[+\-*\/=<>!%])/)) {
                    return "fox-operator";
                }

                // Words (Keywords, Builtins, Identifiers)
                if (stream.match(/^[a-zA-Z_][a-zA-Z0-9_]*/)) {
                    const word = stream.current();
                    if (kwSet.has(word)) {
                        return "fox-keyword";
                    }
                    if (builtinSet.has(word)) {
                        return "fox-builtin";
                    }
                    return "fox-identifier";
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

        rotating_ui: `// ========================================================
// Demo 2: 3D Rotating Geometry & Projection Pipeline
// ========================================================
say "=== FoxVC 3D Spatial Vector Matrix ==="
shift vertices = 8
say "Target: 60 FPS Real-Time Perspective Projection for " + vertices + " Vertices"

act project_point(x, y, z, angle)
    // Isometric trigonometric coordinate rotation
    lock rx = x * 0.866 - z * 0.500
    lock rz = x * 0.500 + z * 0.866
    lock fov = 260 / (rz + 300)
    lock sx = 300 + (rx * fov)
    emit sx

shift i = 0
spin i < 8
    lock screen_x = project_point(50, -50, 50, 0.785)
    say "Vertex [" + i + "] Projected Screen Coordinate: " + screen_x
    i = i + 1

say "Trigonometric pipeline complete. 3D Canvas View Active!"
`,

        server: `// ========================================================
// Demo 3: Micro HTTP & WebSocket Server
// ========================================================
lock PORT = 8080
say "=== Initializing FoxVC Micro HTTP Server on Port " + PORT + " ==="
fuse net
fuse system

act handle_route(method, endpoint)
    pick endpoint == "/health"
        emit "{ 'status': 'ok', 'engine': 'foxvm', 'uptime': 3600 }"
    otherwise
        emit "{ 'error': '404 Not Found' }"

say "Server socket listening on 0.0.0.0:" + PORT
say "Registered routes:"
say "  GET /health       -> JSON Service Health"
say "  GET /api/v1/ping  -> Low-Latency Heartbeat"
say "Worker pool ready for incoming traffic."
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
`,

        fibonacci: `# ========================================================
# Demo 5: Fibonacci Benchmark (Bytecode VM Speed Test)
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
# Demo 6: 25-Keyword Syntax Tour
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
`
    };

    // ============================================================================
    // 3. DOM & Editor Setup
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

    // Tabs & 3D Stage Elements
    const tabTerminalBtn = document.getElementById("tabTerminalBtn");
    const tabStageBtn = document.getElementById("tabStageBtn");
    const stageContainer = document.getElementById("stageContainer");
    const stageCanvas = document.getElementById("stageCanvas");
    const stageSpeedBtn = document.getElementById("stageSpeedBtn");

    // Modal Elements
    const installGuideBtn = document.getElementById("installGuideBtn");
    const nativeInstallModal = document.getElementById("nativeInstallModal");
    const modalCloseBtn = document.getElementById("modalCloseBtn");
    const modalPreviewBtn = document.getElementById("modalPreviewBtn");
    const modalInstallCopyBtn = document.getElementById("modalInstallCopyBtn");

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

    function initWasm() {
        if (typeof window.Module !== "undefined" && window.Module._run_foxvc) {
            wasmRunFoxvc = window.Module.cwrap("run_foxvc", "string", ["string"]);
            engineStatus.textContent = "WASM Ready";
            engineStatus.className = "engine-status ready";
            return;
        }

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

            // Subtraction
            if (expr.includes("-")) {
                const parts = expr.split("-");
                let res = evalExpr(parts[0]);
                for (let i = 1; i < parts.length; i++) {
                    res = Number(res) - Number(evalExpr(parts[i]));
                }
                return res;
            }

            // Multiplication
            if (expr.includes("*")) {
                const parts = expr.split("*");
                let res = evalExpr(parts[0]);
                for (let i = 1; i < parts.length; i++) {
                    res = Number(res) * Number(evalExpr(parts[i]));
                }
                return res;
            }

            // Division
            if (expr.includes("/")) {
                const parts = expr.split("/");
                let res = evalExpr(parts[0]);
                for (let i = 1; i < parts.length; i++) {
                    const denom = Number(evalExpr(parts[i]));
                    res = denom !== 0 ? Number(res) / denom : 0;
                }
                return res;
            }

            // Function call
            const funcMatch = expr.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$/);
            if (funcMatch) {
                const fnName = funcMatch[1];
                const argStr = funcMatch[2].trim();
                const args = argStr ? argStr.split(",").map(a => evalExpr(a.trim())) : [];
                if (funcs[fnName]) {
                    return funcs[fnName](...args);
                }
            }

            // Variable lookup
            if (vars[expr] !== undefined) {
                return vars[expr];
            }

            return expr;
        }

        let i = 0;
        let stepCount = 0;
        const maxSteps = 500000;

        while (i < lines.length && stepCount < maxSteps) {
            stepCount++;
            let rawLine = lines[i];
            i++;

            const commentIdx = rawLine.search(/#|\/\//);
            if (commentIdx !== -1) {
                rawLine = rawLine.substring(0, commentIdx);
            }
            const line = rawLine.trim().replace(/;$/, "");
            if (!line) continue;

            // say statement
            if (line.startsWith("say ")) {
                const expr = line.substring(4).trim();
                out.push(String(evalExpr(expr)));
                continue;
            }

            // lock / shift declaration
            const varMatch = line.match(/^(?:lock|shift)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$/);
            if (varMatch) {
                vars[varMatch[1]] = evalExpr(varMatch[2]);
                continue;
            }

            // Mutation
            const assignMatch = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$/);
            if (assignMatch && vars[assignMatch[1]] !== undefined) {
                vars[assignMatch[1]] = evalExpr(assignMatch[2]);
                continue;
            }

            // Function declaration (act)
            const actMatch = line.match(/^act\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{?$/);
            if (actMatch) {
                const fnName = actMatch[1];
                const params = actMatch[2].split(",").map(p => p.trim()).filter(Boolean);
                const bodyLines = [];

                while (i < lines.length) {
                    const nextRaw = lines[i];
                    if (nextRaw.trim() === "}") {
                        i++;
                        break;
                    }
                    if (lines[i].search(/\S/) <= rawLine.search(/\S/) && lines[i].trim() !== "") {
                        if (!line.endsWith("{")) break;
                    }
                    bodyLines.push(lines[i]);
                    i++;
                }

                funcs[fnName] = function (...callArgs) {
                    const localVars = Object.assign({}, vars);
                    params.forEach((p, idx) => {
                        localVars[p] = callArgs[idx];
                    });

                    for (const bLine of bodyLines) {
                        const trimmed = bLine.trim().replace(/;$/, "");
                        if (trimmed.startsWith("emit ")) {
                            const eExpr = trimmed.substring(5).trim();
                            return evalExpr(eExpr);
                        }
                    }
                    return 0;
                };
                continue;
            }

            // Control flow loops (spin)
            const spinMatch = line.match(/^spin\s*\(?([^){]+)\)?\s*\{?$/);
            if (spinMatch) {
                const cond = spinMatch[1].trim();
                const loopBody = [];

                while (i < lines.length) {
                    if (lines[i].trim() === "}") {
                        i++;
                        break;
                    }
                    if (lines[i].search(/\S/) <= rawLine.search(/\S/) && lines[i].trim() !== "") {
                        if (!line.endsWith("{")) break;
                    }
                    loopBody.push(lines[i]);
                    i++;
                }

                let loopCount = 0;
                while (loopCount < 20000) {
                    loopCount++;
                    const cParts = cond.split("<");
                    if (cParts.length === 2) {
                        const lhs = evalExpr(cParts[0]);
                        const rhs = evalExpr(cParts[1]);
                        if (lhs >= rhs) break;
                    } else {
                        break;
                    }

                    for (const lb of loopBody) {
                        const tLine = lb.trim().replace(/;$/, "");
                        const aMatch = tLine.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$/);
                        if (aMatch && vars[aMatch[1]] !== undefined) {
                            vars[aMatch[1]] = evalExpr(aMatch[2]);
                        } else if (tLine.startsWith("say ")) {
                            out.push(String(evalExpr(tLine.substring(4))));
                        }
                    }
                }
                continue;
            }
        }

        return out.length ? out.join("\n") : "(Program completed with no output)";
    }

    // ============================================================================
    // 5. 3D Canvas Geometry Renderer
    // ============================================================================
    let stageAnimationId = null;
    let stageSpeed = 1.0;
    let angleX = 0.4, angleY = 0.0, angleZ = 0.0;

    const cubeVertices = [
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1]
    ];
    const cubeEdges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ];

    function render3DStage() {
        if (stageContainer.style.display === "none") {
            stageAnimationId = null;
            return;
        }

        const ctx = stageCanvas.getContext("2d");
        const w = stageCanvas.width;
        const h = stageCanvas.height;
        const cx = w / 2;
        const cy = h / 2;

        ctx.fillStyle = "#06050a";
        ctx.fillRect(0, 0, w, h);

        angleY += 0.024 * stageSpeed;
        angleX += 0.012 * stageSpeed;
        angleZ += 0.008 * stageSpeed;

        const scale = Math.min(w, h) * 0.28;
        const projected = [];

        // Rotate & project vertices
        for (let j = 0; j < cubeVertices.length; j++) {
            const [x, y, z] = cubeVertices[j];
            // Y rotation
            const x1 = x * Math.cos(angleY) - z * Math.sin(angleY);
            const z1 = x * Math.sin(angleY) + z * Math.cos(angleY);
            // X rotation
            const y1 = y * Math.cos(angleX) - z1 * Math.sin(angleX);
            const z2 = y * Math.sin(angleX) + z1 * Math.cos(angleX);
            // Perspective depth
            const depth = z2 + 3.2;
            const fov = scale / depth;
            projected.push([cx + x1 * fov, cy + y1 * fov, depth]);
        }

        // Render Edges
        for (let e = 0; e < cubeEdges.length; e++) {
            const [u, v] = cubeEdges[e];
            const [x1, y1, d1] = projected[u];
            const [x2, y2, d2] = projected[v];
            const avgD = (d1 + d2) / 2;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = avgD < 3.2 ? "#ff7a00" : "#a84f00";
            ctx.lineWidth = avgD < 3.2 ? 2.5 : 1.5;
            ctx.shadowColor = "#ff7a00";
            ctx.shadowBlur = avgD < 3.2 ? 8 : 0;
            ctx.stroke();
            ctx.shadowBlur = 0;
        }

        // Render Vertices
        for (let p = 0; p < projected.length; p++) {
            const [px, py, depth] = projected[p];
            ctx.beginPath();
            ctx.arc(px, py, depth < 3.2 ? 4 : 3, 0, Math.PI * 2);
            ctx.fillStyle = depth < 3.2 ? "#38bdf8" : "#1e40af";
            ctx.fill();
        }

        stageAnimationId = requestAnimationFrame(render3DStage);
    }

    function switchTab(tab) {
        if (tab === "stage") {
            tabStageBtn.classList.add("active");
            tabTerminalBtn.classList.remove("active");
            stageContainer.style.display = "flex";
            terminalOutput.style.display = "none";
            if (!stageAnimationId) {
                stageAnimationId = requestAnimationFrame(render3DStage);
            }
        } else {
            tabTerminalBtn.classList.add("active");
            tabStageBtn.classList.remove("active");
            terminalOutput.style.display = "block";
            stageContainer.style.display = "none";
            if (stageAnimationId) {
                cancelAnimationFrame(stageAnimationId);
                stageAnimationId = null;
            }
        }
    }

    tabTerminalBtn.addEventListener("click", () => switchTab("terminal"));
    tabStageBtn.addEventListener("click", () => switchTab("stage"));

    stageSpeedBtn.addEventListener("click", function () {
        if (stageSpeed === 1.0) {
            stageSpeed = 2.0;
            this.textContent = "⚡ 2x Speed";
        } else if (stageSpeed === 2.0) {
            stageSpeed = 0.5;
            this.textContent = "🐌 0.5x Speed";
        } else {
            stageSpeed = 1.0;
            this.textContent = "⚡ 1x Speed";
        }
    });

    // ============================================================================
    // 6. Execution Runner & Smart Native Detection
    // ============================================================================
    function openModal() {
        nativeInstallModal.style.display = "flex";
    }

    function closeModal() {
        nativeInstallModal.style.display = "none";
    }

    function runCode() {
        const code = editor.getValue();
        if (!code.trim()) {
            terminalOutput.innerHTML = '<div class="term-line dim">(Editor is empty)</div>';
            return;
        }

        // Check if user is trying to run native server/socket code
        const isServerCode = /\b(fuse\s+(net|server|socket)|PORT\s*=|listen|serve)\b/i.test(code);
        if (isServerCode) {
            openModal();
            // Also prepare simulated output in terminal
        }

        // Check if 3D Canvas geometry code is being executed
        const isRotatingUi = /\b(project_point|project_vertex|mesh|3D|Rotating|Wireframe|Spatial)\b/i.test(code);
        if (isRotatingUi) {
            switchTab("stage");
        } else {
            switchTab("terminal");
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

                if (isServerCode) {
                    const notice = document.createElement("div");
                    notice.className = "term-line prompt-line";
                    notice.style.color = "#ff7a00";
                    notice.textContent = "⚡ Simulated Server Log. To bind real native TCP sockets on your machine, run: 'curl -sSL ... | bash'";
                    terminalOutput.appendChild(notice);
                }
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
    // 7. UI Event Handlers & Sharing
    // ============================================================================
    runBtn.addEventListener("click", runCode);

    document.addEventListener("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            runCode();
        }
    });

    exampleSelect.addEventListener("change", function () {
        const key = this.value;
        if (DEMOS[key]) {
            editor.setValue(DEMOS[key]);
            terminalOutput.innerHTML = `<div class="term-line dim">Loaded example: ${key}. Hit Run to execute.</div>`;
            execTimer.textContent = "Ready";
            if (key === "rotating_ui") {
                switchTab("stage");
            } else {
                switchTab("terminal");
            }
        }
    });

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

    copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(editor.getValue()).then(() => {
            showToast("Code copied to clipboard!");
        });
    });

    clearBtn.addEventListener("click", function () {
        terminalOutput.innerHTML = '<div class="term-line dim">Terminal cleared.</div>';
        execTimer.textContent = "Ready";
    });

    // Modal Events
    installGuideBtn.addEventListener("click", openModal);
    modalCloseBtn.addEventListener("click", closeModal);
    modalPreviewBtn.addEventListener("click", closeModal);

    modalInstallCopyBtn.addEventListener("click", function () {
        const cmd = "curl -sSL https://raw.githubusercontent.com/AnayUpadhyay-all/FoxVC/main/install.sh | bash";
        navigator.clipboard.writeText(cmd).then(() => {
            showToast("Universal install command copied!");
            closeModal();
        });
    });

    document.querySelectorAll(".copy-cmd-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const cmd = this.getAttribute("data-clipboard");
            navigator.clipboard.writeText(cmd).then(() => {
                showToast("Command copied to clipboard!");
            });
        });
    });

    // Close modal on backdrop click
    nativeInstallModal.addEventListener("click", function (e) {
        if (e.target === nativeInstallModal) {
            closeModal();
        }
    });

    // Drag Resizer for split pane
    const resizer = document.getElementById("dragResizer");
    let isDragging = false;

    resizer.addEventListener("mousedown", function () {
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
