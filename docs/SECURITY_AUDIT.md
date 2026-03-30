# Cherry Evals — Security, Privacy & Compliance Audit

**Date**: 10 March 2026
**Last updated**: 31 March 2026
**Scope**: Full application (backend, frontend, agents, MCP, infrastructure, legal)
**Status**: Pre-deployment review — remediation in progress

---

## Executive Summary

**46 findings** across security, LLM exploitation, frontend, and compliance.
**4 Critical**, **11 High**, **12 Medium**, **9 Low**, **10 compliance gaps**.

**Remediation progress** (as of 31 March 2026):
- **30 findings fixed** via PRs #20, #22, #23, #25, #27, #28, #29
- **16 findings remaining** (open or partially addressed)

All Critical security vulnerabilities have been resolved:
1. ~~**Remote code execution** via `exec()`~~ — Fixed in PR #25
2. ~~**IDOR** on `DELETE /collections/{id}/examples/{id}`~~ — Fixed in PR #20
3. ~~**MCP HTTP unauthenticated access**~~ — Fixed in PR #28 (API key auth middleware)
4. ~~**Billing webhook email-only lookup**~~ — Fixed in PR #27 (UNIQUE on `polar_customer_id`)
5. ~~**JWT missing issuer validation**~~ — Fixed in PR #27 (PyJWT `iss` check)
6. ~~**Empty JWT secret silent fallback**~~ — Fixed in PR #27 (startup ValueError)

---

## 1. Security Vulnerabilities

### CRITICAL

