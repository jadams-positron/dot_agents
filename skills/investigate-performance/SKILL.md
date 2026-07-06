---
name: investigate-performance
description: Build and run rigorous benchmark, performance, race-condition, fuzz, and profiling investigations for endpoints, APIs, parsers, async jobs, and suspected slow or racy code paths. Use when Codex is asked to design or implement benchmark harnesses, exercise every code path, fuzz user-input surfaces, use pprof or trace, compare before/after results, or optimize verified performance bottlenecks.
---

# Investigate Performance

## Overview

Use this skill to turn a vague performance concern into a repeatable investigation: map the code paths, build realistic harnesses, measure, profile, fuzz user input, optimize only verified hotspots, and report the result with enough evidence to reproduce it.

For Go repositories, read [references/go-bench-fuzz.md](references/go-bench-fuzz.md) when the task involves `go test -bench`, `go test -race`, fuzzing, `go tool pprof`, `go tool trace`, HTTP handlers, or endpoint harnesses.

## Workflow

1. Establish the target surface.
   - Read the relevant implementation, routing, validation, client, persistence, and async worker code before writing tests.
   - List every reachable code path: success, validation failure, dependency failure, capacity or policy block, dry-run, forced execution, cancellation, resume/retry, list/get, status filters, and malformed input.
   - Identify inputs controlled by users or external systems. Treat path parameters, query parameters, request bodies, headers, durations, enum strings, IDs, metadata, and persisted records as fuzz candidates.

2. Build measurement harnesses.
   - Prefer in-process harnesses with mocks, fake transports, `httptest`, temporary dirs, and deterministic timers over live infrastructure unless the user explicitly needs live-system numbers.
   - Add scale dimensions that match the suspected issue: node count, allocation count, job count, payload size, retained history, retry count, and concurrent callers.
   - Make benchmarks assert behavior before reporting speed. A benchmark that accepts incorrect output is not useful.
   - Keep new tests close to the package that owns the behavior.

3. Measure before optimizing.
   - Run correctness tests first, then race tests where concurrency is involved, then benchmarks with allocation reporting.
   - Use CPU, memory, and trace profiles when benchmark results point to unclear or surprising hotspots.
   - Save commands and profile artifact paths in working notes or the final report so the investigation can be repeated.

4. Fuzz all user-input surfaces.
   - Seed fuzzers with valid, boundary, malformed, oversized, and semantically invalid examples.
   - Cap generated input sizes inside the fuzz function when needed to keep runs useful.
   - Assert invariants such as no panic, no internal-server error for ordinary bad input, no accepted invalid duration/enum/ID, stable serialization, and no unsafe state transition.
   - Run fuzz targets individually when multiple fuzzers would compete for CPU or corpus mutation.

5. Investigate race risk.
   - Add tests for concurrent start/list/get/cancel/resume paths and shared persistence.
   - Exercise async paths to completion with explicit waits rather than sleeps alone.
   - Run the relevant package set with `-race`; keep race-only test failures separate from benchmark regressions.

6. Optimize from evidence.
   - Optimize after the baseline exposes a measurable bottleneck.
   - Prefer algorithmic reductions, early exits, bounded fan-out, caching within a single operation, and avoiding repeated deep copies or string conversions in sort/comparison loops.
   - Preserve behavior with focused tests when changing the implementation.
   - Re-run the same benchmarks after each material change and compare `ns/op`, `B/op`, and `allocs/op`.

7. Report findings.
   - State what was exercised, what commands ran, what passed, and what failed or remains unmeasured.
   - Include before/after numbers for every claimed improvement.
   - Separate benchmark findings, race findings, fuzz findings, and production code changes.
   - Call out residual hotspots even when they are outside the current optimization scope.
