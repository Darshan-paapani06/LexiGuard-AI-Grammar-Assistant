










<div align="center"><img src="docs/images/animated-title.gif" width="100%" alt="LexiGuard animated writing correction header." /><img src="docs/images/hero-banner.png" width="100%" alt="LexiGuard branded hero art." />
✦ LexiGuard — AI Grammar & Writing Assistant
A Grammarly-inspired writing studio with local-first grammar checks, optional AI rewriting, and encrypted drafts.






Features · Demo · Get Started · AI Models · Cryptography · API

Project status: Functional local MVP / learning project. It is not an official Grammarly product and does not claim to match Grammarly's production models or service.

</div>
🎬 Live demo
<div align="center"> <img src="docs/images/animated-title.gif" alt="Animated example of LexiGuard typing and correcting English grammar." width="840" /> <p><em>Type → analyze → review suggestions → apply corrections.</em></p> <img src="docs/images/demo.gif" alt="Screen recording of the actual LexiGuard writing editor using the built-in grammar engine." width="960" /> </div>
The animated editor demo uses the real LexiGuard frontend and example responses from the built-in rule engine. Optional transformer inference is not shown in the demo.

✨ Features
Capability	What it does	Availability
✍️ Writing studio	Minimal editor with document controls, sample text, and dark theme	Included
📝 Grammar & spelling	Rule-based spelling, grammar, punctuation, and clarity suggestions	Included
⚡ One-click fixes	Apply suggestions individually or all together	Included
📈 Writing insights	Word/character counts, reading estimate, sentence statistics, and heuristic score	Included
🧠 Transformer rewrite	Optional Hugging Face text-to-text model to propose a whole-text correction	Optional install
🔎 LanguageTool	Optional deeper grammar checks using a locally installed LanguageTool engine	Optional Java + install
🔐 Encrypted vault	Password-protected drafts with scrypt key derivation and AES-256-GCM encryption at rest	Included
🖥️ Local-first backend	FastAPI HTTP service with built-in Swagger documentation	Included
Why cryptography? Good writing tools should give users meaningful control over their private drafts. LexiGuard adds a local encrypted storage demonstration alongside the editing workflow.

🖼️ Interface preview
<div align="center"> <img src="docs/images/studio-light.png" alt="LexiGuard light theme: editor, grammar suggestions and writing insights." width="920" /> <p><sub>Writing studio · Light mode</sub></p> <img src="docs/images/studio-dark.png" alt="LexiGuard dark theme writing editor." width="920" /> <p><sub>Writing studio · Dark mode</sub></p> </div>
🚀 Quick start
Prerequisites: Python 3.10+, pip, and a modern browser. The built-in grammar checker does not need an API key, an external model, or Java.

Windows PowerShell — from the folder containing backend/ and frontend/:

py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
macOS / Linux:

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
Open http://127.0.0.1:8000 in your browser, paste an English paragraph, and press Check writing. Explore the API at http://127.0.0.1:8000/docs.

On Windows, if PowerShell blocks script activation, use Command Prompt with .venv\Scripts\activate.bat or run the venv's Python executable directly. Don't change system-wide PowerShell policies just for this project.

🤖 Optional advanced language models
1) Transformer-based rewriting
python -m pip install -r requirements-ml.txt
Restart the server and choose Rewrite with AI. The default model setting is vennify/t5-base-grammar-correction (configurable with LEXIGUARD_ML_MODEL). The first use downloads model weights, so allow additional storage/RAM and an internet connection. Verify that your chosen model remains available and is compatible with the installed transformer pipeline.

Important: The UI shows a proposed rewrite for review; it does not silently replace the draft. Generative outputs can change the meaning of a sentence and should be checked.

2) LanguageTool checking
Install a compatible Java runtime, then install the separate optional package:

python -m pip install -r requirements-language-tool.txt
Restart the server and select LanguageTool (optional) in the editor. This is a local optional component, not a paid or remote Grammarly API. The first launch may fetch language resources.

🔐 Cryptography & security
<div align="center"> <img src="docs/images/crypto-flow.svg" alt="Diagram of encryption: passphrase, scrypt derived key, AES-256-GCM and ciphertext stored in SQLite." width="920" /> </div>
The draft vault uses:

A random 16-byte salt and random 12-byte nonce per saved draft.
scrypt (N=16384, r=8, p=1) to derive a 256-bit key from the user's passphrase.
AES-256-GCM authenticated encryption for the draft title and body, with the draft ID used as associated authenticated data (AAD).
SQLite to store ciphertext, salt, nonce, draft ID, and creation time — not passphrases or encryption keys.
Decrypting a draft requires the original passphrase, which cannot be recovered by the application if lost.

[!WARNING]
Security scope: This is a single-user localhost demonstration, not a production multi-user vault. The backend receives plaintext and passphrases; it is not zero-knowledge or end-to-end encryption. Vault list/delete endpoints lack per-user authentication and authorization. Do not expose the server publicly or use it to store sensitive production information without HTTPS, authentication, access controls, rate limits, backups, and a proper security review.

🏗️ Architecture
Project structure
lexiguard_project/
├── backend/
│   ├── main.py                  # FastAPI routes and static app
│   ├── engine.py                # Built-in checks + optional LanguageTool
│   ├── ml.py                    # Optional transformer text rewriting
│   └── secure_store.py          # scrypt, AES-GCM and SQLite
├── frontend/
│   ├── index.html
│   └── assets/                 # JavaScript, CSS, logo and favicon
├── docs/
│   ├── architecture.md
│   ├── GITHUB_PUBLISHING.md
│   └── images/                 # Banner, screenshots, diagrams, GIFs
├── scripts/
│   └── publish-github.ps1
├── tests/
│   └── test_project.py
├── requirements.txt
├── requirements-ml.txt
├── requirements-language-tool.txt
└── README.md
🔌 API reference
Method	Route	Use
GET	/api/health	Server health
POST	/api/analyze	Built-in or LanguageTool grammar analysis
POST	/api/rewrite	Optional local transformer rewrite
POST	/api/vault	Encrypt and store a draft
GET	/api/vault	List encrypted draft IDs
POST	/api/vault/{id}/unlock	Unlock a draft with its passphrase
DELETE	/api/vault/{id}	Delete an encrypted draft
GET	/docs	Interactive OpenAPI reference
Example:

curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"i dont recieve teh message.","engine":"built-in"}'
🧪 Tests
python -m unittest discover -s tests -v
The bundled tests cover representative grammar rules, secure draft encryption/decryption, and API behavior. They are not a replacement for production security, browser, and load tests.

🗺️ Roadmap

Responsive original writing studio + custom logo

Built-in grammar checker with one-click fixes

Password-encrypted SQLite draft vault

Optional local LanguageTool and transformer integration hooks
Fine-tune and evaluate a dedicated grammar-correction model on properly licensed data
Add precise model correction spans, long-document support, and improved linguistic evaluation
Add identity, user-specific vault access, HTTPS, rate limits, and deployment security
Add browser extension, document import/export, and integration tests
🧑‍💻 Publishing to GitHub
The full commands are in GITHUB_PUBLISHING.md. A Windows PowerShell helper is included at scripts/publish-github.ps1.

📜 License & attribution
Released under the MIT License. Built as an independent student/developer project inspired by the category of writing assistants. Not affiliated with, endorsed by, or a copy of Grammarly's protected software or branding.

<div align="center"> <sub>✦ LexiGuard · Write brilliantly. Privately.</sub> </div>




