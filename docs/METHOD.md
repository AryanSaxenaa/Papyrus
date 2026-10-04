# Method (plain language)

Papyrus resolves each bibliography entry against several scholarly indexes, then applies claim–evidence alignment (NLI) for evidentiary citations.

**Google Scholar via SerpApi** is an additional *witness*, not a sole authority:

- `google_scholar` — does a similar title exist?
- `google_scholar_cite` — does Scholar’s canonical citation string disagree on authors/year/venue?
- `google_scholar_author` — positive-only: does the author’s profile list this title?

**One-sided rules:** a Scholar hit can prevent a false “DOI not found” verdict; a miss or missing author profile is **unknown**, never proof of fabrication.

Every SerpApi call records a receipt (`search_metadata.id`, redacted params, credits). Export `GET /api/audits/{id}/bundle.zip` and run `verify.py` inside the bundle offline.
