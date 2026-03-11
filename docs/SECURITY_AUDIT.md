# Cherry Evals — Security, Privacy & Compliance Audit

**Date**: 10 March 2026
**Last updated**: 11 March 2026
**Scope**: Full application (backend, frontend, agents, MCP, infrastructure, legal)
**Status**: Pre-deployment review — remediation in progress

---

## Executive Summary

**46 findings** across security, LLM exploitation, frontend, and compliance.
**4 Critical**, **11 High**, **12 Medium**, **9 Low**, **10 compliance gaps**.

**Remediation progress** (as of 11 March 2026):
- **17 findings fixed** via PRs #20, #22, #23, #25
- **29 findings remaining** (open or partially addressed)

The two most severe issues (RCE via `exec()` and IDOR) have been fixed:
1. ~~**Remote code execution** via `exec()`~~ — Fixed in PR #25 (restricted `__builtins__` to safe allowlist + output scanning)
2. ~~**IDOR** on `DELETE /collections/{id}/examples/{id}`~~ — Fixed in PR #20 (shared `check_collection_ownership()` in `api/deps.py`)

---

## 1. Security Vulnerabilities

### CRITICAL

| ID | Finding | File | Impact | Status |
|----|---------|------|--------|--------|
| SEC-C1 | MCP HTTP mode has no enforced auth | `mcp_server/server.py` | Full unauthenticated access to all data + LLM credits | Open |
| SEC-C2 | IDOR: `remove_example` skips ownership check | `api/routes/collections.py` | Any user can delete any other user's collection examples | **Fixed** (PR #20) |
| SEC-C3 | Billing webhook matches user by email (not unique column) | `api/routes/billing.py` | Wrong user could be tier-upgraded/downgraded | Open |
| SEC-C4 | Hand-rolled JWT validation does not check `iss`, `aud`, `nbf` claims | `api/deps.py` | Tokens from other services sharing the same secret are accepted | Open |
| SEC-C5 | Empty `supabase_jwt_secret` defaults to `""` — trivially forgeable JWTs | `api/deps.py`, `config.py` | Full auth bypass if operator forgets to set env var | Open |

### HIGH

