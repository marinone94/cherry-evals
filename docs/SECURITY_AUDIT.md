# Cherry Evals — Security, Privacy & Compliance Audit

**Date**: 10 March 2026
**Scope**: Full application (backend, frontend, agents, MCP, infrastructure, legal)
**Status**: Pre-deployment review

---

## Executive Summary

**46 findings** across security, LLM exploitation, frontend, and compliance.
**4 Critical**, **11 High**, **12 Medium**, **9 Low**, **10 compliance gaps**.

The two most severe issues are:
1. **Remote code execution** via `exec()` with full `__builtins__` in the ingestion and export agents
2. **IDOR** on `DELETE /collections/{id}/examples/{id}` (missing ownership check)

Both must be fixed before any public-facing deployment.

---

## 1. Security Vulnerabilities

### CRITICAL

| ID | Finding | File | Impact |
|----|---------|------|--------|
| SEC-C1 | MCP HTTP mode has no enforced auth — `_resolve_user_from_api_key()` defined but never called | `mcp_server/server.py:60-78` | Full unauthenticated access to all data + LLM credits |
| SEC-C2 | IDOR: `remove_example` skips `_check_collection_ownership()` | `api/routes/collections.py:249` | Any user can delete any other user's collection examples |
| SEC-C3 | Billing webhook matches user by email (not unique column); should use `polar_customer_id` after first event | `api/routes/billing.py:63` | Wrong user could be tier-upgraded/downgraded |
| SEC-C4 | Hand-rolled JWT validation does not check `iss`, `aud`, `nbf` claims | `api/deps.py:76-118` | Tokens from other services sharing the same secret are accepted |
| SEC-C5 | Empty `supabase_jwt_secret` defaults to `""` — trivially forgeable JWTs | `api/deps.py:97`, `config.py:41` | Full auth bypass if operator forgets to set env var |

### HIGH

| ID | Finding | File |
|----|---------|------|
| SEC-H1 | `check_collection_example_limit` does not verify collection ownership | `api/deps.py:370-394` |
| SEC-H2 | In-memory rate limiter not shared across workers | `api/deps.py:239-271` |
| SEC-H3 | Analytics endpoints (`/analytics/stats`, `/popular`, `/co-picked`) fully unauthenticated, leak user query history | `api/routes/analytics.py` |
| SEC-H4 | Internal exception details leaked to clients (`str(e)` in HTTPException) | `api/routes/search.py:105`, `export.py:103` |
| SEC-H5 | Qdrant running without auth, ports published to host in docker-compose | `docker-compose.yml:19-31` |
| SEC-H6 | Hardcoded `cherry/cherry` DB credentials in docker-compose and Helm values | `docker-compose.yml:5-8`, `values.yaml:24-25` |

### MEDIUM

| ID | Finding | File |
|----|---------|------|
| SEC-M1 | Qdrant collection name from user input — no allowlist validation | `api/models/search.py:55,69` |
| SEC-M2 | `sort_by` parameter not validated against allowed values | `api/models/search.py:17` |
| SEC-M3 | `Content-Disposition` filename not sanitized — header injection risk | `api/routes/export.py:127`, `agents.py:211` |
| SEC-M4 | Daily quota TOCTOU race condition (read-then-write without lock) | `api/deps.py:279-338` |
| SEC-M5 | CORS: `allow_credentials=True` with `allow_methods=["*"]`, `allow_headers=["*"]` | `api/main.py:28-34` |
| SEC-M6 | nginx missing CSP, HSTS, Permissions-Policy headers | `frontend/nginx.conf:27-31` |
| SEC-M7 | Helm chart missing all auth/billing secrets (Supabase, Polar, CORS) | `deploy/helm/cherry-evals/templates/secret.yaml` |

### LOW

| ID | Finding | File |
|----|---------|------|
| SEC-L1 | IP rate limit uses `request.client.host` behind proxy — all users share one bucket | `api/deps.py:246` |
| SEC-L2 | `X-Session-Id` stored raw without format validation | `core/traces/events.py:32` |
| SEC-L3 | `/analytics/popular` limit has no upper bound | `api/routes/analytics.py:23` |
| SEC-L4 | Dockerfile runs app as root | `Dockerfile` |
| SEC-L5 | Agentic ingestion may execute LLM-generated code (see LLM section) | `api/routes/agents.py:118` |

