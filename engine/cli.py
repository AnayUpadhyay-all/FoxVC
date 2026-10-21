"""
FoxVC Workspace CLI & The Den Sandbox Environment (v0.5.2x)
Clean single-header prompt, persistent sandbox session, and strictly .fox file tooling.
"""

import sys
import os

# Auto-resolve parent root so direct execution always works
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import readline
import subprocess
import textwrap

from engine.runner import run_foxvc_project, run_foxvc_diagnostic, run_foxvc_code
from engine.interpreter import Interpreter, FoxPack

ENGINE_VERSION = "0.5.2x"
PUBLIC_VERSION = "1.0.0"
VERSION = f"v{PUBLIC_VERSION} (Engine: v{ENGINE_VERSION})"

# ============================================================================
# True Terminal Themes (OSC Background/Foreground sequences + ANSI Colors)
# ============================================================================
THEMES = {
    "fox": {
        "name": "Fox Amber 🦊",
        "bg_hex": "#1a120c",
        "fg_hex": "#ffb07c",
        "primary": "\033[38;5;208m",      # Fox Orange
        "secondary": "\033[38;5;214m",    # Light Amber
        "accent": "\033[38;5;221m",       # Warm Yellow
        "dim": "\033[38;5;244m",          # Slate Gray
        "error": "\033[38;5;196m",        # Red
        "success": "\033[38;5;48m",       # Spring Green
        "prompt": "\033[38;5;208mfox \033[38;5;214m>\033[0m ",
        "den_header": "\033[38;5;208mden \033[38;5;221m[sandbox]\033[38;5;214m ❯\033[0m ",
        "den_cont": "\033[38;5;240m  │ \033[0m",
    },
    "cyber": {
        "name": "Cyber Cyan ⚡",
        "bg_hex": "#08131a",
        "fg_hex": "#00f0ff",
        "primary": "\033[38;5;51m",       # Neon Cyan
        "secondary": "\033[38;5;45m",     # Sky Blue
        "accent": "\033[38;5;199m",       # Neon Magenta
        "dim": "\033[38;5;243m",
        "error": "\033[38;5;197m",
        "success": "\033[38;5;49m",
        "prompt": "\033[38;5;51mcyber \033[38;5;199m>\033[0m ",
        "den_header": "\033[38;5;51mcyber \033[38;5;199m[sandbox]\033[38;5;45m ❯\033[0m ",
        "den_cont": "\033[38;5;240m  │ \033[0m",
    },
    "matrix": {
        "name": "Matrix Terminal 🟢",
        "bg_hex": "#041206",
        "fg_hex": "#00ff66",
        "primary": "\033[38;5;46m",       # Bright Green
        "secondary": "\033[38;5;40m",     # Mid Green
        "accent": "\033[38;5;82m",        # Pale Green
        "dim": "\033[38;5;238m",
        "error": "\033[38;5;160m",
        "success": "\033[38;5;118m",
        "prompt": "\033[38;5;46mmatrix \033[38;5;40m#\033[0m ",
        "den_header": "\033[38;5;46mmatrix \033[38;5;82m[sandbox]\033[38;5;40m ❯\033[0m ",
        "den_cont": "\033[38;5;238m  │ \033[0m",
    },
    "mono": {
        "name": "Charcoal Minimal 🌑",
        "bg_hex": "#121212",
        "fg_hex": "#e0e0e0",
        "primary": "\033[38;5;253m",      # Off White
        "secondary": "\033[38;5;248m",    # Light Gray
        "accent": "\033[38;5;255m",       # Pure White
        "dim": "\033[38;5;240m",
        "error": "\033[38;5;203m",
        "success": "\033[38;5;250m",
        "prompt": "\033[38;5;253mcli \033[38;5;244m>\033[0m ",
        "den_header": "\033[38;5;253mden \033[38;5;255m[sandbox]\033[38;5;248m ❯\033[0m ",
        "den_cont": "\033[38;5;240m  │ \033[0m",
    }
}

