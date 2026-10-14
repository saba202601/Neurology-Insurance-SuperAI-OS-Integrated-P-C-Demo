# Neurology Insurance SuperAI-OS — Synthetic P&C Demonstration

**Purpose:** small runnable proof of concept, NOT a regulated insurer production system.

## Modules
- Orchestration dashboard with an auditable dry-run
- Canonical elements, picklists, synonyms, policy/claims/billing sample records
- Ten deterministic business rules and policy-level evaluation
- Florida HO3 simplified rating and synthetic forms
- Fictional CSV statistical reporting export (NOT a bureau-approved layout)
- Explainable fuzzy mapping proposals with manual approval and audit
- Data validation exceptions and audit events

## Run locally
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
SQLite database `demo.sqlite` is created on the first run. Click **Reset synthetic demo database** to restore five sample policies. No keys, logins or client data needed.

## Tests
```bash
python -m pytest -q tests
```
Install `pytest` separately for testing if needed.

## Deploy to Streamlit Community Cloud
Create a GitHub repository with these files at the repository root, choose `app.py` as entrypoint, and deploy. This package does **not** deploy itself or create a live URL. On shared cloud hosting, SQLite data is ephemeral; not multiuser-safe for persistent approvals.

## Security, compliance and implementation limitations
- All data, rates, business rules, forms and bureau layouts are synthetic. No regulatory compliance or rate accuracy is claimed.
- Approval is a *demo* button; it is not production identity-backed SME approval. Add SSO, RBAC, immutable audit logs, separation of duties, secrets management, encryption and transaction controls before client use.
- No live LLM, no external APIs, no actual policy issuance, ledger postings or statutory filing.
- For SQL Server: implement approved SQL Server drivers, migrations and transaction handling; the bundled code runs on SQLite only.
- Any carrier integration needs security/legal authorization and a development sandbox before use.
