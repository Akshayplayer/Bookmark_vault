# Bookmark Vault

## 1. Project aim

Learn full stack development by building a small end-to-end deployed app, Bookmark Vault (a bookmark manager: React + Vite frontend, FastAPI backend, PostgreSQL). The user types the code; Claude guides, reviews, explains.

Stack: React + Vite (frontend, not started), Python + FastAPI + Uvicorn (backend), PostgreSQL 18 on local port 5432 via SQLAlchemy 2.x and psycopg 3, python-dotenv for config, Pydantic 2 for schemas.

## 2. For Claude: start here

Session rules:
- Guide step by step. Do not write or fix the user's code unless they ask.
- If the user asks for a sample, show the code in chat, not in files.
- Explain the why behind each step.
- Read the user's files to review them.
- Run `/check` after each step; it verifies the code and updates this README
- The user is on Windows 11 with PowerShell; use PowerShell syntax.

Current step: **Step 5, Auth (password hashing + JWT): implemented, pending manual verification of the two-user test. One item left in code: the shared URL validator.**

Re-check on 2026-11-08: all backend files pass `py_compile` (which cannot catch runtime bugs; nothing was run against the server). Since 2026-11-05 only small edits happened (`auth.py` got two debug `print` calls in `get_current_user`; `main.py` PUT now uses a `required = {"title", "url"}` set). **None of the open items is done yet:** shared `normalize_url()` (still the naive validator in both schemas), email lowercasing on register/login (`data.email` / `form.username` are used as-is), CORS (no `CORSMiddleware` in `main.py`), and the manual two-user test (no confirmation in this README). `frontend/` is still empty.

Status (details as of 2026-11-05, still accurate except where noted above):
- `auth.py`: `hash_password`/`verify_password` (pwdlib `PasswordHash.recommended()`, argon2), `create_access_token(user_id)` (PyJWT, HS256, `sub` = user id as string, `exp` = 60 minutes), `OAuth2PasswordBearer(tokenUrl="login")`, and the `get_current_user` dependency (decodes token, 401 on invalid/expired token or unknown user). Raises `RuntimeError` at import if `SECRET_KEY` is missing.
- `schemas.py`: `UserCreate` (`EmailStr`, password min 8), `UserOut` (id, email), `Token`. `owner_id` is gone from `BookmarkCreate`. The URL validators are still the naive "prepend `https://` if no scheme" version in both `BookmarkCreate` and `BookmarkUpdate` (so `https//x.com` becomes `https://https//x.com` and `javascript:` links are accepted); no shared `normalize_url()` yet.
- `main.py`: `/register` (400 if email exists, stores the argon2 hash) and `/login` (`OAuth2PasswordRequestForm`; the `username` field holds the email; same 401 message for unknown email and wrong password). All five bookmark routes take `current_user = Depends(auth.get_current_user)`; create sets `owner_id=current_user.id`; list filters by owner; get/put/delete return 404 for missing or not-owned bookmarks (None check first, then owner check).
- `backend/.env` has the keys `DATABASE_URL` and `SECRET_KEY` (values not recorded here). `requirements.txt` includes `pwdlib`, `argon2-cffi`, `PyJWT`, `email-validator`, `python-multipart`.
- The old POST owner-exists check (and its `details=` typo) was removed together with `owner_id`; no longer relevant.
- Existing rows created before auth may belong to the manual test user (id 1, hashed_password `x`), who cannot log in.

Last thing finished: the auth module, `/register` and `/login`, protected and owner-scoped bookmark routes, `owner_id` passed from the token, `EmailStr`, and the `SECRET_KEY` startup guard.

Blockers: none (nothing blocks progress; the open items below are simply not started).

Open items for step 5 (checked against the code on 2026-11-08):
- Shared `normalize_url()`: not done.
- Email lowercasing in `/register` and `/login` (e.g. `.strip().lower()`, or a validator on `UserCreate.email`): not done, so `A@x.com` and `a@x.com` would be two accounts and login is case-sensitive.
- PUT with `"title": null`: current behavior is to silently ignore it and return 200 (the `required` set skips `None` for title/url). Decide whether to keep that or return 422; either is fine, but make it a conscious choice.
- Remove the two debug `print(payload)` / `print(user_id)` lines from `get_current_user` in `auth.py` (they write token contents to the server log).
- CORS for `http://localhost:5173`: not done (needed before React can call the API).
- Manual two-user test: not confirmed.

