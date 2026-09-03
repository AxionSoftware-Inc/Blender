# Spectra Science — Backend Session Product Contract

Status: **source-audit/design contract; no runtime code changed**.

The current runtime already provides a generic `BackendSession` lifecycle over the renderer-neutral `Backend` protocol.

This document defines how product/project/presentation code should use that existing abstraction.

## Existing runtime truth

Backend protocol:

```text
create(scene) -> handle
apply(handle, scene)
destroy(handle)
```

`BackendSession` wraps this as:

```text
BackendSession.open(backend, source_scene)
session.seek(time)
session.close()
```

It samples the Spectra-owned Timeline and sends only static Scene snapshots to the backend.

## Product-facing rule

UI, project runtime, CLI preview, and future WebGPU/Blender host code should prefer `BackendSession` rather than directly juggling native handles.

Conceptual flow:

```python
presented_scene = project.present("presentation.demo.cinematic")
session = BackendSession.open(backend, presented_scene)
session.seek(1.25)
...
session.close()
```

This keeps renderer lifecycle separate from scientific and presentation semantics.

## Scientific time remains Spectra-owned

`BackendSession.seek(t)` calls:

```text
source_scene.sample(t)
```

before backend application.

Therefore Blender/WebGPU/etc. receive static snapshots and do not own scientific time integration.

A backend may cache/bake native animation for performance later, but that cache remains derived from Spectra Timeline semantics.

## Presentation timeline relationship

A presented Scene may contain both:

```text
scientific tracks
presentation tracks
```

provided animation ownership conflicts have been resolved before session open.

`BackendSession` should not understand whether a track is scientific or presentation-owned; it simply samples the final generic Scene Timeline.

Conflict semantics belong upstream in presentation composition.

## Compatibility validation

`BackendSession.open()` and `seek()` already call generic backend compatibility validation.

Future richer `BackendCapabilities` should continue using this boundary.

Do not duplicate compatibility checks in every UI or project host.

Premium capability negotiation may happen before session creation, but the session still validates the resulting Scene contract.

## Session ownership

A session owns one backend handle lifecycle.

Product code must guarantee `close()` on:

```text
project close
renderer switch
preview replacement
fatal renderer error
application shutdown
```

Future context-manager support could improve ergonomics, but is not required to preserve the current contract.

## Renderer switching

Switching Blender -> WebGPU or MemoryBackend should conceptually be:

```text
close old BackendSession
resolve presentation for new capabilities
open new BackendSession with same scientific/presentation source state
```

Do not mutate numerical results because a renderer changed.

## Presentation changes

If presentation intent changes:

```text
base scientific Scene unchanged
    -> recompose presented Scene
    -> update/replace session source_scene
```

Current `BackendSession` does not expose a dedicated `replace_source_scene()` method.

Initial product implementation may safely close/reopen a session when structural presentation changes occur.

A future method may support source replacement while preserving native handles where backend/session semantics allow it.

Do not add that API until concrete presentation runtime needs it.

## Incremental Blender behavior

`IncrementalBlenderBackend` already preserves native objects/data where compatible across `apply()` calls.

Using it through `BackendSession.seek()` retains this behavior.

Therefore product code does not need Blender-specific update loops just to receive incremental animation performance.

## MemoryBackend

MemoryBackend is useful for:

```text
headless inspection
presentation semantic tests
project/view tests
CLI validation
```

The same `BackendSession` flow should work without Blender.

## Remote rendering

A remote renderer is not necessarily an in-process Backend implementation.

However the same conceptual lifecycle should remain:

```text
presented Scene/artifact
    -> remote render request
    -> static/time-sampled or baked representation
```

Do not make remote workers authoritative for scientific semantics.

## Diagnostics

Product-level renderer diagnostics should distinguish:

```text
backend compatibility failure
backend unavailable
native create failure
native apply failure
native destroy/cleanup failure
presentation fallback
```

These are not numerical solver errors.

## Tests after implementation gate

- open samples time zero;
- seek samples Scene at requested time;
- seek validates backend compatibility;
- close destroys native handle once;
- closed session rejects seek;
- IncrementalBlenderBackend remains usable through session;
- MemoryBackend supports the same generic session path;
- renderer switch does not alter scientific result state;
- presentation-only recompose does not trigger numerical solve.

## Success criterion

The product can drive Blender, MemoryBackend, WebGPU, or future renderers through one renderer-neutral session lifecycle while scientific domains and project state remain unaware of native handles.