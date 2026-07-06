# Spectra Science

`Spectra Science` is a Blender addon foundation for scientific visualization and animation.

## Version 0.2.1 goals

- Default to a clean 2D scientific scene.
- Accept formulas from the Blender UI.
- Generate `y = f(x)` curve graphs.
- Generate `z = f(x, y)` surface graphs.
- Animate graph creation.
- Create simple title, formula and axis labels.
- Update an existing Spectra graph without creating a new object.
- Support named parameters like `a=1, b=2`.
- Support live frame-based animation with `t` and animated parameters.
- Keep the codebase modular for later animation, labels, and render pipeline upgrades.

## Install

1. Zip the `spectra_science` folder.
2. In Blender, open `Edit > Preferences > Add-ons > Install from Disk`.
3. Enable `Spectra Science`.

## Current formula syntax

- Variables: `x`, `y`, `t`
- Constants: `pi`, `e`, `tau`
- Functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `exp`, `log`, `log10`, `sqrt`, `pow`, `floor`, `ceil`, `abs`, `min`, `max`, `round`

Examples:

- `sin(x)`
- `sin(x + t) * exp(-x*x/12)`
- `cos(sqrt(x*x + y*y) - t)`
- `a * sin(b * x + t)`
- `sin(a * x) + cos(b * y)`

## Next steps

- Keyframed parameter controls
- Rebuild/update existing graphs instead of adding new ones
- Labels and formula rendering
- Vector fields, point clouds, parametric curves and surfaces
- Render presets and one-click export
