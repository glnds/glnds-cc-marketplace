# Security checklist

Aligned to OWASP Top 10:2025 RC and ASVS v5.0.0. Patterns assume `rg` (ripgrep) with PCRE2 (`-P`).

> **Self-exclusion trick.** Where patterns below use a one-character class like `[d]angerously...`
> or `[p]ickle`, that is a deliberate regex device: the regex still matches the literal in source
> code, but the literal does not appear in this checklist itself. This avoids both noisy
> self-matches and false positives from local security-reminder hooks.

## Secrets

```bash
# AWS key IDs
rg -n --pcre2 '\b(AKIA|ASIA|AROA|AIDA|AGPA|ANPA|ANVA|AIPA)[A-Z0-9]{16}\b'
# AWS secret keys in context
rg -n --pcre2 '(?i)aws(.{0,20})?(secret|sk|key)["'\'' :=]{1,5}[A-Za-z0-9/+=]{40}'
# Generic high-entropy assignments
rg -n --pcre2 '(?i)(secret|token|passwd|password|api[_-]?key|private[_-]?key)\s*[:=]\s*["'\''][A-Za-z0-9+/=_\-]{16,}["'\'']'
# Private keys
rg -n '-----BEGIN (RSA |OPENSSH |EC |DSA |PGP |ENCRYPTED )?PRIVATE KEY-----'
# JWTs
rg -n --pcre2 '\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b'
# GitHub / Slack / Stripe / Google tokens
rg -n --pcre2 '\b(xox[abpr]-[A-Za-z0-9-]{10,}|ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|ghs_[A-Za-z0-9]{36}|sk_live_[A-Za-z0-9]{24,}|AIza[0-9A-Za-z_\-]{35})\b'
# Credentials in URLs
rg -n --pcre2 '(https?|ftp|redis|mongodb|postgres(ql)?|mysql|amqp)://[^:\s/]+:[^@\s/]+@'
# .env and key files checked in
rg --files -g '*.env' -g '*.env.*' -g '!*.env.example' -g '*.pem' -g '*.key' -g 'id_rsa*'
```

Preferred tool: `gitleaks detect --source . --no-git -v --redact --report-format sarif`
(write to `gitleaks.sarif` with `--report-path`).
Live verification: `trufflehog filesystem --only-verified --no-update .`.

## Dangerous sinks (injection, deserialization, RCE)

```bash
# Python
rg -n --pcre2 '\b(eval|exec|compile)\s*\(' -g '*.py'
rg -n '[p]ickle\.(loads?|Unpickler)|marshal\.loads?|shelve\.open' -g '*.py'
rg -n 'yaml\.load\s*\(' -g '*.py'           # must be yaml.safe_load
rg -n 'subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True' -g '*.py'
rg -n 'os\.(system|popen)|os\.exec[lv]p?e?' -g '*.py'

# JS / TS
rg -n --pcre2 '\beval\s*\(|new\s+Function\s*\(' -g '*.{js,jsx,ts,tsx,mjs,cjs}'
rg -n '[d]angerouslySetInnerHTML' -g '*.{js,jsx,ts,tsx}'   # React unsafe HTML sink
rg -n '(child_process\.)?(exec|execSync|spawn)\s*\(' -g '*.{js,ts,mjs,cjs}'
rg -n 'vm\.(run(InNewContext|InThisContext|InContext)|createContext)' -g '*.{js,ts}'

# Java
rg -n 'Runtime\.getRuntime\(\)\.exec|new\s+ProcessBuilder|ScriptEngineManager|ObjectInputStream' \
  -g '*.java'

# Go
rg -n 'exec\.Command\(|template\.HTML\(|template\.JS\(|template\.URL\(' -g '*.go'

# PHP
PHP_SINKS='\b(eval|assert|create_function|unserialize'
PHP_SINKS+='|system|passthru|shell_exec|proc_open|popen)\s*\('
rg -n --pcre2 "$PHP_SINKS" -g '*.php'

# Path traversal leads
rg -n --pcre2 '\.\./|\.\.\\\\|path\.join\([^)]*(req|request|input|params|query|body)'

# SQL concatenation (high false positives — triage)
rg -n --pcre2 '(SELECT|INSERT|UPDATE|DELETE)[^;\n]{0,120}[\+%].{0,60}(req|params|input|body|user|query)'

# SSRF: HTTP clients taking user URLs
rg -n --pcre2 '(requests\.(get|post|put|delete)|urllib\.request\.urlopen|http\.(get|post)|axios|fetch)\([^)]*(req|request|input|params|body|query|url)'

# XXE
rg -n 'DocumentBuilderFactory|SAXParserFactory|XMLInputFactory' -g '*.java'
rg -n 'etree\.(parse|fromstring)|lxml' -g '*.py'   # verify resolve_entities=False
```

## Cryptography misuse

