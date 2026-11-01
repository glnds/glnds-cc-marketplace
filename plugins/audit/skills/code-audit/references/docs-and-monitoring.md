# Documentation and monitoring checklist

## Documentation freshness

```bash
# TODO / FIXME density
rg -nP '\b(TODO|FIXME|HACK|XXX|BUG|KLUDGE|DEPRECATED)\b' --stats

# README references to missing files
for f in $(rg -l '\.\./|\./' README.md docs/**/*.md 2>/dev/null); do
  rg -oP '`([^`]+\.(sh|py|js|ts|tf|yml|yaml|md))`' "$f" | sort -u | \
    while read -r path; do
      path=${path//\`/}
      [ -e "$path" ] || echo "MISSING in $f: $path"
    done
done

# Env var drift (env vars used in code but missing from .env.example)
comm -23 \
  <(rg -hoP 'process\.env\.[A-Z_][A-Z0-9_]+|os\.environ\[[^\]]+\]|os\.getenv\([^)]+\)' | \
      rg -oP '[A-Z_][A-Z0-9_]{2,}' | sort -u) \
  <(rg -oP '^[A-Z_][A-Z0-9_]*' .env.example 2>/dev/null | sort -u)

# ADRs
test -d docs/adr || test -d adr || test -d doc/adr || echo "NO ADRs"
find docs/adr adr doc/adr -name '*.md' 2>/dev/null | wc -l
git log -1 --format=%cs -- docs/adr/ 2>/dev/null

# OpenAPI route drift (declared vs code)
diff <(rg -oP '@(app|router)\.(get|post|put|delete|patch)\("([^"]+)"' -r '$3' | sort -u) \
     <(rg -oP '^\s+(/[A-Za-z0-9_/{}\-]+):\s*$' openapi.yaml | sort -u)

# SECURITY.md presence
test -f SECURITY.md || echo "NO SECURITY.md"

# CHANGELOG freshness
git log -1 --format='%cs %s' -- CHANGELOG.md
```

Red flags: TODO count growing month over month; README quickstart references absent scripts;
`.env.example` mismatch; zero ADRs despite significant `git log` architectural changes; OpenAPI
routes not equal to code routes; runbook URLs that 404; missing `SECURITY.md`; CHANGELOG untouched
for more than six months on an actively developed service.

## Monitoring gaps

```bash
# Handlers without instrumentation
HANDLER='@app\.(get|post|put|delete|patch)'
HANDLER+='|router\.(get|post|put|delete)'
HANDLER+='|func\s+\w+\(w\s+http\.ResponseWriter'
rg -nP "$HANDLER" -g '*.{py,js,ts,go}' -A20 | \
  rg -B1 -P 'tracer|span|metric|counter|histogram' -v

# Absence of OpenTelemetry imports
rg -L 'opentelemetry|otel\.|trace\.Span|Tracer|@opentelemetry/api' \
  -g '*.{py,js,ts,go,java}' -g '!**/test/**' -g '!**/vendor/**'

# Health / readiness / liveness routes
rg -nP '"/?(health|ready|live|healthz|readyz|livez)"' -g '*.{py,js,ts,go,java}' | sort -u

# Alerts without runbook_url
yq '.groups[].rules[] | select(.alert) | select(.annotations.runbook_url == null) | .alert' \
  alerts/*.yaml 2>/dev/null
rg -nP '^\s*- alert:' -g 'prometheus*.yml' -g 'alerts/*.yaml' -c

# SLO / error budget definitions
rg -n --pcre2 '\b(slo|sli|error[_-]?budget|burn[_-]?rate)\b' -g '*.{yaml,yml,md,json}'

# Correlation / trace ID plumbing
rg -n 'MDC\.put|contextvars\.ContextVar|AsyncLocalStorage|logger\.With\('
rg -n 'x-request-id|x-correlation-id|traceparent|tracestate'

# Metrics endpoint
rg -nP '"/metrics"' -g '*.{py,js,ts,go,java}'

# Dashboards as code
find . -path '*/grafana/*.json' -o -path '*/dashboards/*.json' 2>/dev/null | wc -l
```

Red flags: handlers with zero span or metric calls on the golden path; alerts without a
`runbook_url`; no SLOs committed to the repo; logs without `trace_id` or `correlation_id`; missing
`/health` and `/ready` distinction (orchestrators cannot make correct decisions); unbounded metric
cardinality (cost overlap); `/metrics` exposed on the public internet without auth; dashboards only
in the Grafana UI, not under version control.

Preferred validators: `promtool check rules alerts/*.yaml`, `amtool check-config alertmanager.yml`,
`otelcol validate --config=config.yaml`.