---

## 2. LLM Exploitation Vulnerabilities

### CRITICAL

| ID | Finding | File | Impact |
|----|---------|------|--------|
| LLM-C1 | `exec()` with full `__builtins__` on LLM-generated ingestion parser code | `agents/ingestion_agent.py:96-111` | **Remote code execution** — attacker-controlled description → Gemini → exec'd code with open(), __import__(), os, subprocess |
| LLM-C2 | `exec()` with full `__builtins__` on LLM-generated export converter code | `agents/export_agent.py:110-134` | **Remote code execution** — `format_description` prompt injection → exec'd code |

### HIGH

| ID | Finding | File |
|----|---------|------|
| LLM-H1 | Raw user queries injected into all LLM prompts (no sanitization, no structural separation) | `query_agent.py:36`, `search_agent.py:341,375`, `reranker.py:41` |
| LLM-H2 | Dataset `question`/`answer` content injected into reranker and evaluator prompts (indirect injection via DB) | `reranker.py:27-42`, `search_agent.py:365-373` |
| LLM-H3 | `format_description` enables LLM scope creep + triggers RCE via exec() | `agents/export_agent.py:206-208` |
| LLM-H4 | MCP tools have zero auth, rate limits, or quota enforcement | `mcp_server/server.py` |
| LLM-H5 | MCP collection tools expose all users' data (no user scoping) | `mcp_server/server.py:342-549` |

### MEDIUM

| ID | Finding | File |
|----|---------|------|
| LLM-M1 | HuggingFace sample rows embedded in Gemini prompt — dataset poisoning → RCE chain | `agents/ingestion_agent.py:309-313` |
| LLM-M2 | No content validation/sanitization on ingested dataset rows | All ingestion adapters |
| LLM-M3 | No length limits on `format_description` or `description` fields sent to LLMs | `api/routes/agents.py:45-50` |
| LLM-M4 | LLM-supplied HuggingFace dataset ID passed to `load_dataset()` without allowlisting | `agents/ingestion_agent.py:247-266` |

### LOW

| ID | Finding | File |
|----|---------|------|
| LLM-L1 | LLM reasoning fields (`explanation`, `assessment`, `rationale`) returned unfiltered — system prompt leakage risk | `api/routes/search.py:242`, `search_agent.py:214` |

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

### Immediate (before any public access)

1. **Fix `exec()` sandbox** in `ingestion_agent.py` and `export_agent.py` — replace `__builtins__` with strict allowlist
2. **Fix IDOR** on `DELETE /collections/{id}/examples/{id}` — add `_check_collection_ownership()`
3. **Enforce auth on MCP tools** or document that MCP HTTP must never be publicly exposed
4. **Add startup assertion** that `supabase_jwt_secret` is non-empty when `auth_enabled=True`
5. **Replace hand-rolled JWT** with PyJWT library (validates `iss`, `aud`, `nbf`)

### Before launch

6. **Add `DELETE /account/me`** endpoint with cascade to curation_events, collections, API keys
7. **Add `GET /account/export`** for data portability (all user data as JSON)
8. **Add input length limits** on all user strings sent to LLMs (`max_length=2000`)
9. **Add structural prompt separation** (XML tags for user data, system instructions in `system` role)
10. **Fix billing webhook** to use `polar_customer_id` for returning subscribers + add UNIQUE on email
11. **Add CSP header** to nginx config
12. **Scope MCP collections** to authenticated user
13. **Sign DPAs** with Supabase, Polar.sh, Google, Anthropic

### After launch

14. **Move rate limiter** to Redis for multi-worker correctness
15. **Atomic quota increment** (SQL `UPDATE ... WHERE ... RETURNING`)
16. **Add Langfuse instrumentation** to LLM calls for AI Act audit trail
17. **Implement data retention policy** — anonymise curation events older than 24 months
18. **Run container as non-root** user
19. **Secure Qdrant** with API key in docker-compose and Helm
