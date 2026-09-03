# Spectra Science — Trust and Security Model

This document defines trust boundaries for external plugins, native numerical providers, project files, data resources, remote workers, and renderer integrations.

Spectra is a scientific engine, not a sandbox. The architecture should therefore make it explicit which components may execute code and which should be treated only as data.

## Core principle

Scientific semantics and persistent project/resource documents should be data/contracts.

Executable code enters only through explicitly installed/approved software components such as:

```text
Spectra itself
approved Python plugins
approved native providers
approved renderer backends
approved remote workers
```

A project file must not be able to turn arbitrary embedded data into executable code merely by being opened.

## Trust zones

Conceptual zones:

### Zone 1 — Spectra core/runtime

Trusted installed engine code.

### Zone 2 — built-in domains/backends

Shipped with the Spectra distribution and part of the trusted package set.

### Zone 3 — approved third-party plugins/providers

Executable code explicitly installed/enabled by the user, organization, or deployment administrator.

### Zone 4 — project/data documents

Untrusted data by default.

### Zone 5 — remote resources/services

Require explicit network/auth/trust policy.

Opening Zone 4 data must not implicitly promote it to Zone 3 executable code.

## Plugin installation vs project activation

A project may declare that it requires a plugin, for example:

```text
physics.optics package >= version X
```

If the plugin is not installed/enabled, Spectra should report a dependency diagnostic.

It should not:

- download code automatically from an arbitrary URL in the project;
- pip-install code silently;
- execute bundled Python scripts from the project archive by default.

Plugin installation/approval is a separate user/admin action.

## External Python plugins

Third-party Python plugins execute with the privileges of the Spectra process unless sandboxed externally.

Therefore they should be treated like installing any other Python package.

A plugin can potentially:

- read/write files accessible to the process;
- access network resources;
- import native extensions;
- allocate memory/CPU/GPU;
- mutate process state.

Spectra capability contracts improve modularity but do not magically sandbox malicious Python code.

## Plugin approval model

Future product policies may support:

```text
allow all installed plugins
allow signed/approved plugins only
organization allowlist
disable external plugins
per-project plugin enablement
```

Enterprise deployments may require centrally managed allowlists.

## Plugin descriptor integrity

A plugin descriptor should expose metadata before registration side effects where possible:

```text
plugin id
version
vendor/publisher
Spectra compatibility range
domain factories
native providers
requested optional integrations
```

The loader should validate compatibility before calling registration code.

## Capability conflicts

A malicious or accidental plugin must not silently replace another provider simply by import order.

Provider conflicts should be deterministic and inspectable.

If competing providers are allowed for a contract, selection must happen through the explicit catalog/solver/provider mechanism.

## Native numerical providers

Native code has full process-level risk similar to other native extensions.

Before loading a provider validate where possible:

```text
provider identity/version
Spectra native ABI version
platform/architecture
required runtime
supported precision/device
library path provenance
```

Do not load native library paths supplied by arbitrary project documents without policy/approval.

## GPU providers

GPU execution adds resource and driver concerns.

A provider should not be trusted to:

- write beyond declared buffers;
- retain invalid host pointers;
- expose stale device memory as scientific results;
- silently change precision;
- run unsupported kernels for a problem outside compatibility scope.

These are correctness and safety reasons for the validation/provenance contracts in the numerical backend docs.

## External data files

Data importers must treat files as untrusted.

Prefer parsers that read data structures rather than general object deserialization.

Avoid unsafe formats/features that can execute arbitrary code during loading.

Examples of dangerous patterns to avoid:

```text
pickle-like arbitrary object loading from untrusted files
executing scripts/macros embedded in scientific documents
eval of arbitrary expressions from files
shell command expansion in file paths
```

Spectra's safe expression engine is appropriate only for its explicitly restricted grammar, not as a general project-code execution feature.

## Project files

A future `spectra.project` document may contain:

- scientific model records;
- plugin requirements;
- resource references;
- presentation policies;
- experiment artifacts.

Opening it should:

1. parse/validate data;
2. report missing plugin/resource requirements;
3. not execute unapproved code;
4. not automatically contact arbitrary remote endpoints unless policy/user action allows it.

## Remote URLs

A project/resource URI can create privacy/security risks.

