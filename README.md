# Spectra Science

`Spectra Science` is a Blender addon foundation for scientific visualization and animation.

## Version 0.3.9 goals

- Default to a clean 2D scientific scene.
- Accept formulas from the Blender UI.
- Generate `y = f(x)` curve graphs.
- Generate `z = f(x, y)` surface graphs.
- Animate graph creation.
- Create simple title, formula and axis labels.
- Update an existing Spectra graph without creating a new object.
- Support named parameters like `a=1, b=2`.
- Support live frame-based animation with `t` and animated parameters.
- Add single-variable calculus helpers: moving point, secant, tangent, and area under the curve.
- Add derivative HUD with live point, slope, angle and tangent formula text.
- Add linked derivative graph `f'(x)` and safer calculus/scene workflow guards.
- Add derivative preset, `h -> 0` secant animation, derivative-graph point, and simplified default UI.
- Improve scene polish: replace old graphs on generate, keep helper positions in sync, and unify scene styling.
- Use a true black background and a clearer mathematical coordinate system with grid and ticks.
- Tie graph/calculus geometry to coordinate unit scale and preserve shared scientific coordinates across templates.
- Add an integral template with signed-area shading, live bounds, bound animation, and realtime HUD values.
- Make the shared coordinate model the single source of truth for graphs, derivative helpers, and integral helpers.
- Keep template switching idempotent so derivative and integral workflows reset cleanly instead of stacking stale helpers.
- Make template buttons build full ready-to-render lesson scenes instead of only filling panel values.
- Auto-build scene, graph, helpers, labels, HUD, and timeline markers in one click while preserving non-Spectra objects.
- Add a full limit module with one-sided/two-sided approach animation, live HUD, hole/target markers, and a dedicated template.
- Improve graph sampling to support discontinuity-aware curve segments and conditional expressions for piecewise-style limit scenes.
- Expand integral teaching with accumulation/FTC mode controls, strip previews, and richer HUD value display.
- Keep the codebase modular for later animation, labels, and render pipeline upgrades.

## Install

1. Zip the `spectra_science` folder, or use the included `install_spectra.sh` for a direct local install.
2. In Blender, open `Edit > Preferences > Add-ons > Install from Disk`.
3. Enable `Spectra Science`.

## Current formula syntax

- Variables: `x`, `y`, `t`
- Constants: `pi`, `e`, `tau`
- Functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `exp`, `log`, `log10`, `sqrt`, `pow`, `floor`, `ceil`, `abs`, `min`, `max`, `round`
- Conditional expressions are supported, for example `-1 if x < 0 else 1`

Examples:

- `sin(x)`
- `sin(x + t) * exp(-x*x/12)`
- `cos(sqrt(x*x + y*y) - t)`
- `a * sin(b * x + t)`
- `sin(a * x) + cos(b * y)`
- `-1 if x < 0 else 1`

## Next steps

- Limit, derivative, and integral teaching templates with stronger storyboard defaults
- Better text/formula rendering
- Vector fields, point clouds, parametric curves and surfaces
- Render presets and one-click export