| ID | Finding | File | Status |
|----|---------|------|--------|
| SEC-H1 | `check_collection_example_limit` does not verify collection ownership | `api/deps.py` | Open |
| SEC-H2 | In-memory rate limiter not shared across workers | `api/deps.py` | Open |
| SEC-H3 | Analytics endpoints fully unauthenticated, leak user query history | `api/routes/analytics.py` | **Partial** (PR #22: query strings hidden for anonymous users via privacy scoping) |
| SEC-H4 | Internal exception details leaked to clients (`str(e)` in HTTPException) | `api/routes/search.py`, `export.py`, `mcp_server/server.py` | **Fixed** (PR #20: search/export, PR #22: MCP) |
| SEC-H5 | Qdrant running without auth, ports published to host in docker-compose | `docker-compose.yml` | **Partial** (PR #23: Postgres bound to localhost; Qdrant still open) |
| SEC-H6 | Hardcoded `cherry/cherry` DB credentials in docker-compose and Helm values | `docker-compose.yml`, `values.yaml` | Open |

### MEDIUM

| ID | Finding | File | Status |
|----|---------|------|--------|
| SEC-M1 | Qdrant collection name from user input — no allowlist validation | `api/models/search.py` | **Fixed** (PR #22: regex pattern `^[a-z0-9_]{1,64}$`) |
| SEC-M2 | `sort_by` parameter not validated against allowed values | `api/models/search.py` | **Fixed** (already `Literal` type; PR #22 added test confirming 422) |
| SEC-M3 | `Content-Disposition` filename not sanitized — header injection risk | `api/routes/export.py`, `agents.py` | **Fixed** (PR #20: `_sanitize_filename()` with regex) |
| SEC-M4 | Daily quota TOCTOU race condition (read-then-write without lock) | `api/deps.py` | **Fixed** (PR #20: atomic SQL `UPDATE...WHERE` with rowcount check) |
| SEC-M5 | CORS: `allow_credentials=True` with `allow_methods=["*"]`, `allow_headers=["*"]` | `api/main.py` | Open |
| SEC-M6 | nginx missing CSP, HSTS, Permissions-Policy headers | `frontend/nginx.conf` | **Fixed** (PR #23: CSP, HSTS, X-Frame-Options DENY) |
| SEC-M7 | Helm chart missing all auth/billing secrets (Supabase, Polar, CORS) | `deploy/helm/` | Open |

### LOW

| ID | Finding | File | Status |
|----|---------|------|--------|
| SEC-L1 | IP rate limit uses `request.client.host` behind proxy — all users share one bucket | `api/deps.py` | Open |
| SEC-L2 | `X-Session-Id` stored raw without format validation | `core/traces/events.py` | **Fixed** (PR #22: regex `^[0-9a-zA-Z\-_]{1,100}$`) |
| SEC-L3 | `/analytics/popular` limit has no upper bound | `api/routes/analytics.py` | **Fixed** (PR #22: `Query(20, ge=1, le=200)`) |
| SEC-L4 | Dockerfile runs app as root | `Dockerfile` | Open |
| SEC-L5 | Agentic ingestion may execute LLM-generated code (see LLM section) | `agents/ingestion_agent.py` | **Fixed** (PR #25: restricted exec sandbox)

---

## 2. LLM Exploitation Vulnerabilities

### CRITICAL

| ID | Finding | File | Impact | Status |
|----|---------|------|--------|--------|
| LLM-C1 | `exec()` with full `__builtins__` on LLM-generated ingestion parser code | `agents/ingestion_agent.py` | **Remote code execution** | **Fixed** (PR #25: `safe_builtins` allowlist + output scanning) |
| LLM-C2 | `exec()` with full `__builtins__` on LLM-generated export converter code | `agents/export_agent.py` | **Remote code execution** | **Fixed** (PR #25: `safe_builtins` allowlist + output scanning) |

### HIGH

| ID | Finding | File | Status |
|----|---------|------|--------|
| LLM-H1 | Raw user queries injected into all LLM prompts (no sanitization, no structural separation) | `query_agent.py`, `search_agent.py`, `reranker.py` | Open |
| LLM-H2 | Dataset `question`/`answer` content injected into reranker and evaluator prompts (indirect injection via DB) | `reranker.py`, `search_agent.py` | Open |
| LLM-H3 | `format_description` enables LLM scope creep + triggers RCE via exec() | `agents/export_agent.py` | **Mitigated** (PR #25: exec sandbox prevents RCE; prompt injection risk remains) |
| LLM-H4 | MCP tools have zero auth, rate limits, or quota enforcement | `mcp_server/server.py` | Open |
| LLM-H5 | MCP collection tools expose all users' data (no user scoping) | `mcp_server/server.py` | Open |

### MEDIUM

| ID | Finding | File | Status |
|----|---------|------|--------|
| LLM-M1 | HuggingFace sample rows embedded in Gemini prompt — dataset poisoning risk | `agents/ingestion_agent.py` | **Mitigated** (PR #25: exec sandbox blocks RCE chain; poisoning risk remains) |
| LLM-M2 | No content validation/sanitization on ingested dataset rows | All ingestion adapters | Open |
| LLM-M3 | No length limits on `format_description` or `description` fields sent to LLMs | `api/routes/agents.py` | **Fixed** (existing `max_length` on Pydantic fields: 500 for description, 1000 for format_description) |
| LLM-M4 | LLM-supplied HuggingFace dataset ID passed to `load_dataset()` without allowlisting | `agents/ingestion_agent.py` | **Partial** (PR #22: `hf_dataset_id` pattern validation `^[\w\-./]+$`) |

### LOW

| ID | Finding | File | Status |
|----|---------|------|--------|
| LLM-L1 | LLM reasoning fields (`explanation`, `assessment`, `rationale`) returned unfiltered — system prompt leakage risk | `api/routes/search.py`, `search_agent.py` | Open |

---

## 3. Frontend Findings

| ID | Severity | Finding | File |
|----|----------|---------|------|
| FE-M1 | Medium | Supabase JWT + refresh token stored in localStorage (XSS theft vector) | `src/lib/supabase.js:9` |
| FE-M2 | Medium | No Content-Security-Policy header on nginx | `frontend/nginx.conf` |
| FE-L1 | Low | ProtectedRoute bypasses auth when Supabase env vars missing | `src/components/ProtectedRoute.jsx:9` |
| FE-L2 | Low | OAuth `redirectTo` uses `window.location.origin` instead of hardcoded URL | `src/pages/LoginPage.jsx:60` |
| FE-L3 | Low | Raw server error `detail` rendered in UI | `src/lib/api.js:26` |
| FE-L4 | Low | `Content-Disposition` filename not sanitized in download handler | `src/lib/api.js:34-38` |
| FE-L5 | Low | Polar checkout URL env var not validated for https:// scheme | `src/pages/PricingPage.jsx:3-4` |

**Positive findings**: no `dangerouslySetInnerHTML`, no third-party scripts, no tracking pixels, no npm CVEs, no tokens in URLs. React JSX escaping prevents XSS.

---

## 4. GDPR Compliance Gaps

| # | Gap | Severity | Status |
|---|-----|----------|--------|
| GDPR-1 | **No privacy policy** anywhere (landing page, app, API docs) | Critical | **Fixed**: created `/privacy` page, linked from footer |
| GDPR-2 | **No right to erasure** — no `DELETE /account/me` endpoint; `curation_events.user_id` not FK-cascaded | Critical | Needs backend endpoint |
| GDPR-3 | **No lawful basis articulation** for curation event collection (used for "collective intelligence" with no notice) | Critical | **Fixed**: documented in privacy policy as legitimate interest with opt-out |
| GDPR-4 | **User queries sent to Google Gemini** with no disclosure or consent | Critical | **Fixed**: disclosed in privacy policy Section 3 |
| GDPR-5 | **No sub-processor DPAs** documented or referenced | High | Needs operational DPA review with Supabase, Polar, Google, Anthropic, Qdrant, Langfuse |
| GDPR-6 | **No right to data portability** endpoint | High | Needs `GET /account/export` endpoint |
| GDPR-7 | **No data retention policy** — curation events grow indefinitely | High | Needs retention job or documented policy |
| GDPR-8 | **No ROPA** (Records of Processing Activities) | Medium | Needs internal document |
| GDPR-9 | **API key soft-delete only** — hash+prefix retained after revocation | Low | Should hard-delete after reasonable period |

---

## 5. EU AI Act Compliance Gaps

| # | Gap | Status |
|---|-----|--------|
| AI-1 | **No AI transparency disclosure at point of use** — Article 50 requires "clear and distinguishable" notice when interacting with AI | **Fixed**: documented in Terms of Service Section 8 |
| AI-2 | **Langfuse tracing not instrumented** for LLM calls — no persistent audit trail for AI operations | Needs implementation |

**Risk category**: Limited risk (search assistance tooling). No prohibited or high-risk uses. Human oversight exists (user reviews all AI results before acting).

---

## 6. Cookie / ePrivacy Compliance

| # | Status | Detail |
|---|--------|--------|
| Cookies used | localStorage only (`sb-*-auth-token`) — strictly necessary, exempt from consent |
| Third-party tracking | None |
| Cookie banner needed | **No** — only strictly necessary storage is used |
| Cookie policy | **Fixed**: created `/cookies` page explaining what is stored and why |

---

## 7. Priority Remediation Roadmap

### Done

| # | Fix | PR |
|---|-----|----|
| ~~1~~ | ~~Fix `exec()` sandbox~~ — restricted `__builtins__` to safe allowlist + output scanning | PR #25 |
| ~~2~~ | ~~Fix IDOR~~ — shared `check_collection_ownership()` in `api/deps.py` | PR #20 |
| ~~8~~ | ~~Input length limits~~ — already enforced via Pydantic `max_length` on all agent request fields | Existing |
| ~~11~~ | ~~Add CSP header~~ + HSTS + X-Frame-Options DENY to nginx | PR #23 |
| ~~15~~ | ~~Atomic quota increment~~ — SQL `UPDATE...WHERE` with rowcount check | PR #20 |

### Immediate (before any public access)

1. **Enforce auth on MCP tools** or document that MCP HTTP must never be publicly exposed (SEC-C1)
2. **Add startup assertion** that `supabase_jwt_secret` is non-empty when `auth_enabled=True` (SEC-C5)
3. **Replace hand-rolled JWT** with PyJWT library — validate `iss`, `aud`, `nbf` claims (SEC-C4)
4. **Fix billing webhook** to use `polar_customer_id` for returning subscribers + add UNIQUE on email (SEC-C3)

### Before launch

5. **Add `DELETE /account/me`** endpoint with cascade to curation_events, collections, API keys (GDPR-2)
6. **Add `GET /account/export`** for data portability — all user data as JSON (GDPR-6)
7. **Add structural prompt separation** — XML tags for user data, system instructions in `system` role (LLM-H1, LLM-H2)
8. **Scope MCP collections** to authenticated user (LLM-H5)
9. **Tighten CORS** — restrict `allow_methods` and `allow_headers` to needed values (SEC-M5)
10. **Add Helm auth secrets** — Supabase, Polar, CORS (SEC-M7)
11. **Sign DPAs** with Supabase, Polar.sh, Google, Anthropic (GDPR-5)

### After launch

12. **Move rate limiter** to Redis for multi-worker correctness (SEC-H2)
13. **Add Langfuse instrumentation** to LLM calls for AI Act audit trail (AI-2)
14. **Implement data retention policy** — anonymise curation events older than 24 months (GDPR-7)
15. **Run container as non-root** user (SEC-L4)
16. **Secure Qdrant** with API key in docker-compose and Helm (SEC-H5)
17. **Replace hardcoded DB credentials** with env vars / secrets (SEC-H6)
