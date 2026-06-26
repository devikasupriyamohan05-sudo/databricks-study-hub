# Databricks DE Associate — Intern Study Hub 🦆

A study app for the **Databricks Certified Data Engineer Associate** exam
(July 25, 2025 outline). Built on top of the original self-contained study hub,
now with flashcards, learning games, an AI tutor, and a Feed-the-Duck XP system.

## What's inside

- **Notes + quizzes** for all 5 official sections (unchanged, original content).
- **Flashcards** — 50 cards derived straight from the section notes, with a
  spaced-repetition flow (Again / Hard / Good / Easy) and mastery tracking.
- **Games**
  - 🎯 **Jeopardy** — pick a section and point value; answer to bank points.
  - ⌨️ **Fill the blank / complete the code** — type the missing term or keyword.
- 🦆 **Feed-the-Duck XP** — every correct answer feeds your duck. It earns XP,
  levels up (Duckling → Data Duck 👑), and tracks streaks across everything.
- 🤖 **AI Tutor** — ask anything, grounded in the exam notes; explains any quiz
  question you got wrong. Says when it's unsure instead of inventing facts.
- **Progress saves locally** per intern. A shared leaderboard can be added later
  (see below) without a rewrite.

## Two ways to run it

### 1. Standalone (zero setup, fully free, no AI)
Open **`Databricks DE Associate - Study Hub.html`** in any browser. Everything
works except the live AI tutor (which needs the hosted version). Share the file
with the other interns — each person's progress saves in their own browser.

To regenerate it after editing content or the template:
```bash
python build_standalone.py
```

### 2. Hosted on Streamlit Community Cloud (free, adds the AI tutor)
This is the recommended setup for the whole intern group + working AI.

**Run locally first (optional):**
```bash
pip install -r requirements.txt
# add your token:
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit it
streamlit run streamlit_app.py
```

**Deploy free:**
1. Create a **public** GitHub repo and push these files:
   `streamlit_app.py`, `ai_tutor.py`, `app_template.html`, `content.json`,
   `requirements.txt`, `build_standalone.py`, `README.md`.
   (Do **not** commit `.streamlit/secrets.toml` — `.gitignore` already blocks it.)
2. Go to **https://share.streamlit.io**, sign in with GitHub, **New app**,
   pick the repo, main file = `streamlit_app.py`, **Deploy**.
3. In the app's **Settings → Secrets**, paste:
   ```toml
   GITHUB_TOKEN = "ghp_your_token_here"
   ```
   Save — the app restarts and the AI tutor turns on.

You'll get one shared URL all interns can open. Progress is still per-browser.

> Streamlit Community Cloud is free but requires a **public** repo. Keep the
> token only in Secrets — never in the code or repo.

## The AI tutor (free) — how it's wired

- Uses **GitHub Models** (free, OpenAI-compatible). Limits are roughly **10
  requests/min and ~50/day** on top models — fine for studying.
- The token lives in **`st.secrets` on the server**. It is never sent to the
  browser, which also sidesteps browser CORS limits — that's why the tutor is a
  Streamlit sidebar panel rather than a client-side call.
- Get a token at **https://github.com/settings/tokens** (Models access is enough).
- **Graceful fallback:** with no token, the tutor shows a short setup note and
  the rest of the app is unaffected.

### Grounding (no hallucinated study content)
The tutor is fed the hub's own section notes (from `content.json`, which follows
the official outline) and is instructed to stay within those topics and say when
it's unsure. Flashcards and fill-in-the-blank answers are derived directly from
the notes — nothing is invented.

## Turning on a shared leaderboard later

v1 keeps each intern's XP in their own browser. To make it shared and free:

1. Create a free **Supabase** project; add a table:
   ```sql
   create table scores (
     name text primary key,
     xp int not null,
     updated_at timestamptz default now()
   );
   alter table scores enable row level security;
   create policy "anyone upsert" on scores for all using (true) with check (true);
   ```
2. In `app_template.html`, implement the `Leaderboard.submit()` / `fetch()` stub
   (search for **"LEADERBOARD (pluggable stub)"**) to upsert/read that table with
   the Supabase anon key. Call `Leaderboard.submit(state.name, state.xp)` from
   `Duck.feed`.

Scores are honor-system (a client key can be read), which is fine for a friendly
intern competition.

## File map

| File | Purpose |
|---|---|
| `Databricks DE Associate - Study Hub.html` | Standalone app (generated) — open directly |
| `app_template.html` | UI template (`__CONTENT_JSON__` injected at build/serve time) |
| `content.json` | Single source of truth: notes, quizzes, flashcards, fill-blanks |
| `streamlit_app.py` | Hosted wrapper + AI tutor sidebar |
| `ai_tutor.py` | GitHub Models call + grounding |
| `build_standalone.py` | Inlines content → standalone HTML |
| `requirements.txt` / `.streamlit/secrets.toml.example` | Deploy config |

Always cross-check topics against the
[official exam guide](https://www.databricks.com/learn/certification/data-engineer-associate).