Next action (one thing): replace the naive URL validators with one shared `normalize_url()` using `urllib.parse.urlparse` (reject `https//x.com` and non-http(s) schemes such as `javascript:`; add `https://` only when there is no scheme), used by both `BookmarkCreate` and `BookmarkUpdate`. Then do the manual two-user test in `/docs` (register A and B, log in as each, create a bookmark as A, confirm B gets 404 on it and does not see it in the list, and that no token gives 401). Then tick step 5 and start Step 6.

Goal of next session: finish step 5 (URL validator, email lowercasing, remove debug prints, the two-user test), then Step 6: React frontend with Vite, and add CORS middleware in FastAPI allowing `http://localhost:5173`.

## 3. Quick start (PowerShell)

```powershell
# Postgres service (name may be postgresql-x64-18)
Get-Service *postgres*
Start-Service postgresql-x64-18            # if stopped (may need admin)

# Open the database
psql -U postgres -h localhost # to just open the databases and create new data bases in it.

psql -U postgres -h localhost -d bookmark_vault
#   SQL statements must end with ;   e.g. SELECT * FROM users;
#   \dt           list tables
#   \d bookmarks  describe a table
#   \q            quit
#   prompt shows -#  -> you forgot the ; , type ; and Enter

# Backend
cd backend
python -m venv venv                        # first time only
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload                  # run from backend/
```

- API: http://127.0.0.1:8000/ and interactive docs at http://127.0.0.1:8000/docs
- Frontend (upcoming, not created yet): `cd frontend; npm install; npm run dev`.

Find and stop servers on port 8000:

```powershell
netstat -ano | findstr :8000               # last column is the PID
Stop-Process -Id <pid> -Force              # or Ctrl+C in the uvicorn terminal
```

Git basics:

```powershell
git status
git add .
git commit -m "message"
git log --oneline
```

`backend/.env` (git-ignored, never commit). Variable names, with placeholder values:

```
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/bookmark_vault
SECRET_KEY=PASTE_GENERATED_VALUE_HERE
```