| ID | Finding | File | Impact | Status |
|----|---------|------|--------|--------|
| SEC-C1 | MCP HTTP mode has no enforced auth | `mcp_server/server.py` | Full unauthenticated access to all data + LLM credits | **Fixed** (PR #28: API key auth middleware + user scoping) |
| SEC-C2 | IDOR: `remove_example` skips ownership check | `api/routes/collections.py` | Any user can delete any other user's collection examples | **Fixed** (PR #20) |
| SEC-C3 | Billing webhook matches user by email (not unique column) | `api/routes/billing.py` | Wrong user could be tier-upgraded/downgraded | **Fixed** (PR #27: UNIQUE on `polar_customer_id`, already used as primary lookup) |
| SEC-C4 | Hand-rolled JWT validation does not check `iss`, `aud`, `nbf` claims | `api/deps.py` | Tokens from other services sharing the same secret are accepted | **Fixed** (PR #27: issuer validation via `supabase_url + /auth/v1`) |
| SEC-C5 | Empty `supabase_jwt_secret` defaults to `""` — trivially forgeable JWTs | `api/deps.py`, `config.py` | Full auth bypass if operator forgets to set env var | **Fixed** (PR #27: startup ValueError instead of silent fallback) |

### HIGH

| ID | Finding | File | Status |
|----|---------|------|--------|
| SEC-H1 | `check_collection_example_limit` does not verify collection ownership | `api/deps.py` | **Fixed** (PR #20: ownership check added at lines 392-396) |
| SEC-H2 | In-memory rate limiter not shared across workers | `api/deps.py` | Open |
| SEC-H3 | Analytics endpoints fully unauthenticated, leak user query history | `api/routes/analytics.py` | **Fixed** (PR #22 + PR #27: `get_optional_user` dependency, stats scoped to user) |
| SEC-H4 | Internal exception details leaked to clients (`str(e)` in HTTPException) | `api/routes/search.py`, `export.py`, `mcp_server/server.py` | **Fixed** (PR #20: search/export, PR #22: MCP) |
| SEC-H5 | Qdrant running without auth, ports published to host in docker-compose | `docker-compose.yml` | **Fixed** (PR #23: localhost binding, PR #29: `QDRANT__SERVICE__API_KEY` env var) |
| SEC-H6 | Hardcoded `cherry/cherry` DB credentials in docker-compose and Helm values | `docker-compose.yml`, `values.yaml` | **Fixed** (PR #23: docker-compose uses env vars, PR #29: Helm `password: ""` REQUIRED) |

### MEDIUM

| ID | Finding | File | Status |
|----|---------|------|--------|
| SEC-M1 | Qdrant collection name from user input — no allowlist validation | `api/models/search.py` | **Fixed** (PR #22: regex pattern `^[a-z0-9_]{1,64}$`) |
| SEC-M2 | `sort_by` parameter not validated against allowed values | `api/models/search.py` | **Fixed** (already `Literal` type; PR #22 added test confirming 422) |
| SEC-M3 | `Content-Disposition` filename not sanitized — header injection risk | `api/routes/export.py`, `agents.py` | **Fixed** (PR #20: `_sanitize_filename()` with regex) |
| SEC-M4 | Daily quota TOCTOU race condition (read-then-write without lock) | `api/deps.py` | **Fixed** (PR #20: atomic SQL `UPDATE...WHERE` with rowcount check) |
| SEC-M5 | CORS: `allow_credentials=True` with `allow_methods=["*"]`, `allow_headers=["*"]` | `api/main.py` | **Fixed** (PR #20: restricted to specific methods + headers) |
| SEC-M6 | nginx missing CSP, HSTS, Permissions-Policy headers | `frontend/nginx.conf` | **Fixed** (PR #23: CSP, HSTS, X-Frame-Options DENY) |
| SEC-M7 | Helm chart missing all auth/billing secrets (Supabase, Polar, CORS) | `deploy/helm/` | **Fixed** (PR #29: values, secret template, deployment env vars) |

### LOW

| ID | Finding | File | Status |
|----|---------|------|--------|
| SEC-L1 | IP rate limit uses `request.client.host` behind proxy — all users share one bucket | `api/deps.py` | Open |
| SEC-L2 | `X-Session-Id` stored raw without format validation | `core/traces/events.py` | **Fixed** (PR #22: regex `^[0-9a-zA-Z\-_]{1,100}$`) |
| SEC-L3 | `/analytics/popular` limit has no upper bound | `api/routes/analytics.py` | **Fixed** (PR #22: `Query(20, ge=1, le=200)`) |
| SEC-L4 | Dockerfile runs app as root | `Dockerfile` | **Fixed** (already runs as `appuser` non-root since initial Dockerfile) |
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
| LLM-H1 | Raw user queries injected into all LLM prompts (no sanitization, no structural separation) | `query_agent.py`, `search_agent.py`, `reranker.py` | **Fixed** (PR #25: search_agent, PR #29: query_agent + reranker — `wrap_external_content` boundary markers) |
| LLM-H2 | Dataset `question`/`answer` content injected into reranker and evaluator prompts (indirect injection via DB) | `reranker.py`, `search_agent.py` | **Fixed** (PR #25: search_agent, PR #29: reranker — `sanitize_prompt_literal` + `wrap_external_content`) |
| LLM-H3 | `format_description` enables LLM scope creep + triggers RCE via exec() | `agents/export_agent.py` | **Mitigated** (PR #25: exec sandbox prevents RCE; prompt injection risk remains) |
| LLM-H4 | MCP tools have zero auth, rate limits, or quota enforcement | `mcp_server/server.py` | **Fixed** (PR #28: API key auth middleware for HTTP mode) |
| LLM-H5 | MCP collection tools expose all users' data (no user scoping) | `mcp_server/server.py` | **Fixed** (PR #28: collections scoped to authenticated user in HTTP mode) |

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
| ~~3~~ | ~~Enforce auth on MCP HTTP~~ — API key middleware + user scoping on collections | PR #28 |
| ~~4~~ | ~~Startup assertion~~ — ValueError when `auth_enabled=True` + empty JWT secret | PR #27 |
| ~~5~~ | ~~JWT issuer validation~~ — PyJWT `iss` claim check against Supabase URL | PR #27 |
| ~~6~~ | ~~Fix billing webhook~~ — UNIQUE constraint on `polar_customer_id` | PR #27 |
| ~~7~~ | ~~Structural prompt separation~~ — `wrap_external_content` boundary markers on all LLM prompts | PR #25, #29 |
| ~~8~~ | ~~Input length limits~~ — already enforced via Pydantic `max_length` | Existing |
| ~~9~~ | ~~Scope MCP collections~~ — HTTP mode scoped to authenticated user | PR #28 |
| ~~10~~ | ~~Tighten CORS~~ — restricted to specific methods + headers | PR #20 |
| ~~11~~ | ~~Add CSP header~~ + HSTS + X-Frame-Options DENY to nginx | PR #23 |
| ~~12~~ | ~~Add Helm auth secrets~~ — Supabase, Polar, CORS, Qdrant | PR #29 |
| ~~13~~ | ~~Secure Qdrant~~ — API key env var in docker-compose + Helm | PR #29 |
| ~~14~~ | ~~Replace hardcoded DB credentials~~ — env vars in docker-compose, empty REQUIRED in Helm | PR #23, #29 |
| ~~15~~ | ~~Atomic quota increment~~ — SQL `UPDATE...WHERE` with rowcount check | PR #20 |
| ~~16~~ | ~~Analytics auth~~ — `get_optional_user` scoping on `/analytics/stats` | PR #27 |
| ~~17~~ | ~~Container non-root~~ — already runs as `appuser` | Existing |

### Before launch

1. **Add `DELETE /account/me`** endpoint with cascade to curation_events, collections, API keys (GDPR-2)
2. **Add `GET /account/export`** for data portability — all user data as JSON (GDPR-6)
3. **Sign DPAs** with Supabase, Polar.sh, Google, Anthropic (GDPR-5)

### After launch

4. **Move rate limiter** to Redis for multi-worker correctness (SEC-H2)
5. **Add Langfuse instrumentation** to LLM calls for AI Act audit trail (AI-2)
6. **Implement data retention policy** — anonymise curation events older than 24 months (GDPR-7)
