# Resilience checklist

## Timeouts on every external call

```bash
# Python requests without timeout=
rg -nP 'requests\.(get|post|put|delete|patch|head|request)\((?:(?!timeout=)[\s\S]){0,400}\)' -g '*.py'

# httpx / aiohttp without timeout=
rg -nP '(httpx|aiohttp)\.[A-Za-z]+\((?:(?!timeout=)[\s\S]){0,400}\)' -g '*.py'

# Node fetch without AbortController signal
rg -nP 'fetch\((?:(?!signal:)[\s\S]){0,400}\)' -g '*.{js,ts,mjs}'

# axios without timeout
rg -nP 'axios\.(get|post|put|delete|patch|request)\((?:(?!timeout)[\s\S]){0,400}\)' -g '*.{js,ts}'

# Go http.Client{} without Timeout, or DefaultClient use
rg -nP 'http\.Client\s*\{(?:(?!Timeout)[\s\S]){0,300}\}' -g '*.go'
rg -n 'http\.DefaultClient|http\.Get\(|http\.Post\(' -g '*.go'

# Go contexts with no deadline on the wire
rg -n 'context\.Background\(\)|context\.TODO\(\)' -g '*.go'

# Java HttpClient / RestTemplate defaults
rg -n 'new RestTemplate\(\)|HttpClient\.newHttpClient\(\)' -g '*.java'

# DB drivers with no statement or connection timeout
rg -n 'createConnection|createPool|new Pool\(|DriverManager\.getConnection' -g '*.{js,ts,java}'
```

## Retries, backoff, circuit breakers

Presence of these libraries is a positive signal; absence in a service that makes many upstream
calls is a finding.

```bash
rg -n 'tenacity|backoff\.on_exception|retry\s*\(' -g '*.py'
rg -n '@Retry|Retry\.of|resilience4j' -g '*.{java,kt}'
rg -n 'Polly\.|WaitAndRetry|CircuitBreaker' -g '*.cs'
rg -n '@CircuitBreaker|go-resiliency|sony/gobreaker|hashicorp/go-retryablehttp' -g '*.go'
rg -n 'p-retry|async-retry|axios-retry|cockatiel' -g '*.{js,ts}'
```

## Resource cleanup and error propagation

```bash
# Unmanaged file handles (Python)
rg -nP 'open\([^)]+\)(?!\s*(as|with))' -g '*.py'

# Empty catches
rg -nP 'except[^:]*:\s*(pass|continue|\.\.\.|logger?\.\w+\([^)]*\)\s*$)' -g '*.py'
rg -nP 'catch\s*\([^)]*\)\s*\{\s*\}' -g '*.{js,ts,java,cs}'
rg -nP 'if\s+err\s*!=\s*nil\s*\{\s*\}|_\s*=\s*err\b' -g '*.go'

# Panics / hard exits in library code
rg -n 'panic\(|os\.Exit\(|System\.exit\('
```

## Observability plumbing

```bash
# OpenTelemetry / tracing presence
rg -n 'opentelemetry|otel\.|trace\.Start|Tracer|context\.Propagat'

# Correlation / trace ID propagation
rg -n '(correlation[_-]?id|trace[_-]?id|request[_-]?id|x-request-id|traceparent|tracestate)'

# Structured loggers (presence good; absence on the request path bad)
rg -n 'structlog|zap\.|logrus|slog\.|winston|pino|serilog'
```

## Red flags

- Any external call without an explicit timeout.
- Retry loops without jittered exponential backoff or a max-attempts cap.
- `context.Background()` passed to RPC or DB calls inside request handlers.
- Empty catches or `_ = err` swallows.
- `print()` or `console.log()` used as the production logger.
- Absent `/health`, `/ready`, and `/live` endpoints.
- Unbounded goroutines (`go func(` with no `sync.WaitGroup` or semaphore).
- Default DB connection pool left untuned; no `statement_timeout`.