CURRENT_THEME = "fox"
RESET = "\033[0m"


def get_t():
    return THEMES[CURRENT_THEME]


def apply_terminal_theme(theme_key: str):
    t = THEMES[theme_key]
    sys.stdout.write(f"\033]11;{t['bg_hex']}\007")
    sys.stdout.write(f"\033]10;{t['fg_hex']}\007")
    sys.stdout.flush()


def restore_terminal_theme():
    sys.stdout.write("\033]111\007")
    sys.stdout.write("\033]110\007")
    sys.stdout.write(RESET)
    sys.stdout.flush()


def print_banner():
    t = get_t()
    banner = f"""
{t['primary']}  ███████╗ ██████╗ ██╗  ██╗██╗   ██╗ ██████╗ 
{t['primary']}  ██╔════╝██╔═══██╗╚██╗██╔╝██║   ██║██╔════╝ 
{t['secondary']}  █████╗  ██║   ██║ ╚███╔╝ ██║   ██║██║      
{t['secondary']}  ██╔══╝  ██║   ██║ ██╔██╗ ╚██╗ ██╔╝██║      
{t['accent']}  ██║     ╚██████╔╝██╔╝ ██╗ ╚████╔╝ ╚██████╗ 
{t['accent']}  ╚═╝      ╚═════╝ ╚═╝  ╚═╝  ╚═══╝   ╚═════╝ 
{t['dim']}  FoxVC Studio Engine [v{VERSION}]
{t['dim']}  Theme: {t['name']} {t['dim']}| Type 'help' for commands, 'den sandbox' for scratchpad.{RESET}
"""
    print(banner)


def show_cli_help():
    t = get_t()
    print(f"""
{t['accent']}FoxVC Workspace File Operations (.fox only):{RESET}
  {t['primary']}view <file.fox>{RESET}         Inspect .fox source code with line numbering 📄
  {t['primary']}edit <file.fox>{RESET}         Open and edit .fox file directly in editor ✏️
  {t['primary']}add <file.fox>{RESET}          Create a fresh .fox script with starter template 📝
  {t['primary']}remove <file.fox>{RESET}       Delete a .fox file from workspace 🗑️
  {t['primary']}run <file.fox>{RESET}          Execute a FoxVC script directly ⚡

{t['accent']}Den Sandbox & Interactive Tools:{RESET}
  {t['primary']}exercise{RESET}                 First interactive greeting exercise for beginners 🎓
  {t['primary']}den sandbox{RESET}             Enter persistent multiline scratchpad 🧪
  {t['primary']}theme [name]{RESET}            Switch theme ({', '.join(THEMES.keys())}) 🎨
  {t['primary']}assist [topic]{RESET}          FoxVC architectural advice and recipes 💡
  {t['primary']}suggest{RESET}                 Show clean native patterns (pack, case, pulse) 🔍
  {t['primary']}vars / fns{RESET}              Inspect running variables and declared functions 📊
  {t['primary']}clear{RESET}                   Clear screen 🧹
  {t['primary']}exit / quit{RESET}             Leave FoxVC 👋
""")


def validate_fox_extension(filename: str) -> bool:
    f = filename.strip()
    return f.endswith(".fox") or f.endswith(".foxc")


def handle_view(args: list):
    t = get_t()
    filename = args[0] if args else "main.fox"
    if not validate_fox_extension(filename):
        print(f"{t['error']}FoxVC Security: Cannot open non-FoxVC file '{filename}'. Only .fox files allowed!{RESET}")
        return
    if not os.path.exists(filename):
        print(f"{t['error']}File '{filename}' does not exist.{RESET}")
        return

    print(f"\n{t['accent']}─── Viewing: {filename} ───{RESET}")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                print(f"{t['dim']}  (Empty file){RESET}")
            for i, line in enumerate(lines, start=1):
                print(f"{t['dim']}{i:3d} │{RESET} {line.rstrip()}")
    except Exception as e:
        print(f"{t['error']}Failed to read file: {e}{RESET}")
    print()


