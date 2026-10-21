"""
FoxVC Beginner Exercise (Step 1: Small Success -> Step 2: Change One Line)
"""
import sys
import time
import re
from engine.runner import run_foxvc_code


def run_beginner_exercise():
    from engine.cli import get_t, RESET
    t = get_t()

    print(f"\n{t['primary']}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{t['accent']}   🦊 Welcome to FoxVC! Your Very First Exercise   {RESET}")
    print(f"{t['primary']}══════════════════════════════════════════════════════════════{RESET}\n")

    time.sleep(0.2)
    print(f"{t['secondary']}Here is your first FoxVC program (just 1 line of code):{RESET}")
    starter_code = 'say "Welcome to FoxVC!"'
    print(f"\n    {t['primary']}{starter_code}{RESET}\n")

    print(f"{t['dim']}Running it for you now...{RESET}\n")
    time.sleep(0.3)

    # Step 1: Run it and give them their first small success!
    res = run_foxvc_code(starter_code)
    print(f"{t['success']}🎉 Small Success! You just ran your first FoxVC greeting!{RESET}\n")
    time.sleep(0.2)

    # Step 2: Change one line and see the result change
    print(f"{t['accent']}⭐ Step 2: Change One Line{RESET}")
    print(f"Now change the greeting to your own message or name.")
    print(f"For example, type: {t['primary']}say \"Hello, my name is Anay!\"{RESET}\n")

    while True:
        try:
            user_line = input(f"{t['primary']}Your line ❯ {RESET}").strip()
            if not user_line:
                continue
            if user_line.lower() in ("exit", "quit"):
                print(f"\n{t['dim']}Exercise completed. Returning to main menu...{RESET}\n")
                return

            if re.match(r"^print\b", user_line, re.IGNORECASE):
                print(f"{t['error']}💡 Everyday Fix:{RESET}")
                print(f"   In FoxVC, we use 'say' instead of 'print' to show text on the screen.")
                print(f"   Try: {t['primary']}say {user_line[5:].strip()}{RESET}\n")
                continue

            if re.match(r"^say\s+[^\"']+$", user_line) and not any(c in user_line for c in "()[]{}0123456789"):
                word = user_line[3:].strip()
                print(f"{t['error']}💡 Everyday Fix:{RESET}")
                print(f"   You wrote '{word}' without quotation marks.")
                print(f"   To print text or greetings, wrap words in quotes so FoxVC knows it's text.")
                print(f"   Try: {t['primary']}say \"{word}\"{RESET}\n")
                continue

            print(f"\n{t['dim']}Executing your code...{RESET}\n")
            res = run_foxvc_code(user_line)

            if res["success"]:
                print(f"\n{t['success']}✨ Perfect! You changed one line and saw your result update immediately.{RESET}")
                print(f"{t['accent']}You've mastered printing greetings in FoxVC! Keep shipping! 🚀{RESET}\n")
                break
            else:
                # Everyday language error support
                print(f"{t['error']}Oops! That didn't quite work. Here is what happened:{RESET}")
                print(f"{res['error']}\n")
                print(f"{t['secondary']}Don't worry, try typing the line again (or type 'exit' to quit):{RESET}")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{t['dim']}Exercise exited.{RESET}\n")
            break
