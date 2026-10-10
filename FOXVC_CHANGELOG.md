# FoxVC Changelog

## [0.3.4] - 2026-09-02
### Changed
- **Eliminated Static Render Dependency in FoxVC Web Runtime:**
  - Introduced `WebApplication` as a first-class living runtime concept in `engine/web.py`.
  - Added native `mount <target>` and `show <target>` statements to mount applications into the runtime.
  - Added automatic root discovery: constructing a web model now automatically mounts and registers the active `WebApplication` on `ExecutionResult.web_app` without requiring `render`.
  - Updated FoxVC Studio to detect active `WebApplication` instances automatically and launch them directly (F7) without reporting `"No web document rendered"`.
  - Preserved `render` strictly as a backward-compatible preview statement.
  - Created `examples/interactive_app.fox` modeling a multi-subsystem reactor telemetry console operating entirely through `mount app` with zero `render` calls.
  - Updated `tests/test_web.py` to assert living application creation, headless event dispatching, and dynamic state mutation.
