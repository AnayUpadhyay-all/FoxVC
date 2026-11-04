# ============================================================================
# FoxVC VHS Demo Recording Script (demo.tape)
# Generates a crisp, 15-second animated GIF/SVG demo for GitHub README.
# Install VHS: brew install vhs / pkg install vhs / go install github.com/charmbracelet/vhs@latest
# Run: vhs demo.tape
# ============================================================================

Output demo.gif
Output demo.svg

Set FontSize 16
Set Width 900
Set Height 520
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Padding 20
Set TypingSpeed 45ms

# 1. Show FoxVC Version & Identity
Type "foxvc --version"
Enter
Sleep 1s

# 2. Inspect Hero Script
Type "cat examples/hero_tic_tac_toe.fox | head -n 22"
Enter
Sleep 2s

# 3. Direct Execution
Type "foxvc run examples/hero_tic_tac_toe.fox"
Enter
Sleep 2.5s

# 4. Standalone Binary Compilation
Type "foxvc build examples/hero_tic_tac_toe.fox -o tictactoe_app"
Enter
Sleep 1.5s

# 5. Native Binary Execution Benchmark
Type "./tictactoe_app"
Enter
Sleep 2.5s
