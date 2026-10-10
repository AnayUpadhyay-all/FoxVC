# FoxVC (v1.0.0)

> **Zero-Overlap Lean Programming Language**
> *Engine Core: v0.5.2x | Baseline Release*

FoxVC is a lightweight, zero-overlap programming language designed for raw logic and fast simulation loops.
It features a strict 25 zero-overlap keyword set with 0% syntactic overlap against Python, JavaScript, C/C++, Rust, and Lua.

## Installation (Offline & Serverless)

### Linux & macOS
Run in terminal:
  ./install.sh

### Windows
Double-click install.bat or run it in Command Prompt.

## The 25 Zero-Overlap Keywords

act, emit, pack, mold, pick, alt, otherwise, pulse, cycle, spin,
halt, skip, say, ask, guard, trap, fuse, lock, shift, blank,
aye, nay, also, either, deny

## Quick Example (main.fox)

drone = { x: 0, speed: 15, active: aye }
act travel(d, distance)
    d.x += distance
    emit d.x

pick drone.active
    travel(drone, 45)
    say "Drone deployed to coordinate: " + drone.x
otherwise
    say "Drone systems inactive."

## Built-in Shelf Primitives

* Math: sin, cos, tan, sqrt, round, abs, pi
* Clocks: time, sleep
* Collections: len

## License
MIT License. Nexus Systems.