Generate a `SECRET_KEY` (the app refuses to start without it):

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Using auth in `/docs` (http://127.0.0.1:8000/docs):
1. `POST /register` with `{"email": "a@example.com", "password": "at-least-8-chars"}` (returns 201).
2. Click **Authorize** (top right). Enter the email in the `username` field and the password in `password`. Leave `client_id` and `client_secret` blank (they are unused). Click Authorize, then Close.
3. Call any `/bookmarks` route; the padlock means a Bearer token is sent. To test as another user, click Authorize, Logout, and log in as that user.
Alternatively, `POST /login` returns `access_token`; send it as the header `Authorization: Bearer <token>`.

Prerequisites: Python 3, PostgreSQL 18 on port 5432 with `psql` on PATH, a database named `bookmark_vault` (`CREATE DATABASE bookmark_vault;`), Node.js for later.

The old manual test user (id 1, run in psql before auth existed) is no longer needed; use `/register` instead.

## 4. Progress

- [x] 1. Setup (folders, git, `.gitignore`, venv, Postgres installed, `bookmark_vault` database created)
- [x] 2. FastAPI hello world (`GET /`, `/docs`)
- [x] 3. Database + models (`database.py`, `models.py`, `create_all`; test user inserted into `users`, so the tables exist)
- [x] 4. Bookmark CRUD API (code complete; the POST owner check was replaced by auth in step 5)
  - [x] Pydantic schemas (`BookmarkCreate`, `BookmarkUpdate`, `BookmarkOut`)
  - [x] `POST /bookmarks` (201)
  - [x] `GET /bookmarks` (list)
  - [x] `GET /bookmarks/{bookmark_id}` (404 if missing)
  - [x] `PUT /bookmarks/{bookmark_id}` (partial update with `exclude_unset`)
  - [x] `DELETE /bookmarks/{bookmark_id}` (204)
  - [x] `tag` and `q` query filters on the list route
  - [x] Owner-exists check on POST (removed in step 5: the owner now comes from the token, so it is no longer needed)
  - [x] Null-title/url handling in PUT (`continue` skips `None` for required fields; `note`/`tag` can be cleared)
  - [x] Pydantic `Field` length limits and `https://` URL validator in `schemas.py`
  - [x] `GET /bookmarks` ordered by `created_at` descending
- [ ] 5. Auth (password hashing + JWT) (implemented, pending manual verification of the two-user test)
  - [x] Password hashing (`hash_password`/`verify_password`, argon2 via pwdlib)
  - [x] `POST /register`
  - [x] `POST /login` + JWT (`create_access_token`, HS256, 60 min)
  - [x] `get_current_user` dependency (`OAuth2PasswordBearer`)
  - [x] Owner taken from the token (`owner_id=current_user.id` in `create_bookmark`)
  - [x] Queries scoped to the current user (list filter; 404 on get/put/delete for not-owned)
  - [x] `owner_id` removed from `BookmarkCreate`
  - [x] `SECRET_KEY` startup guard (`RuntimeError` in `auth.py`)
  - [x] `EmailStr` on `UserCreate`/`UserOut`
  - [ ] Shared URL validation with `urllib.parse` (both schemas still use the naive prepend-`https://` validator; re-checked 2026-11-08)
  - [ ] Email lowercasing on register/login (not in code)
  - [ ] Decision on PUT with null title (currently silently ignored, returns 200; decide keep vs 422)
  - [ ] Remove debug `print` calls in `get_current_user`
  - [ ] CORS middleware for `http://localhost:5173` (not in `main.py`)
  - [ ] Manual two-user test in `/docs` (not confirmed by the user in this README)
- [ ] 6. React basics
- [ ] 7. React features
- [ ] 8. Polish and tests
- [ ] 9. Deploy

## 5. Project structure

```
bookmark-vault/
├── .gitignore
├── README.md
├── backend/
│   ├── .env              # git-ignored, holds DATABASE_URL and SECRET_KEY
│   ├── auth.py           # password hashing, JWT creation, get_current_user
│   ├── database.py       # engine, SessionLocal, Base, get_db
│   ├── main.py           # FastAPI app, create_all, health check, bookmark routes, /register, /login
│   ├── models.py         # User and Bookmark tables (SQLAlchemy)
│   ├── schemas.py        # Bookmark*, UserCreate / UserOut / Token (Pydantic)
│   └── requirements.txt  # UTF-8 (BOM)
└── frontend/             # empty so far
```

(`venv/`, `__pycache__/`, `node_modules/`, `.git/` omitted.)

## 6. Architecture and data

Flow: React (browser) -> HTTP/JSON -> FastAPI (Uvicorn) -> SQLAlchemy -> PostgreSQL. Only the FastAPI -> SQLAlchemy -> Postgres side exists so far. Protected routes expect the header `Authorization: Bearer <JWT>`.

API endpoints (only those in code):

| Method | Path | Description | Bearer token? | Status codes |
| ------ | ---- | ----------- | ------------- | ------------ |
| GET    | `/` | Health check, returns `{"status": "ok"}` | No | 200 |
| POST   | `/register` | Create a user (body: email, password min 8); returns id and email | No | 201, 400 (email taken), 422 |
| POST   | `/login` | Form body `username` (the email) and `password`; returns `{access_token, token_type: "bearer"}` | No | 200, 401, 422 |
| POST   | `/bookmarks` | Create a bookmark for the current user (body: title, url, note?, tag?); URL gets `https://` if no scheme | Yes | 201, 401, 422 |
| GET    | `/bookmarks` | List the current user's bookmarks, newest first; optional `?tag=` (exact) and `?q=` (title contains, case-insensitive) | Yes | 200, 401 |
| GET    | `/bookmarks/{bookmark_id}` | Get one of your bookmarks | Yes | 200, 401, 404 (missing or not yours), 422 |
| PUT    | `/bookmarks/{bookmark_id}` | Partial update (title, url, note, tag) | Yes | 200, 401, 404, 422 |
| DELETE | `/bookmarks/{bookmark_id}` | Delete | Yes | 204, 401, 404 |

Database schema (from `models.py`):

`users`
- `id` int, primary key
- `email` varchar(255), unique
- `hashed_password` varchar(255)

`bookmarks`
- `id` int, primary key
- `title` varchar(200)
- `url` varchar(2000)
- `note` varchar(255), nullable
- `tag` varchar(255), nullable
- `created_at` datetime, server default `now()`
- `owner_id` int, foreign key to `users.id`

Relationship: one User has many Bookmarks (`User.bookmarks` <-> `Bookmark.owner`, via `back_populates`).

Notes:
- `owner_id` is no longer in `BookmarkCreate`; the logged-in user (from the JWT) provides it. `BookmarkOut` still returns it.
- `hashed_password` stores an argon2 hash (never the plain password). The JWT payload holds `sub` (user id as a string) and `exp`.
- An old manual test user (id 1, hashed_password `x`) may still exist in the DB from before auth; it cannot log in.

## 7. Concepts learned

React
- (none yet; frontend starts at step 6)

FastAPI
- Uvicorn vs FastAPI: FastAPI is the app (routes and logic); Uvicorn is the server that runs it; `--reload` restarts on code changes.
- Routes and decorators: `@app.get("/")` links a URL and method to a Python function.
- Auto-generated docs: FastAPI builds interactive API docs at `/docs`; you can test routes there.
- Models vs schemas: SQLAlchemy models describe DB tables; Pydantic schemas describe what the API accepts and returns (and validate it).
- `from_attributes`: lets Pydantic read a SQLAlchemy object (not just a dict) when building the response.
- Dependency injection: `Depends(get_db)` hands each request its own DB session and closes it afterwards.
- CRUD verbs and status codes: POST create (201), GET read (200), PUT update (200), DELETE (204, no body); 404 not found, 422 invalid input, 500 server error.
- Path vs query params: `/bookmarks/{bookmark_id}` identifies one thing; `?tag=x&q=y` filters a collection.
- `exclude_unset=True` on `model_dump` keeps only fields the client actually sent, enabling partial updates.
- Query params `tag` and `q`: optional function parameters (`str | None = None`) become `?tag=...&q=...`; apply each filter only when given.
- 422 vs 404 vs 500: 422 = request shape/validation wrong (Pydantic); 404 = valid request but the thing does not exist (you raise it); 500 = unhandled server error (a bug or an unchecked DB error).
- Pydantic `Field(min_length=, max_length=)`: validates input sizes at the API edge, matching DB column sizes, so bad input gives 422 instead of a DB error.
- `field_validator` + `@classmethod`: runs custom logic on one field (here: prepend `https://` if the URL has no scheme) and returns the cleaned value.
- Ordering: `query.order_by(models.Bookmark.created_at.desc())` gives newest first.
- None vs unset: `exclude_unset` tells "not sent" apart from "sent as null". For required columns (title/url) skip a `None`; for nullable ones (note/tag) `None` means "clear it".
- `continue` in a loop: skips the rest of the current iteration and moves to the next item (used to skip `None` for required fields).
- `HTTPException` takes `detail=` (singular); a wrong keyword is a `TypeError` at runtime, not caught by `py_compile`.

Auth and security (step 5)
- Hashing vs encryption: hashing is one-way (you cannot get the password back; you hash the login attempt and compare); encryption is reversible with a key. Passwords are hashed, never encrypted or stored plain.
- Salt: random data mixed into each hash so equal passwords give different hashes and precomputed tables fail; argon2 (via pwdlib) adds it automatically.
- JWT structure: three parts `header.payload.signature`. The payload is only base64-encoded (readable by anyone), so never put secrets in it. `sub` = who the token is about (user id), `exp` = expiry time. The signature proves the server issued it and it was not altered.
- Secret key: `SECRET_KEY` signs and verifies tokens; anyone with it can forge tokens, so it lives in `.env`, never in git. Changing it invalidates all tokens.
- OAuth2 password flow: client sends username and password to the token URL (`/login`, form-encoded) and gets an access token back. FastAPI's `OAuth2PasswordRequestForm` always names the field `username`; here it holds the email.
- Bearer header: the client sends `Authorization: Bearer <token>` on each request; `OAuth2PasswordBearer(tokenUrl="login")` reads it and powers the Authorize button in `/docs`.
- Dependencies as gatekeepers: `Depends(auth.get_current_user)` runs before the route; if it raises 401 the route body never runs, and it hands the route the user object.
- Authentication vs authorization: authentication = who are you (token valid); authorization = may you touch this thing (owner_id matches).
- 401 vs 403 vs 404 for not-owned resources: 401 = not authenticated/invalid token; 403 = authenticated but forbidden; we return 404 for another user's bookmark so the API does not reveal that the id exists.
- Login error message: `/login` returns the same "Incorrect email or password" for an unknown email and a wrong password, so attackers cannot learn which emails are registered.
- Fail-fast startup guard: raising `RuntimeError` at import if `SECRET_KEY` is missing stops the app immediately instead of failing weirdly on the first token.
- Python parameter order: a parameter without a default cannot follow one with a default (`SyntaxError`); put plain parameters first and `Depends(...)` ones last.
- `urllib.parse.urlparse`: splits a URL into scheme, netloc, path, etc.; lets you check the scheme is `http`/`https` and a host exists, instead of string-prefix guessing.
- `EmailStr`: Pydantic type that validates email format (needs `email-validator`); bad emails give 422.
- Email normalization: emails are case-insensitive in practice, so strip and lowercase them once (in a schema validator) before storing or comparing; otherwise `A@x.com` and `a@x.com` become two accounts.
- CORS and preflight (upcoming): browsers block a page on `http://localhost:5173` from reading responses from `http://127.0.0.1:8000` unless the API sends CORS headers. For requests with an `Authorization` header or JSON body the browser first sends an `OPTIONS` preflight; FastAPI's `CORSMiddleware` (`allow_origins=["http://localhost:5173"]`, `allow_headers`, `allow_methods`) answers it. CORS is enforced by the browser only, so `/docs` and curl never hit it.
- Logging secrets: never `print` tokens or payloads in auth code; logs are often stored and shared.
- Shared validator function: write the URL-cleaning logic once (`normalize_url()`) and call it from both `BookmarkCreate` and `BookmarkUpdate` so the rules cannot drift apart.

Postgres / SQLAlchemy
- Postgres server vs database: one server runs many databases; ours is `bookmark_vault`.
- psql: command-line client to inspect data (`\dt`, `\d bookmarks`, `\q`).
- SQL needs a `;` at the end; a `-#` prompt means it is waiting for one.
- SQLAlchemy engine/session/Base: engine is the connection, session is a unit of work, `Base` is the parent of all table classes.
- Primary and foreign keys: `id` identifies a row; `owner_id` points at `users.id`, and Postgres rejects values with no matching user.
- Relationships: `relationship(back_populates=...)` lets you go from a user to their bookmarks and back.
- `db.add` + `db.commit` + `db.refresh` saves a new row and reloads DB-generated fields (id, created_at); `db.get(Model, id)` fetches one row by primary key.
- `ilike` is case-insensitive match; `%` is the wildcard, so `f"%{q}%"` means "contains". Chaining `.filter(...)` calls combines them with AND.

Tooling
- Virtualenvs: an isolated Python install per project, activated before `pip install`.
- `.env` and `.gitignore` secrets: keep `.env` and `venv/` out of git; load them with python-dotenv.

## 8. Problems and fixes log

| Problem | Symptom | Cause | Fix |
| ------- | ------- | ----- | --- |
| `psql` not on PATH | `psql` not recognized in PowerShell | Postgres `bin` folder not in PATH | Add `C:\Program Files\PostgreSQL\18\bin` to PATH, restart the terminal / VS Code |
| Stack Builder asks for a package | Installer's Stack Builder wants you to select something | It is an optional add-on installer | Just click Cancel; it is not needed |
| UTF-16 `requirements.txt` | `pip install -r` fails or shows garbled text | File was saved UTF-16 (PowerShell `>` redirect) | `pip freeze \| Out-File -Encoding utf8 requirements.txt` (file is now UTF-8) |
| Windows Application Control blocks SQLAlchemy | Import error about a blocked `_util_cy ... .pyd` file | Windows policy blocked an unsigned native extension | Delete the `.pyd` files in the venv's `sqlalchemy` folder so the pure-Python path is used (fallback: a Python 3.13 venv) |
| Empty `.env` | `create_engine(None)` failure on startup | `DATABASE_URL` missing, so `os.getenv` returned `None` | Put `DATABASE_URL=...` in `backend/.env` |
| Duplicate uvicorn servers on port 8000 | `/docs` hangs, or old code still served | An earlier uvicorn kept running | `netstat -ano \| findstr :8000`, then `Stop-Process -Id <pid>` |
| `ForeignKey("user.id")` vs table `users` | Foreign key target table not found | Name did not match `__tablename__ = "users"` | Use `ForeignKey("users.id")` |
| `unique=True` on title/url | Could not save two bookmarks with the same title or URL | Wrong constraint for these columns | Removed it; only `users.email` is unique |
| `model.py` vs `import models` | `ModuleNotFoundError: No module named 'models'` | File was named `model.py` | Renamed to `models.py` |
| `!bookmark` | Syntax error | `!` is not a Python operator | Use `not bookmark` |
| `db.query(Model, id)` vs `db.get(Model, id)` | Wrong/odd results or errors fetching one row | `query` takes models/columns, not an id | Use `db.get(models.Bookmark, bookmark_id)` |
| Missing path param in PUT | Route did not receive the id / 422 | `{bookmark_id}` in the path but not a function parameter | Add `bookmark_id: int` to the function signature |
| `commit`/`return` inside the `for` loop | Only the first field saved/returned | Indentation put them in the loop body | Dedent them to run after the loop |
| `status_code=201` on every route | Wrong status codes | 201 means "created"; only POST creates | Use 201 for POST only, 200 default, 204 for DELETE |
| Duplicate function names | Confusing behavior / shadowed functions | Two route functions with the same name | Give each route function a unique name |
| Missing semicolon in psql | Prompt becomes `-#`, nothing runs | SQL statement not terminated | Type `;` and Enter |
| FK violation gives 500 | `POST /bookmarks` with a non-existent `owner_id` returns 500 (`ForeignKeyViolation`) | Postgres rejects the foreign key; no check in the route | Insert a test user (id 1) and use it; added `db.get(models.User, data.owner_id)` check returning 404 (see next row) |
| `details=` instead of `detail=` | Owner check still returns 500 (`TypeError`) instead of 404 | `HTTPException` keyword is `detail`; `py_compile` does not catch wrong keyword names | Use `detail=...` (the check was later removed with `owner_id`; all current `HTTPException`s use `detail`) |
| psql statement without `;` (again) | Prompt stuck at `-#` | Statement not terminated | Type `;` and Enter |
| `get_bookmarks` vs `list_bookmarks` in `/docs` | Route titles in `/docs` show the function name (e.g. "Get Bookmarks" vs "List Bookmarks"), confusing when names clash or are unclear | FastAPI builds operation titles from function names | Use distinct, descriptive names: `list_bookmarks` (collection), `get_bookmark` (one) |
| Parameter without default after one with default | `SyntaxError: parameter without a default follows parameter with a default` | A route had `x: T = None` (or `Depends(...)`) before a plain parameter | Put plain parameters first, defaulted/`Depends` ones last |
| `datatime` typo | `ImportError: cannot import name 'datatime'` | Misspelled `datetime` in an import | Fix the spelling: `from datetime import datetime, timedelta, timezone` |
| `model.User` vs `models.User` | `NameError: name 'model' is not defined` | Module is `models`, not `model` | Use `models.User` |
| Missing `SECRET_KEY` | App fails to start (or `jwt.encode` fails with a `None` key) | `SECRET_KEY` not in `backend/.env` | Generate one with `secrets.token_hex(32)`, add to `.env`; startup `RuntimeError` guard now gives a clear message |
| `db.query.filter(...)` | `AttributeError` / invalid call | `query` is a method; it must be called first | `db.query(models.User).filter(...)` |
| Owner check before None check | 500 `AttributeError: 'NoneType' object has no attribute 'owner_id'` for a missing bookmark | `bookmark.owner_id` read before checking `bookmark` exists | Check `not bookmark or bookmark.owner_id != current_user.id` (None first) |
| Validator crash on `None` in `BookmarkUpdate` | Error when `url` is omitted/null in PUT | `v.startswith` called on `None` | Return early `if v is None: return v` |
| `create_bookmark` missing `owner_id` | Every create would be a 500 (`NOT NULL` violation) after `owner_id` was removed from `BookmarkCreate` | `model_dump()` no longer contains `owner_id` | Pass `owner_id=current_user.id` when building `models.Bookmark` (done) |
| Naive URL validator | `https//x.com` becomes `https://https//x.com`; `javascript:` links accepted | Only checks `startswith(("http://", "https://"))` | Open (still not done on 2026-11-08): replace with a shared `normalize_url()` using `urllib.parse` |
| Debug `print` left in `get_current_user` | Token payload and user id appear in the uvicorn console on every authenticated request | `print(payload)` and `print(user_id)` added while debugging (seen 2026-11-08) | Open: delete them (tokens/payloads should not go to logs) |
| Email case not normalized | `A@x.com` and `a@x.com` register as different users; login is case-sensitive | `/register` and `/login` use the email exactly as typed | Open: lowercase (and strip) the email in `UserCreate` or in both routes |
| `client_id`/`client_secret` in Authorize popup | Blank extra fields in `/docs` Authorize dialog | Part of the OAuth2 password-flow form FastAPI renders | Leave them blank; only `username` (email) and `password` are used |

## 9. Session log

### 2026-11-04

- Step 1 done: `backend/` and `frontend/` folders, git init, `.gitignore` (`.env`, `venv/`, `__pycache__/`, `node_modules/`), Python venv in `backend/`. Postgres 18 installed, `psql` on PATH, database `bookmark_vault` created.
- Step 2 done: FastAPI hello world in `main.py`, run with `uvicorn main:app --reload`, `/docs` explored.
- Step 3 in progress: `main.py` imports `Base`, `engine` and `models` and calls `create_all`. `database.py` and `model.py` exist but are empty.
- Concepts learned: virtualenvs, `.gitignore` and secrets, HTTP routes and decorators, uvicorn, auto-generated docs, Postgres server vs database, SQLAlchemy engine/session/ORM, dependency injection, primary/foreign keys, relationships.

#### 2026-11-04, later (README refresh after code was written)

- What happened: the user wrote `database.py` (engine, `SessionLocal`, `Base`, `get_db`), `models.py` (`User`, `Bookmark`), and put `DATABASE_URL` in `.env`. The `model.py` file is now `models.py`, fixing the import mismatch. README restructured into the 9-section format.
- Verified by reading code: `import models` works and registers `users` and `bookmarks`. The server start and actual table creation in Postgres were not tested in this pass.
- Learned: declarative `Base`, `Mapped[...]`/`mapped_column`, `server_default=func.now()`, nullable columns via `Mapped[str | None]`, `back_populates`.
- Next: start the server, confirm tables with `\dt` in psql, finish step 3, then begin step 4 (Pydantic schemas and Bookmark CRUD routes).

### 2026-11-05

- What happened: step 3 wrapped up (tables exist in Postgres; a test user with id 1 was inserted manually). Step 4 mostly built: `schemas.py` (`BookmarkCreate` with temporary `owner_id`, `BookmarkUpdate`, `BookmarkOut`) and `main.py` routes POST, GET list, GET one, PUT, DELETE, plus `tag` and `q` filters. Many small bugs were fixed along the way (see section 8).
- Verified by reading code: all backend files pass `py_compile`; the five CRUD routes use `Depends(get_db)`, return 404 via `HTTPException` when missing, and use correct status codes (201 on POST, 204 on DELETE). Not in code: owner-exists check on POST, null-title/url guard in PUT.
- Learned: Pydantic schemas vs SQLAlchemy models, `from_attributes`, path vs query params, `exclude_unset`, `db.add/commit/refresh` vs `db.get`, `ilike` with `%`, chaining filters (AND), status codes 200/201/204/404/422/500.
- Next: add the owner-exists check on POST, handle null `title`/`url` in PUT, test every route in `/docs`, then start step 5 (password hashing + JWT) which removes `owner_id` from `BookmarkCreate`.

#### 2026-11-05, later (step 4 hardening)

- What happened: the user was told to harden step 4 and implemented most of it: owner-exists check in POST, `continue` for `None` title/url in PUT, `Field` length limits and an `https://` `field_validator` in `schemas.py`, and `created_at` descending order on the list route.
- Verified by reading code: all four items are present and all backend files pass `py_compile`. Found a bug: the POST owner check uses `details=` instead of `detail=`, so it would raise `TypeError` (500) rather than return 404. Not yet run against the server.
- Learned: query params `tag`/`q`, `ilike`, 422 vs 404 vs 500, `Field` constraints, `field_validator`, `order_by(...desc())`, None-vs-unset semantics, `continue` in loops.
- Problems: POST with a nonexistent `owner_id` raised `ForeignKeyViolation` (500) before the check existed; psql statement without `;`; route function names (`get_bookmarks` vs `list_bookmarks`) appear as titles in `/docs`.
- Next: fix `details` to `detail`, test POST with a bad and a good `owner_id` in `/docs`, then tick step 4 and start step 5 (Auth: argon2/bcrypt hashing, `/register`, `/login` returning a JWT, `get_current_user` dependency, remove `owner_id` from `BookmarkCreate`, scope bookmark queries to the current user, `SECRET_KEY` in `.env`).

#### 2026-11-05, later (step 5 Auth)

- What happened: the user started step 5 and wrote `auth.py` (argon2 hashing via pwdlib, PyJWT HS256 tokens with 60-minute expiry, `OAuth2PasswordBearer`, `get_current_user`), the schemas `UserCreate`/`UserOut`/`Token`, and `/register` and `/login` (`OAuth2PasswordRequestForm`, email in the `username` field). Bookmark routes now require a Bearer token, filter by `owner_id`, and return 404 for missing or not-owned bookmarks. `SECRET_KEY` was added to `.env`.
- Verified by reading code: all backend files pass `py_compile`. Done: `owner_id=current_user.id` in `create_bookmark`, `owner_id` removed from `BookmarkCreate`, `EmailStr`, `SECRET_KEY` startup `RuntimeError` guard. Not done: the shared `urllib.parse` URL validator (both schemas still use the naive prepend-`https://` check). Nothing was run against the server, so the manual two-user test is still pending.
- Learned: hashing vs encryption, salt, JWT structure (`sub`, `exp`, signature), secret key, OAuth2 password flow, Bearer header, dependencies as gatekeepers, authentication vs authorization, 401 vs 403 vs 404, non-revealing login errors, fail-fast startup guard, parameter order (non-default before default), `urlparse`, `EmailStr`, shared validator function.
- Problems: parameter-order `SyntaxError`, `datatime` typo, `model.User` vs `models.User`, missing `SECRET_KEY`, `db.query.filter`, owner check before None check (500), validator crash on `None` in `BookmarkUpdate`, `details=` vs `detail=`, missing `owner_id` in `create_bookmark`, naive URL validator, blank `client_id`/`client_secret` in the Authorize popup (see section 8).
- Next: write the shared `normalize_url()`, run the two-user test in `/docs` (register A and B, A creates a bookmark, B gets 404 and an empty list, no token gives 401), tick step 5, then Step 6: React + Vite frontend with CORS middleware in FastAPI for `http://localhost:5173`.

### 2026-11-08

- What happened: README re-check only. Between 2026-11-05 and now, `auth.py` was edited (two debug `print` calls added in `get_current_user`), and `main.py`/`schemas.py`/`database.py` have newer timestamps; the content matches what is documented, with PUT now using a `required = {"title", "url"}` set to skip `None`.
- Verified by reading code: all five backend files pass `py_compile`. Not done in code: shared `normalize_url()` (both schemas still prepend `https://` naively), email lowercasing on register/login, CORS (`CORSMiddleware` absent), React frontend (`frontend/` is empty; no `package.json`). The PUT-null-title decision is implicitly "silently ignore" (200). The manual two-user test is not confirmed anywhere, so Step 5 stays unticked: implemented, pending manual verification.
- Learned (documented, not yet practiced): email normalization, CORS and preflight, not logging secrets.
- Problems: debug `print`s of token payload in `get_current_user`; email case not normalized (see section 8).
- Next: write `normalize_url()` and use it in both schemas, lowercase emails, remove the debug prints, run the two-user test in `/docs`, then tick step 5 and add `CORSMiddleware` for `http://localhost:5173` before scaffolding the Vite frontend.