```bash
# Weak hashes for auth / passwords
rg -n --pcre2 '(?i)(MD5|SHA-?1)\b' -g '*.{py,js,ts,java,go,rb,php,cs}'

# ECB mode, DES, 3DES, RC4, Blowfish
rg -n --pcre2 '\bAES[/_-]?ECB|Cipher\.getInstance\(\s*"(AES|DES|DESede)/ECB' -g '*.{java,kt,scala}'
rg -n --pcre2 '\bMODE_ECB|AES\.new\([^)]*ECB' -g '*.py'
rg -n --pcre2 '\b(DES|3DES|RC4|Blowfish)\b'

# Weak RNG (use crypto/rand, secrets, SecureRandom)
rg -n 'Math\.random\(' -g '*.{js,ts}'
rg -n '\brandom\.(random|randint|choice)\b' -g '*.py'
rg -n 'new Random\(' -g '*.java'
rg -n 'rand\.(Int|Intn|Float)' -g '*.go'

# Hardcoded IV / key
rg -n --pcre2 '(iv|IV|key|KEY)\s*[:=]\s*["'\''][A-Za-z0-9+/=]{8,}["'\'']'

# TLS verification disabled
rg -n 'InsecureSkipVerify\s*:\s*true' -g '*.go'
rg -n 'verify\s*=\s*False|ssl\._create_unverified_context|CERT_NONE' -g '*.py'
rg -n 'rejectUnauthorized\s*:\s*false' -g '*.{js,ts}'
rg -n 'NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*["'\'']?0'

# JWT alg=none or verification disabled
rg -n --pcre2 '(?i)algorithm\s*[:=]\s*["'\'']none["'\'']|verify\s*=\s*False' -g '*.{py,js,ts,java,go}'

# Error message leakage
rg -n 'printStackTrace|traceback\.(print_exc|format_exc)\(\)|res\.send\(err|String\(err\)'
```

## Supply chain (A03:2025)

Unpinned dependencies:

```bash
# npm caret/tilde/*/latest
rg -n --pcre2 '"\s*[\^~]' package.json
rg -n --pcre2 '"[a-zA-Z0-9@/\-_.]+"\s*:\s*"(\*|latest|next|x)"' package.json
test -f package-lock.json || test -f yarn.lock || test -f pnpm-lock.yaml || echo "NO LOCKFILE"

# Python: no == pin
rg -n --pcre2 '^[A-Za-z0-9_.\-\[\]]+\s*(?!==)[<>~!].*$' requirements*.txt
rg -n '^[A-Za-z0-9_.\-]+\s*$' requirements*.txt

# Go: replace with local path
rg -n '^replace\s+' go.mod
rg -n '=> \.\./|=> /' go.mod

# Cargo wildcard
rg -n --pcre2 '"\s*\*\s*"' Cargo.toml

# Maven SNAPSHOT / LATEST / ranges in prod
rg -n 'SNAPSHOT|<version>\s*LATEST|\[.*,\s*\)' pom.xml

# Docker :latest or no tag
rg -n --pcre2 '^FROM\s+\S+:latest\b|^FROM\s+[^:\s]+\s*$' Dockerfile*

# Git deps (supply chain risk)
rg -n 'git\+https?://|github:|file:' package.json

# GitHub Actions not pinned by SHA
rg -n --pcre2 'uses:\s*[^@]+@(v?\d|main|master)' .github/workflows/

# Postinstall scripts
rg -n '"(pre|post)install"\s*:' package.json

# Lockfile integrity / hashes
rg -c 'integrity":' package-lock.json
rg -c '\-\-hash=sha256:' requirements*.txt
```

CVE and SBOM tooling: `osv-scanner scan source -r --format sarif`,
`trivy fs --scanners vuln --severity HIGH,CRITICAL`, `syft . -o cyclonedx-json=sbom.cdx.json`,
`npm audit --audit-level=high --production`, `pip-audit --strict`, `cargo audit --deny warnings`,
`govulncheck -scan symbol ./...`, OWASP `dependency-check --scan . --failOnCVSS 7`. Check for SLSA
provenance with `rg -n 'cosign|in-toto|attestation|provenance' .github/workflows/`.

## Access control and authentication

Verify every route has an auth middleware. Search for anti-patterns:

- Client-side authorization checks.
- Role checks hardcoded to a user ID.
- Missing CSRF tokens on state-changing endpoints.
- CORS `Access-Control-Allow-Origin: *` combined with `Allow-Credentials: true`.
- Password comparison with `==` rather than a constant-time helper (`hmac.compare_digest`,
  `crypto.timingSafeEqual`, `MessageDigest.isEqual`).
- Session IDs generated from weak RNG.

## Logging, alerting, error handling (A09 + A10:2025)

Stack traces returned to clients, silently-swallowed exceptions, and absent audit logs are
first-class findings under the 2025 Top 10. See `resilience-checklist.md` for error-handling
patterns — they overlap.
