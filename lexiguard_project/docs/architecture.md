# Architecture and security decisions

Browser (vanilla JS + HTML + CSS) → same-origin FastAPI application → grammar engine / optional transformer / encrypted SQLite vault.

- `POST /api/analyze`: deterministic rule engine by default; LanguageTool optional and local; suggestions contain zero-based character `start`/`end` offsets and replacements.
- `POST /api/rewrite`: only invoked by user action; optional Transformers pipeline loaded lazily and cached in process; original text is preserved until the user approves the candidate.
- `POST /api/vault`: JSON title and body are encrypted together using password-derived AES-256-GCM. New salt and nonce per save. DB row ID used as authenticated additional data. No password recovery.
- Frontend escapes all displayed user text by creating text nodes; it never writes untrusted suggestions or draft content with `innerHTML`.
- Rule matches are conservative; the app does not claim a flawless proofread or an authoritative linguistics score. The score is a convenience heuristic, not a scientifically validated metric.

For public deployment, implement auth, authorization on all vault operations, HTTPS, per-user secrets, abuse control, model sandboxing and dedicated secrets policy before storing sensitive data. Base app intentionally binds to localhost in README.