Product policy should govern:

- whether remote fetch is allowed;
- allowed protocols/domains;
- authentication handling;
- redirects;
- maximum size;
- caching;
- TLS requirements.

Do not pass credentials embedded in a project file to arbitrary hosts automatically.

## Secrets

Secrets must not be stored in scientific project documents or reproducibility snapshots.

Examples:

- API keys;
- cloud access tokens;
- database passwords;
- SSH private keys.

Projects may refer to a credential profile name managed by the product/platform, but should not serialize the secret itself.

## Remote workers

A remote worker is executable infrastructure and must be authenticated/authorized by the product/deployment.

A worker should verify job/project/resource authorization rather than assuming possession of a job ID grants access to every resource.

See `REMOTE_EXECUTION_AND_WORKERS.md`.

## Worker input

Workers should receive validated semantic/job payloads and approved resource references.

A worker should not import arbitrary Python modules named inside untrusted job JSON unless those modules are installed/allowlisted providers.

## Renderer backends

Renderer integrations such as Blender run powerful native/Python APIs.

Spectra should treat renderer backend code as trusted installed code, while Scene/project data remains untrusted input.

A Scene should not carry arbitrary Blender Python snippets or node scripts to execute.

## Blender files

A `.blend` file can contain arbitrary user content and potentially scripts/configuration outside Spectra control.

Spectra should not represent `.blend` as a safe portable scientific project format.

Scientific source of truth should remain in Spectra semantic/project data where possible.

## Expression handling

Any user-entered mathematical expression should go through the restricted expression engine or an explicitly trusted scripting surface.

Do not silently fall back from restricted expressions to Python `eval()`.

If a future expert mode allows arbitrary Python, it must be labeled executable/trusted code and separated from safe project semantics.

## AI-generated content

AI may generate project/domain code, but executable generated code should follow the same trust path as manually written code.

Do not auto-execute generated Python/native/plugin code merely because it came from a trusted AI interface.

Safer separation:

```text
AI proposes semantic project edits -> validate -> execute engine contracts
AI proposes plugin/source code -> user/developer review/install -> then executable
```

## Resource limits

Security also includes denial-of-service/resource exhaustion.

Product/worker layers may enforce:

- maximum upload/resource size;
- grid/particle count policy;
- CPU time;
- RAM/VRAM limits;
- concurrent jobs;
- render resolution/duration limits.

The engine should report resource-limit diagnostics distinctly from scientific errors.

## Path handling

Project-relative paths should be normalized and constrained by product policy.

When extracting project archives, prevent path traversal such as entries escaping the destination directory.

Do not interpret shell metacharacters in resource paths.

## Serialization robustness

Readers should reject malformed length/count/reference data before allocating absurd amounts of memory where practical.

Large declared shapes should be validated against configured resource limits before materialization.

## Signed packages/releases

Future plugin distribution may use package-signing or trusted repositories, but signature verification is a product/distribution feature separate from scientific capability semantics.

A signature can establish publisher/artifact integrity; it does not prove scientific correctness.

## Scientific trust

Security trust and scientific validity are different.

An approved plugin can still contain scientifically incorrect formulas.

Scientific modules require:

- tests;
- validation;
- maturity labels;
- documented model scope;
- provenance.

Do not treat a signed/approved package as automatically scientifically production-grade.

## Diagnostic requirements

Security/trust-related diagnostics should distinguish:

```text
plugin not installed
plugin disabled by policy
plugin incompatible
unapproved native library
remote resource blocked
credential required
resource exceeds policy limit
unsafe serialization feature rejected
```

Avoid vague "failed to load" messages.

## Default posture

Reasonable default posture for a general Spectra product:

- built-in code trusted;
- external code executes only when explicitly installed/enabled;
- project/resource files treated as data;
- no automatic arbitrary code installation/execution from projects;
- no secrets stored in projects;
- remote access explicit;
- native/GPU providers validated before use;
- capability/provider conflicts never resolved by accidental import order.

## Success criterion

A user should be able to open an untrusted Spectra project/data file to inspect its metadata and dependency requirements without that action silently installing plugins, executing arbitrary Python/native code, contacting arbitrary remote servers, or mutating unrelated Blender/system state.