def handle_add(args: list):
    t = get_t()
    if not args:
        print(f"{t['dim']}Usage: add <filename.fox>{RESET}")
        return
    filename = args[0]
    if not filename.endswith(".fox"):
        filename += ".fox"

    if os.path.exists(filename):
        print(f"{t['error']}File '{filename}' already exists.{RESET}")
        return

    template = f"""# {filename} - FoxVC v{VERSION}
core = pack {{
    name: "Entity",
    speed: 10
}}

define start()
    say "Initialized: " + core.name
    case core.speed > 5
        say "High performance mode active."
    otherwise
        say "Standard mode active."

start()
"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"{t['success']}✓ Created FoxVC file '{filename}'!{RESET}")
    except Exception as e:
        print(f"{t['error']}Could not create file: {e}{RESET}")


def handle_remove(args: list):
    t = get_t()
    if not args:
        print(f"{t['dim']}Usage: remove <filename.fox>{RESET}")
        return
    filename = args[0]
    if not validate_fox_extension(filename):
        print(f"{t['error']}FoxVC Security: Cannot remove non-FoxVC file '{filename}'. Only .fox files managed!{RESET}")
        return
    if not os.path.exists(filename):
        print(f"{t['error']}File '{filename}' not found.{RESET}")
        return

    confirm = input(f"{t['error']}Are you sure you want to delete '{filename}'? (y/n): {RESET}").strip().lower()
    if confirm in ("y", "yes"):
        try:
            os.remove(filename)
            print(f"{t['success']}✓ Deleted '{filename}'.{RESET}")
        except Exception as e:
            print(f"{t['error']}Failed to delete file: {e}{RESET}")
    else:
        print(f"{t['dim']}Deletion cancelled.{RESET}")


def handle_edit(args: list):
    t = get_t()
    filename = args[0] if args else "main.fox"
    if not filename.endswith(".fox"):
        filename += ".fox"
    if not validate_fox_extension(filename):
        print(f"{t['error']}FoxVC Security: Only .fox files can be edited inside FoxVC.{RESET}")
        return

    if not os.path.exists(filename):
        print(f"{t['secondary']}File '{filename}' does not exist. Creating it first...{RESET}")
        handle_add([filename])

    editor = os.environ.get("EDITOR") or "nano"
    try:
        subprocess.call([editor, filename])
        print(f"{t['success']}✓ Finished editing '{filename}'.{RESET}")
    except Exception as e:
        print(f"{t['error']}Could not launch editor '{editor}': {e}{RESET}")


def handle_assist(query: str):
    t = get_t()
    if not query.strip():
        print(f"{t['dim']}Usage: assist <topic or question>{RESET}")
        return
    print(f"\n{t['accent']}🦊 FoxVC Assistant Protocol:{RESET}")
    q = query.lower()
    if "orbit" in q or "circle" in q or "spin" in q:
        print(f"{t['secondary']}Orbital mechanics in FoxVC:{RESET}")
        print(f"  Hold properties in a {t['primary']}pack {{ angle: 0, radius: 100, speed: 2 }}{RESET}.")
        print(f"  Increment angle with frame delta inside {t['primary']}pulse dt{RESET}.")
    elif "branch" in q or "if" in q or "condition" in q:
        print(f"{t['secondary']}Branching flow in FoxVC:{RESET}")
        print(f"  Use {t['primary']}case <condition>{RESET} for true checks.")
        print(f"  Use {t['primary']}otherwise{RESET} for alternative paths.")
    elif "loop" in q or "game" in q or "tick" in q:
        print(f"{t['secondary']}Native game loops in FoxVC:{RESET}")
        print(f"  Use {t['primary']}pulse dt{RESET}. Yields elapsed frame seconds automatically.")
    else:
        print(f"  FoxVC v0.5.2x has a strict minimal keyword core:")
        print(f"  • {t['primary']}pack {{ key: val }}{RESET}  -> Compound entity state")
        print(f"  • {t['primary']}case / otherwise{RESET} -> Control flow")
        print(f"  • {t['primary']}pulse dt{RESET}         -> Clock-driven execution")
    print()


def handle_suggest():
    t = get_t()
    print(f"\n{t['accent']}💡 Native FoxVC v0.5.2x Idioms:{RESET}")
    print(f"""
{t['dim']}# 1. Compound Pack Data{RESET}
player = pack {{
    hp: 100,
    alive: true
}}

