# Distilling Go

Apply these checks only to Go artifacts. Follow repository instructions, the declared Go version, established package conventions, and configured tooling before general guidance.

The target is obvious, idiomatic Go—not the fewest lines.

## Preserve Before Reducing

Protect:

- Public APIs and interfaces.
- Serialization, wire, database, and command-line formats.
- Nil-versus-empty behavior where observable.
- Error identity, wrapping, messages, and `errors.Is` or `errors.As` behavior.
- Context cancellation, timeouts, cleanup, goroutine lifetimes, ordering, and synchronization.
- Security and performance properties.
- Generated-code boundaries and test coverage.

## Pass 1: Simplify Structure

- Prefer core language constructs, then the standard library, before adding helpers or dependencies.
- Remove premature interfaces, factories, wrappers, utility packages, and extension points.
- Define an interface in the consuming package, keep it narrow, and introduce it only when a real consumer needs it.
- Return concrete types unless an existing contract requires an interface.
- Prefer a useful zero value when it makes the API safer and easier to use.
- Keep packages cohesive. Avoid package stutter and vague packages such as `util`, `common`, or `types`.
- Do not create an abstraction solely to eliminate a small amount of clear duplication.
- Treat reflection, `unsafe`, cgo, and hidden initialization as complexity that requires concrete justification.

## Pass 2: Simplify Control Flow

- Keep the successful path minimally indented. Handle an error and return or continue before proceeding.
- Handle every error deliberately. Return useful context without breaking error identity.
- Do not use `panic` for normal failures.
- Use Go idioms such as multiple returns, `comma, ok`, `defer`, and small interfaces only when they make behavior clearer.
- Make every goroutine's owner, exit condition, cancellation path, and channel-closing responsibility obvious.
- Prefer serial code when concurrency has no demonstrated need or benefit.
- Keep context in function parameters rather than storing it in structs except where an external interface requires otherwise.
- Prefer straightforward loops and branches over dense functional, reflective, or generic machinery.

## Pass 3: Tighten Names and Documentation

- Run `gofmt`; use the repository's import formatter when configured.
- Use `MixedCaps` or `mixedCaps` and canonical initialisms such as `ID`, `HTTP`, and `URL`.
- Choose names whose length matches their scope. Use short local names and descriptive exported names without repeating the package name.
- Avoid `Get` in getter names. Honor conventional method names and signatures such as `Read`, `Write`, `Close`, and `String`.
- Keep doc comments for exported declarations and non-trivial unexported declarations when local policy requires them.
- Document what callers need: behavior, results, errors, special cases, concurrency guarantees, ownership, and constraints.
- Keep implementation commentary focused on rationale and traps rather than narrating operations.
- Keep error strings lower-case and without terminal punctuation unless a proper noun or complete external message requires otherwise.

## Verify

1. Inspect `go.mod`, toolchain declarations, repository instructions, and existing test commands.
2. Format every changed Go file with repository-standard tools.
3. Run focused tests first, then the repository's broader Go test and lint commands.
4. Run race tests when concurrency behavior changed or is material.
5. Compare the resulting API, errors, data formats, and lifecycle behavior with the preservation contract.

Use current official guidance to resolve ambiguity:

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- [Go Doc Comments](https://go.dev/doc/comment)
- [Google Go Style Guide](https://google.github.io/styleguide/go/guide)

Treat Effective Go as idiomatic background rather than an exhaustive guide to newer language features.
