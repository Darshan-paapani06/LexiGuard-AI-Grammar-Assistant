# LexiGuard ✦ — An AI writing assistant with encrypted drafts

A complete, responsive, Grammarly-inspired **original** web application for English writing feedback. Includes a beautiful editorial dashboard, grammar recommendations, one-click correction, an optional local LanguageTool engine, an optional Hugging Face transformer rewrite model, and a password-encrypted draft vault.

> This is an independent academic/developer project, not affiliated with Grammarly. It is a **working local MVP**, not an equivalent to Grammarly's proprietary models or production infrastructure.

## Features

- **Custom modern UI:** responsive sidebar, writing studio, check results, suggestion cards, score and writing statistics, dark mode.
- **Instant analysis:** built-in conservative spelling/grammar/punctuation rules working after the base installation, with explanations and one-click corrections.
- **Deeper analysis (optional):** local LanguageTool checker; requires Java and additional dependencies.
- **AI rewrite (optional):** local transformer seq2seq pipeline (defaults to `vennify/t5-base-grammar-correction`); downloads model weights from Hugging Face on first use; may need significant RAM and CPU time.
- **Cryptography:** AES-256-GCM authenticated encryption at rest, with a different random salt/nonce for each draft and scrypt-derived encryption keys; passphrases are not stored.
- **Local-first:** editor texts are submitted only to this FastAPI server; no third-party writing APIs or tracking scripts. Google Fonts are used as a cosmetic enhancement (self-host fonts for fully offline deployment).
- **Developer-friendly:** Python FastAPI, vanilla JavaScript/CSS, SQLite, tests, API docs at `/docs`.

## Fast setup (Windows / macOS / Linux)

Requires **Python 3.10+**.

```bash
# Extract the ZIP, then open a terminal in its lexiguard_project folder.
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows cmd:
# .venv\Scripts\activate.bat
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in your browser. Enter text, click **Check writing**, review suggestions, and apply edits. To protect a document, click **Encrypt & save** and remember its passphrase. No external API keys are needed for these features.

For Windows, `py -m venv .venv` or `py -m uvicorn ...` may be required instead of `python`.

## Enable the optional ML model

```bash
pip install -r requirements-ml.txt
# Restart the server and click "Rewrite with AI".
```

A supported Hugging Face model is downloaded on first use, so you need an internet connection and enough free memory/disk space. The default is `vennify/t5-base-grammar-correction`; you may override it with `LEXIGUARD_ML_MODEL`. The rewrite is **not automatically applied**: review and confirm it in the preview first. Outputs are probabilistic and can change meaning; do not use them unreviewed for important documents. If the model was moved/removed or its weights are unavailable, choose another compatible text-to-text model and configure `LEXIGUARD_ML_MODEL`.

## Enable optional local LanguageTool

Install **Java** (the supported version depends on the installed LanguageTool package), then:

```bash
pip install -r requirements-language-tool.txt
```

Restart the server, then choose **LanguageTool (optional)** in the writing assistant dropdown. LanguageTool may download additional language data; first-use setup is slower. If dependencies/Java are missing, the UI reports a clear error and you can return to Instant checks.

## Cryptography design

When you save a draft, the server generates a cryptographically random 16-byte salt and 12-byte nonce. The passphrase is processed by scrypt (`N=16384`, `r=8`, `p=1`) to derive a **256-bit key**. AES-GCM encrypts a JSON payload containing both title and body, authenticates the ciphertext, and binds it to the draft ID as authenticated associated data (AAD). The SQLite database stores ciphertext, salt, nonce, random draft ID, and timestamp — **not the key or passphrase**. Opening a draft requires the original passphrase. Wrong passwords fail authentication. Losing the passphrase means losing access.

**Threat model / limits:** encrypted data at rest against someone who obtains only the database. This is a **single-user local demo**, not a hosted multi-user service. The vault listing and deletion endpoints have no login, so anyone with network access to the API could view IDs or delete drafts. The server receives the passphrase and plaintext over HTTP; run on localhost only, use HTTPS for deployment, and add real authentication, user ownership, authorization, rate limiting, secret management, backups, and operational hardening before a public launch. A short passphrase is susceptible to offline guessing if the DB is stolen; choose a long passphrase. Deletion is not guaranteed secure erasure from SQLite/journal/backups. The application does **not** provide end-to-end or zero-knowledge encryption.

## Project structure

```
lexiguard_project/
├── backend/
│   ├── main.py           FastAPI endpoints + static frontend
│   ├── engine.py         Conservative rules + optional LanguageTool
│   ├── ml.py             Optional Hugging Face rewrite pipeline
│   └── secure_store.py   AES-256-GCM + scrypt + SQLite
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── app.js
│       ├── styles.css
│       ├── logo.svg
│       └── favicon.svg
├── tests/
│   └── test_project.py
├── docs/
│   └── architecture.md
├── requirements.txt
├── requirements-ml.txt
└── requirements-language-tool.txt
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Analyze text; `engine` = `built-in` or `languagetool` |
| POST | `/api/rewrite` | Optional local transformer rewrite |
| POST | `/api/vault` | Encrypt and save document |
| GET | `/api/vault` | List encrypted draft identifiers |
| POST | `/api/vault/{id}/unlock` | Decrypt a draft using a passphrase |
| DELETE | `/api/vault/{id}` | Delete a draft |
| GET | `/docs` | Swagger interactive API documentation |

Example analyze request:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
 -H 'Content-Type: application/json' \
 -d '{"text":"i dont recieve teh message", "engine":"built-in"}'
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Roadmap for a production-quality Grammarly competitor

1. Replace simplistic numeric score with calibrated readability, grammaticality, and writing-quality metrics.
2. Fine-tune/evaluate a sequence-to-sequence grammar error correction model on **licensed** datasets and benchmark with GLEU / ERRANT / human reviews; avoid unlicensed model/data usage.
3. Map neural corrections to precise text-span suggestions, handle long documents and paragraphs, and reduce overcorrection and hallucinations.
4. Add user accounts, authentication, per-user draft access, zero-knowledge client-side encryption if required, HTTPS, audit controls, CSRF/CORS policy, and rate limiting.
5. Add model inference queue, GPU serving, caching where privacy permits, monitoring, accessibility and end-to-end UI tests, and consent-aware analytics.

**License:** MIT (see LICENSE).