{t['dim']}# 2. Case Branching{RESET}
define verify_player()
    case player.hp <= 0
        player.alive = false
        say "Defeated!"
    otherwise
        say "Standing strong."

{t['dim']}# 3. Frame Pulse Heartbeat{RESET}
pulse dt
    verify_player()
""")


# ============================================================================
# The Den Sandbox Sub-Environment (Persistent & Clean Multi-line Prompt) 🧪
# ============================================================================
def normalize_sandbox_buffer(buffer_lines: list) -> str:
    """Auto-normalizes pasted code blocks and removes accidental leading indentation."""
    lines = list(buffer_lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""

    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    if non_empty:
        first_indent = len(non_empty[0]) - len(non_empty[0].lstrip())
        if len(non_empty) > 1:
            second_indent = len(non_empty[1]) - len(non_empty[1].lstrip())
            if first_indent > 0 and second_indent > first_indent:
                diff = second_indent - first_indent
                idx = lines.index(non_empty[0])
                lines[idx] = (" " * diff) + lines[idx]

    return textwrap.dedent("\n".join(lines))


def enter_den_sandbox(interp: Interpreter):
    t = get_t()
    print(f"\n{t['primary']}╔════════════════════════════════════════════════════════╗{RESET}")
    print(f"{t['primary']}║  🧪 THE DEN SANDBOX [v{VERSION}]                       ║{RESET}")
    print(f"{t['secondary']}║  Session is persistent (stays open until 'exit').     ║{RESET}")
    print(f"{t['accent']}║  • Type 'den' then Enter, then 'run' to execute block   ║{RESET}")
    print(f"{t['accent']}║  • OR press Ctrl+D to execute buffer without exiting   ║{RESET}")
    print(f"{t['dim']}║  • Type 'vars', 'fns', 'clear', or 'exit' to quit      ║{RESET}")
    print(f"{t['primary']}╚════════════════════════════════════════════════════════╝{RESET}\n")

    buffer = []

    while True:
        t = get_t()
        try:
            # Clean prompt: Header on line 1, clean continuation on lines 2+
            prompt_str = t["den_cont"] if buffer else t["den_header"]
            line = input(prompt_str)

            # Commands only available when not inside an unfinished code block
            if not buffer:
                cmd = line.strip().lower()
                if cmd in ("exit", "quit"):
                    print(f"\n{t['secondary']}Exiting sandbox. Returning to main CLI... 👋{RESET}\n")
                    break
                if cmd == "clear":
                    os.system("clear" if os.name != "nt" else "cls")
                    print(f"{t['dim']}(Sandbox cleared. Ready.){RESET}")
                    continue
                if cmd == "vars":
                    if not interp.variables:
                        print(f"{t['dim']}(no variables defined){RESET}")
                    else:
                        for k, v in interp.variables.items():
                            print(f"  {t['primary']}{k}{RESET} = {t['accent']}{v}{RESET}")
                    continue
                if cmd == "fns":
                    if not interp.functions:
                        print(f"{t['dim']}(no functions defined){RESET}")
                    else:
                        for fn_name, fn_obj in interp.functions.items():
                            p = ", ".join(getattr(fn_obj, "params", []))
                            print(f"  {t['secondary']}define {fn_name}({p}){RESET}")
                    continue

            # Stage command via typing 'den'
            if line.strip().lower() == "den":
                print(f"{t['secondary']}Staging complete. Type 'run' to execute, 'discard' to cancel.{RESET}")
                try:
                    follow = input(f"{t['primary']}den ❯\033[0m ").strip().lower()
                    if follow == "run":
                        code = normalize_sandbox_buffer(buffer)
                        if code.strip():
                            print(f"{t['accent']}⚡ Executing...{RESET}")
                            res = run_foxvc_code(code, filename="<sandbox>", interp=interp)
                            if res.get("emitted") is not None:
                                print(f"--> Emitted: {res['emitted']}")
                            if not res["success"]:
                                print(f"{t['error']}{res['error']}{RESET}")
                        else:
                            print(f"{t['dim']}(Buffer is empty){RESET}")
                        buffer = []
                        # Stays inside sandbox!
                        continue
                    elif follow in ("discard", "cancel"):
                        buffer = []
                        print(f"{t['dim']}Buffer discarded.{RESET}")
                        continue
                    else:
                        print(f"{t['error']}Unknown command '{follow}'. Type 'run' or 'discard'.{RESET}")
                        continue
                except (KeyboardInterrupt, EOFError):
                    print(f"\n{t['dim']}Cancelled.{RESET}")
                    continue

            buffer.append(line)

        except EOFError:
            # Ctrl+D executes buffer but KEEPS YOU in the sandbox!
            if buffer:
                print(f"\n{t['accent']}⚡ [Ctrl+D] Executing Sandbox Buffer...{RESET}")
                code = normalize_sandbox_buffer(buffer)
                res = run_foxvc_code(code, filename="<sandbox>", interp=interp)
                if res.get("emitted") is not None:
                    print(f"{t['success']}--> Emitted: {res['emitted']}{RESET}")
                if not res["success"]:
                    print(f"{t['error']}{res['error']}{RESET}")
                buffer = []
            else:
                # If buffer is already empty and they hit Ctrl+D again, exit
                print(f"\n{t['dim']}Exiting sandbox. Returning to main CLI...{RESET}\n")
                break

        except KeyboardInterrupt:
            # Ctrl+C clears current multi-line buffer without crashing out
            buffer = []
            print(f"\n{t['dim']}(Buffer cleared. Still in sandbox. Type 'exit' to leave.){RESET}")
            continue


# ============================================================================
# Main Outer CLI Loop
# ============================================================================
def start_outer_cli():
    global CURRENT_THEME
    apply_terminal_theme(CURRENT_THEME)
    print_banner()
    interp = Interpreter()

    try:
        while True:
            t = get_t()
            try:
                raw = input(t["prompt"]).strip()
                if not raw:
                    continue

                parts = raw.split()
                cmd = parts[0].lower()
                args = parts[1:]

                # 1. Den Sandbox & Exercise Entry Points
                if cmd in ("exercise", "tutorial", "start", "learn"):
                    from engine.exercise import run_beginner_exercise
                    run_beginner_exercise()
                    continue

                if cmd == "den" and args and args[0].lower() == "sandbox":
                    enter_den_sandbox(interp)
                    continue

                # 2. File Operations (Strictly .fox only)
                if cmd == "view":
                    handle_view(args)
                    continue

                if cmd == "add":
                    handle_add(args)
                    continue

                if cmd in ("edit", "open"):
                    handle_edit(args)
                    continue

                if cmd in ("remove", "rm", "delete"):
                    handle_remove(args)
                    continue

                if cmd == "run":
                    if not args:
                        print(f"{t['dim']}Usage: run <filename.fox>{RESET}")
                    else:
                        target = args[0]
                        if not validate_fox_extension(target):
                            print(f"{t['error']}Cannot run '{target}'. Only .fox files can be executed!{RESET}")
                        else:
                            run_foxvc_project(target)
                    continue

                # 3. Workspace Helpers
                if cmd in ("exit", "quit", ":q"):
                    print(f"\n{t['secondary']}Leaving the Den. Keep shipping! 👋{RESET}")
                    break

                if cmd == "help":
                    show_cli_help()
                    continue

                if cmd == "clear":
                    os.system("clear" if os.name != "nt" else "cls")
                    print_banner()
                    continue

                if cmd == "assist":
                    handle_assist(" ".join(args))
                    continue

                if cmd == "suggest":
                    handle_suggest()
                    continue

                if cmd == "theme":
                    if not args:
                        print(f"{t['dim']}Active theme: {t['name']}. Available: {', '.join(THEMES.keys())}{RESET}")
                    elif args[0].lower() in THEMES:
                        CURRENT_THEME = args[0].lower()
                        apply_terminal_theme(CURRENT_THEME)
                        t = get_t()
                        print(f"{t['success']}✓ Switched theme to {t['name']}{RESET}")
                    else:
                        print(f"{t['error']}Unknown theme. Choices: {', '.join(THEMES.keys())}{RESET}")
                    continue

                if cmd == "vars":
                    if not interp.variables:
                        print(f"{t['dim']}(no variables defined){RESET}")
                    else:
                        for k, v in interp.variables.items():
                            print(f"  {t['primary']}{k}{RESET} = {t['accent']}{v}{RESET}")
                    continue

                if cmd == "fns":
                    if not interp.functions:
                        print(f"{t['dim']}(no functions defined){RESET}")
                    else:
                        for fn_name, fn_obj in interp.functions.items():
                            fn_params = ", ".join(getattr(fn_obj, "params", []))
                            print(f"  {t['secondary']}define {fn_name}({fn_params}){RESET}")
                    continue

                # 4. Direct statement evaluation
                res = run_foxvc_code(raw, filename="<cli>", interp=interp)
                if res.get("emitted") is not None:
                    print(f"{t['success']}--> Emitted: {res['emitted']}{RESET}")
                if not res["success"]:
                    print(f"{t['error']}{res['error']}{RESET}")

            except KeyboardInterrupt:
                print(f"\n{t['dim']}(Interrupted){RESET}")
                continue
            except EOFError:
                print(f"\n{t['secondary']}Leaving the Den. Keep shipping! 👋{RESET}")
                break
    finally:
        restore_terminal_theme()


def main():
    args = sys.argv[1:]

    if not args:
        start_outer_cli()
        return

    cmd = args[0].lower()

    if cmd in ("-v", "--version", "version"):
        print(f"FoxVC Engine v{VERSION}")
        return

    if cmd in ("-h", "--help", "help"):
        show_cli_help()
        return

    if cmd in ("exercise", "tutorial", "start", "learn"):
        from engine.exercise import run_beginner_exercise
        run_beginner_exercise()
        return

    if cmd == "check":
        target = args[1] if len(args) > 1 else "."
        sys.exit(run_foxvc_diagnostic(target))

    if cmd == "compile":
        if len(args) < 2:
            print("Error: Expected file path. Usage: foxvc compile <file.fox>", file=sys.stderr)
            sys.exit(1)
        src = args[1]
        from engine.c_vm import FoxCVM
        out = FoxCVM().compile_fox_file(src)
        print(f"⚡ Successfully compiled '{src}' -> '{out}' (AOT Bytecode)")
        sys.exit(0)

    if cmd == "run":
        if len(args) < 2:
            print("Error: Expected file path. Usage: foxvc run <file.fox>", file=sys.stderr)
            sys.exit(1)
        if not validate_fox_extension(args[1]):
            print(f"Error: Refusing to run '{args[1]}'. FoxVC only executes .fox files.", file=sys.stderr)
            sys.exit(1)
        sys.exit(run_foxvc_project(args[1]))

    if os.path.exists(cmd) or cmd.endswith(".fox"):
        if not validate_fox_extension(cmd):
            print(f"Error: '{cmd}' is not a valid FoxVC source (.fox) file.", file=sys.stderr)
            sys.exit(1)
        sys.exit(run_foxvc_project(cmd))

    print(f"Unknown command: '{cmd}'. Run 'foxvc help' for usage.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
