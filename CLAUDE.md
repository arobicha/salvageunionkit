# CLAUDE.md — Development Guidance for salvageunionkit

This file governs how code is designed and generated in this repository.

---

## Architecture & Modularity Principles

- **Single Responsibility**: Every file, class, and function must have exactly one reason to change.
- **Anti-God-Object**: Maximum file length is 250 lines. Split logic into small, focused sub-modules.
- **Strict Encapsulation**: Expose only essential interfaces. Keep internal state, helpers, and types private.
- **Dependency Rule**: High-level business logic must never depend on low-level implementation details.
- **Explicit Boundaries**: Pass dependencies via injection. Avoid global state, singletons, and hidden side effects.
- **Component Cohesion**: Group files by domain feature rather than technical type (e.g., `features/billing/`).

## Refactoring Trigger

- **Proactive Splitting**: If a modification pushes a file past 250 lines, refactor it into smaller modules *before* implementing the new feature.

## Extended Design & Clean Code Rules

- **Interface Segregation**: Clients must not be forced to depend on interfaces they do not use.
- **Don't Repeat Yourself (DRY)**: Abstract duplicate logic, but prefer duplication over wrong abstraction.
- **Command-Query Separation (CQS)**: Methods must either change state or return data, never both.
- **Law of Demeter**: Talk only to immediate friends. Avoid long method chains like `a.getB().getC().doSomething()`.
- **Immutability by Default**: Mark variables and data structures read-only unless mutation is strictly required.
- **Tell, Don't Ask**: Instruct objects to perform actions rather than requesting their state to make decisions.
- **Fail Fast**: Validate inputs, arguments, and environmental preconditions immediately at the boundary.
- **Predictable Errors**: Return typed error objects or results instead of throwing generic exceptions for expected failures.

## Testing & Verification

- **Test behavior, not implementation**: Never couple tests to private internals; test observable outcomes.
- **One concept per test**: A single test body covers one behavior. Name tests `given_X_when_Y_then_Z` or `should_verb_condition`.
- **Pure functions first**: Isolate side-effectful code at system boundaries so the core is trivially testable without mocks.
- **No logic in tests**: Tests should be straight-line setup → act → assert. Extract helpers if setup grows complex.

## Data & Types

- **Parse, don't validate**: Convert external input into typed domain objects at entry points. Internal code never handles raw strings or untyped dicts.
- **Prefer value objects**: A `NodeId(str)` is safer than a bare `str`. Use `NewType` and `TypeAlias` to name domain concepts.
- **Make illegal states unrepresentable**: Use enums, narrowed types, and `dataclasses` with field constraints rather than ad-hoc dicts with optional keys.
- **Primitive obsession is a code smell**: If you find yourself passing the same group of primitives together repeatedly, they belong in a dataclass.

## Python-Specific Rules

- Use `@dataclass(frozen=True)` for data-carrying objects unless mutation is explicitly required.
- Annotate all public function signatures with explicit return types.
- Use `TypeAlias` and `NewType` to encode domain distinctions in the type system.
- **Strict layer isolation**: `generators/` and `renderers/` must import nothing from `app/`. Data flows one way: `core → generators → renderers → app`.
- No magic numbers. Name all constants at module scope with a descriptive `ALL_CAPS` identifier.
- Delete commented-out code. Use git history instead.

## Conciseness & Clarity

- Default to writing no comments. Only add one when the *why* is non-obvious: a hidden constraint, a subtle invariant, a workaround for a known bug.
- Never write multi-paragraph docstrings or multi-line comment blocks — one short line max.
- Do not add features, refactor, or introduce abstractions beyond what the task requires.
- Do not add error handling for scenarios that cannot occur. Trust internal guarantees; validate only at system boundaries.
