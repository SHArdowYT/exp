# Changelog

All notable changes to this project are documented here.
Dates are in ISO 8601 format (YYYY-MM-DD).

---

## 2026-09-03 (pass 8)

### Changed
- `python/static/style.css` -- renamed all classes from SUIT CSS (Pascal case)
  to BEM (lowercase kebab-case): Card->card, Card--wide->card--wide,
  Button->button, Button--*->button--*, UserList->user-list,
  UserList-item->user-list__item, etc. Eyebrow, Heading, Subtitle, Avatar,
  Divider all lowercased. CSS comment block documents BEM convention and links
  to getbem.com.
- All four templates updated to use new BEM class names
- `python/templates/home_signed_out.html` -- inline SVG replaced with
  <img src="/static/images/google.svg">

### Added
- `python/static/images/google.svg` -- Google brand icon served as a static
  file; no longer inlined in the template

---


### Changed
- `python/static/style.css` -- renamed all classes to follow SUIT CSS conventions
  (https://github.com/suitcss/suit/blob/master/doc/naming-conventions.md):
  Pascal case blocks (Card, Button, Avatar, Eyebrow, Heading, Subtitle, Divider,
  UserList), camel case descendants (UserList-item, UserList-avatar, UserList-info,
  UserList-name, UserList-email, UserList-action), double dash modifiers
  (Card--wide, Button--primary, Button--outline, Button--google). Previously
  card__eyebrow, card__heading etc. were illogically scoped as elements of Card
  when they are independent components.
- All four templates updated to use new SUIT class names
- `scripts/update_fonts.py` -- rewritten to download the official release zip
  from github.com/rektdeckard/departure-mono/releases/download/v1.500/
  DepartureMono-1.500.zip, extract the woff2, and write it to static/fonts/

---


### Added
- `python/static/fonts/DepartureMono-Regular.woff2` -- font served locally;
  no longer fetched from Google Fonts at page load
- `python/static/fonts/LICENSE` -- Departure Mono licence file
- `scripts/` directory containing all maintenance scripts
- `scripts/update_fonts.py` -- fetches Google Fonts CSS, parses the woff2 URL,
  downloads the font, and writes it to python/static/fonts/
- `scripts/check_ascii.py` -- lists all git-tracked files, skips binary
  extensions, reports any line containing non-ASCII bytes, exits 1 on failure
- `scripts/lint.py` -- runs ruff, mypy, and pylint in sequence against python/,
  shows output for any failures, reports pass/fail per tool

### Changed
- `scripts/zip.sh` -- moved from repo root to scripts/
- `python/static/style.css` -- Google Fonts @import replaced with a local
  @font-face rule pointing to /static/fonts/DepartureMono-Regular.woff2
- `python/templates/base.html` -- Google Fonts preconnect links removed
- `.gitignore` -- stale typescript entries removed; .mypy_cache/ and
  .ruff_cache/ added; zip.sh reference updated to scripts/zip.sh
- `INSTRUCTIONS.md` -- scripts section added; all sections renumbered

---


### Removed
- `typescript/` directory -- no longer needed
- `python/.env.example` -- removed per instructions

### Fixed
- All non-ASCII characters (em dashes, arrows) replaced with ASCII equivalents
  throughout every file: .py, .css, .html, .md, .toml, .sh, .gitignore
- All lowercase hex colour codes in CSS upgraded to uppercase (#FFFFFF, #111111, etc.)

### Changed
- `python/static/style.css` -- CSS class names reorganised: standalone utility
  classes (`eyebrow`, `subtitle`, `divider`, `avatar`) renamed to BEM elements
  of `.card` (`card__eyebrow`, `card__subtitle`, `card__divider`, `card__avatar`);
  Jinja2 block `card_class` renamed to `card_modifier` for clarity; all hex codes
  uppercase; all em dashes replaced with --
- All four templates updated to use renamed CSS classes
- `INSTRUCTIONS.md` -- fully rewritten for Python-only; accurate configuration
  table with all current settings; updated routes table; extension guide added

---


### Changed
- `python/auth/google.py` -- removed `router()` method; route registration is not this class's responsibility. Handlers renamed from `_handle_*` to `handle_*` (public) since `main.py` calls them directly. `_user_from_userinfo` extracted as a typed helper. Full type annotations on all locals and instance variables. `_FlowConfig` type alias for the Flow config dict.
- `python/auth/dummy.py` -- removed `router()` method for the same reason. Handlers renamed to public. Full type annotations throughout.
- `python/main.py` -- now the single place where all URL paths are defined. Introduced typed `AppState` dataclass stored on `app.state`, replacing untyped `Any` attribute access. Each route is a thin `@app.get` function that delegates immediately to the appropriate domain object retrieved from `AppState`. `_get_state()` helper centralises the one `# type: ignore` needed to extract `AppState` from FastAPI's untyped `app.state`.
- `python/session/store.py` -- full type annotations on all instance variables and local variables in `_load` and `_flush`.
- `python/session/middleware.py` -- type annotation on `session_id` local.
- `python/config.py` -- type annotation on `_REPO_ROOT`.

### Responsibility boundaries (enforced)
- `auth/google.py` -- OAuth2 logic only; no knowledge of URL paths or routing API
- `auth/dummy.py` -- dummy auth logic only; no knowledge of URL paths or routing API
- `main.py` -- application wiring only; all URL paths defined here and nowhere else
- `session/store.py` -- storage logic only; no framework imports
- `session/middleware.py` -- cookie helpers only; no auth logic, no routing

---


### Fixed
- `*.zip` added to `.gitignore` -- zip archives are now never tracked by git and therefore never included in `git archive` output, eliminating the zip-inside-zip problem

### Changed
- `python/config.py` -- added `session_ttl_seconds` (default 7 days), `cookie_name` (default `"session_id"`), `userinfo_timeout_seconds` (default 10.0), and `log_level` (default `"DEBUG"`) settings; all previously hardcoded constants now configurable via environment variables
- `python/session/store.py` -- removed module-level `_SESSION_TTL_SECONDS` constant; `JsonSessionStore.__init__` now accepts `ttl_seconds` parameter sourced from `Settings`; `_is_expired` accepts `ttl_seconds` explicitly
- `python/session/middleware.py` -- removed `_COOKIE_NAME` and `_COOKIE_MAX_AGE_SECONDS` constants; `get_session`, `set_session_cookie`, and `clear_session_cookie` now accept `Settings` and read cookie name and TTL from it
- `python/auth/google.py` -- `userinfo_timeout_seconds` sourced from settings; `set_session_cookie` and `clear_session_cookie` receive settings; `get_session` receives settings
- `python/auth/dummy.py` -- `set_session_cookie` receives settings; `_settings` stored on instance
- `python/main.py` -- log level sourced from `settings.log_level`; `settings` stored on `app.state` for access by route handlers; `JsonSessionStore` constructed with `ttl_seconds=settings.session_ttl_seconds`
- `python/.env.example` -- documents all new optional settings with their defaults

---


### Changed
- `python/config.py` -- added `dummy_users_file`, `session_file`, `pkce_max_pending` settings; replaced module-level singleton with `get_settings()` (`lru_cache`); added `__all__` and full docstring
- `python/models.py` -- `created_at` changed from `float` to `datetime` (UTC-aware); `frozen=True` on all models; `datetime.UTC` alias; `__all__`
- `python/session/store.py` -- introduced `AbstractSessionStore` ABC for swappable backends; renamed `JsonSessionStore` (was `SessionStore`); `session_file` now injected (not a module-level relative path); renamed `set` -> `save` to avoid shadowing the built-in; `datetime.UTC` alias; typed `dict[str, object]` annotation; `__all__`
- `python/session/middleware.py` -- depends on `AbstractSessionStore` not concrete class; constants made private (`_COOKIE_NAME`, `_COOKIE_MAX_AGE_SECONDS`); `__all__`
- `python/auth/google.py` -- settings injected via constructor (no global import); `_build_flow` takes explicit args; `asyncio.to_thread` for blocking `fetch_token`; `google_user_id` named explicitly; all long lines wrapped; `__all__`
- `python/auth/dummy.py` -- settings and templates injected via constructor; `_load_users_from_file` takes explicit `Path`; typed `dict[str, str]`; long lines wrapped; `__all__`
- `python/main.py` -- all shared resources (`SessionStore`, `GoogleAuth`, `DummyAuth`, `Jinja2Templates`) created in `lifespan` and stored on `app.state`; no module-level mutable singletons; home route reads from `request.app.state`
- `python/auth/__init__.py`, `python/session/__init__.py` -- informative docstrings and sorted `__all__`
- `python/pyproject.toml` -- added tool config for ruff, mypy (strict), pylint (max-line-length=120, R0903/C0305 disabled)

### Result
ruff, mypy (strict), and pylint all pass with zero errors. pylint score: 10.00/10.

## 2026-09-03

### Added
- `CHANGELOG.md` (this file)
- `instructions_history.md` -- running log of user instructions with ISO 8601 dates
- Departure Mono font from GitHub (rektdeckard/departure-mono) via Google Fonts
- White, minimalist, editorial CSS aesthetic with CSS custom properties
- Touch, keyboard, and mouse accessibility: all interactive targets min 44x44px, `:focus-visible` outlines, `aria-label` on all interactive elements, `role` attributes, `aria-hidden` on decorative elements
- Responsive breakpoint at 480px: card loses side borders and expands to full width on mobile

### Changed
- `python/static/style.css` -- full redesign; Departure Mono, CSS variables, BEM naming, editorial aesthetic, responsive
- `python/templates/base.html` -- added Google Fonts preconnect, semantic `<main>` element, 4-space indentation
- `python/templates/home_signed_out.html` -- eyebrow label, divider, accessibility attributes, 4-space indentation
- `python/templates/home_signed_in.html` -- eyebrow label, divider, accessibility attributes, 4-space indentation
- `python/templates/dummy_list.html` -- eyebrow label, `role="list"`, `aria-label` on list and sign-in links, 4-space indentation

### Fixed (linting)
- `python/main.py` -- `AsyncIterator` moved to `collections.abc`; lifespan `app` param renamed to `_app` to avoid shadowing
- `python/session/middleware.py` -- removed unused `Cookie` import
- `python/session/store.py` -- removed unused `User` import; replaced inline `__import__("json")` with proper `import json`; narrowed bare `Exception` catches to `(OSError, ValueError)`
- `python/auth/dummy.py` -- narrowed bare `Exception` catch to `(OSError, ValueError, KeyError)`
- `python/auth/google.py` -- narrowed bare `Exception` catch to `(httpx.HTTPError, ValueError, KeyError)`
- All three linters (ruff, mypy, pylint) pass at 10/10 with zero errors

---

## 2026-09-02

### Added
- Python implementation rewritten with FastAPI, uvicorn, pydantic, pydantic-settings, httpx, pathlib
- `python/config.py` -- pydantic-settings `Settings` class; reads `.env` automatically
- `python/models.py` -- pydantic `User` and `Session` models
- `python/main.py` -- FastAPI app with lifespan hook, static file mount, Jinja2Templates
- PKCE (S256) support in `python/auth/google.py` -- fixes `invalid_grant: Missing code verifier`
- Jinja2 templates for all HTML pages
- Unified `python/static/style.css`
- `<meta name="referrer" content="no-referrer">` in base template -- fixes broken Google profile pictures
- `zip.sh` -- archives repo via `git archive`, respects `.gitignore`, prompts for confirmation, shows command

### Removed
- `python/server.py` -- replaced by `python/main.py`
- `python/types_sha.py`, `python/types_.py` -- replaced by `python/models.py`
- `python/pages/` package -- templating handled by FastAPI's `Jinja2Templates`

---

## 2026-09-01

### Added
- Initial project: TypeScript and Python implementations of Google OAuth2 sign-in
- Shared `dummy_users.json` for test users
- `INSTRUCTIONS.md` at repo root
- `zip.sh` at repo root
