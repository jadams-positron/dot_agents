# Go Benchmark, Race, Fuzz, And Profile Workflow

Use this reference for Go services, API handlers, parsers, and async workers.

## Source Mapping

Before adding harnesses, inspect:

- Route registration and handler validation.
- Request and response DTO conversion.
- Controller or service orchestration.
- External clients and retry behavior.
- Persistence, list/get/copy/sort paths.
- Async lifecycle: start, phase transitions, cancellation, resume, finalization.
- Error mapping and status-code behavior.

Create a small path matrix in notes or tests. Include happy path, dry run, forced execution, blocked preflight, malformed ID, malformed JSON, invalid enum/status filter, dependency failure, cancellation, and list/get status filtering when present.

## Benchmark Harness Pattern

Use in-process dependencies where possible:

```go
func BenchmarkThing(b *testing.B) {
    subject := newBenchSubject(b, scale)
    b.ReportAllocs()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        got, err := subject.Do(context.Background(), input)
        if err != nil {
            b.Fatal(err)
        }
        if !valid(got) {
            b.Fatalf("invalid result: %#v", got)
        }
    }
}
```

For HTTP clients, prefer `httptest` or a custom `http.RoundTripper` that dispatches to an in-memory mux. Avoid network timing unless the user asked for an integration benchmark.

Use scale sub-benchmarks:

```go
for _, n := range []int{1, 4, 16, 64, 128} {
    b.Run(fmt.Sprintf("items_%d", n), func(b *testing.B) {
        // build fixture at this scale
    })
}
```

Useful commands:

```bash
go test ./target/pkg
go test -race ./target/pkg
go test -run '^$' -bench 'Thing|Endpoint' -benchmem ./target/pkg
```

For before/after comparisons, keep the command identical. If `benchstat` is available, use it; otherwise report the raw benchmark rows and compare `ns/op`, `B/op`, and `allocs/op`.

## Profiling

Generate profiles from the benchmark that reproduces the issue:

```bash
go test -run '^$' -bench 'BenchmarkThing$' -benchmem -cpuprofile /private/tmp/thing-cpu.out -memprofile /private/tmp/thing-mem.out ./target/pkg
go tool pprof -top /private/tmp/thing-cpu.out
go tool pprof -top /private/tmp/thing-mem.out
go test -run '^$' -bench 'BenchmarkThing$' -trace /private/tmp/thing-trace.out ./target/pkg
go tool trace /private/tmp/thing-trace.out
```

If local `go tool pprof` or `go tool trace` is unavailable, check whether a standalone tool is already installed before adding new dependencies. Keep profile artifacts in `/private/tmp` or another disposable location unless the user asks to preserve them.

## Race Tests

Use targeted concurrency tests for shared state:

- Concurrent start/list/get/cancel calls.
- Concurrent persistence and readback.
- Async resume while a previous run is active.
- Cancellation during external-client calls or phase transitions.

Use explicit synchronization where possible:

```go
var wg sync.WaitGroup
for i := 0; i < callers; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        _ = subject.List("")
    }()
}
wg.Wait()
```

Then run:

```bash
go test -race ./target/pkg
```

## Fuzz Targets

Fuzz every user-input or externally supplied surface:

- Path IDs and UUIDs.
- Query filters and enum strings.
- JSON request bodies, including raw malformed bodies.
- Durations, sizes, counts, and booleans.
- Placement or scheduling metadata.
- Persisted records that may be loaded after restart.

Pattern:

```go
func FuzzValidateThing(f *testing.F) {
    for _, seed := range []string{"", "valid", "invalid", "999999999999999999999h"} {
        f.Add(seed)
    }
    f.Fuzz(func(t *testing.T, s string) {
        if len(s) > 256 {
            s = s[:256]
        }
        got := validateThing(s)
        if accepted(got) && !semanticallyValid(s) {
            t.Fatalf("accepted invalid input %q", s)
        }
    })
}
```

Run fuzz targets one at a time:

```bash
go test -run '^$' -fuzz FuzzValidateThing -fuzztime=30s -parallel=1 ./target/pkg
```

Use shorter `-fuzztime` during iteration and longer runs before reporting completion.

## Optimization Checklist

Prefer changes that reduce work at the algorithm level:

- Fetch the minimum data needed before fan-out.
- Stop once enough evidence has been collected.
- Bound concurrency against external systems.
- Sort cheap references before deep-copying large records.
- Avoid repeated `String()` or serialization calls in sort comparators.
- Reuse per-operation derived values rather than recomputing across loops.

After optimizing, run the same correctness, race, fuzz, and benchmark commands used for the baseline. Report both the improvement and any remaining hotspot that still matters.
