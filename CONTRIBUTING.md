# Contributing to FoxVC 🦊

Welcome! We are thrilled you want to help build and expand FoxVC.

FoxVC is built on a simple vision: **a clean, 25-keyword language that compiles directly into 14.3KB standalone native binaries with 0.8ms startup time.**

You do not need to be a compiler expert to contribute. Because FoxVC is designed to be lean and understandable, any developer can contribute a feature, a new standard shelf, or write a tutorial in an afternoon!

---

## 🚀 How to Get Started

### 1. Clone the Repository
```bash
git clone https://github.com/AnayUpadhyay-all/FoxVC.git
cd FoxVC
```

### 2. Run the Test Suite
Before making any changes, verify all unit tests pass on your machine:
```bash
python3 -m unittest discover tests
```
*(You should see `Ran 101 tests ... OK`)*

### 3. Verify the CLI
```bash
./foxvc run examples/hello.fox
./foxvc build examples/hello.fox -o hello_bin
./hello_bin
```

---

## 💡 Ways You Can Contribute

### 1. Build a New "Shelf" (Standard Library Module)
Writing a new shelf in FoxVC takes less than **15 minutes**.
Check out our step-by-step guide:  
👉 **[docs/HOW_TO_CREATE_A_SHELF.md](docs/HOW_TO_CREATE_A_SHELF.md)**

High-priority shelves we are looking for:
- [ ] `shelf regex` — Regular expression matching and searching.
- [ ] `shelf base64` — Base64 string encoding and decoding.
- [ ] `shelf zip` — Extracting and creating `.zip` archives.
- [ ] `shelf math` extensions — Linear algebra (dot product, matrix multiply).
- [ ] `shelf color` — Terminal ANSI color formatting and styling.

### 2. Editor & Tooling Support
- [ ] Syntax highlighting for **Neovim / Vim** (`foxvc.vim`).
- [ ] Syntax highlighting for **Sublime Text** (`FoxVC.sublime-syntax`).
- [ ] TextMate grammar grammar extensions for **Helix** and **Zed**.

### 3. Examples & Mini-Games
- Write a simple game in FoxVC using `shelf graphics` (Raylib).
- Write a fast CLI utility in FoxVC and add it to `examples/`.

---

## 📋 Pull Request Guidelines

1. **Keep it Lean:** FoxVC has an exact **25-keyword limit**. We never add new keywords without extensive RFC discussion.
2. **Zero Regressions:** Run `python3 -m unittest discover tests` and ensure all tests stay green.
3. **Format Code:** Run `./foxvc fmt <file.fox> -w` on any `.fox` example files.
4. **Be Welcoming:** We welcome first-time open-source contributors with open arms! If you get stuck, open an issue or pull request and ask for help.
