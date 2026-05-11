# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

三心书坊 (TriHeart Book Atelier) is an immersive digital reading platform for technical books. It renders PDFs as WebP images via PyMuPDF, protects copyright via per-page signed URLs (no raw PDF exposure), enriches reading with AI-extracted glossary terms and coordinate-scanning annotations, and provides a 3D book simulation reader. Built on the **Brtech Fusion** low-code platform (博然低代码底座).

Site: https://thba.brtech.top

## Development commands

### Backend
```bash
cd app_backend
pip install -r requirements.txt
python main.py                          # starts on port 9988
```

### Frontend
```bash
cd app_frontend
npm install                             # requires local brtech-fusion tarball (see package.json)
npm run dev                             # Vite dev server on :5173, proxies /thba/backend to :9988
npm run build                           # type-check + build → app_backend/static/
npm run lint                            # ESLint
npm run format                          # Prettier
```

No test suite exists for this project.

## Architecture

### Backend: platform-on-rails pattern

The entire backend runs on **Brtech Fusion**, a low-code platform (`brtech_backend` package). The application inherits from `Application` and wires up base platform routers (A4 auth/perms, payment, task tracking, dictionary, UI config). Business logic is injected through **model annotations** and **service hooks** — the platform auto-generates CRUD endpoints, admin pages, and DB queries from `@ui_config` decorators on SQLModel classes.

**File map:**
| File | Role |
|---|---|
| `main.py` | App bootstrap — inherits `Application`, registers routers, wires storage (MinIO) and middleware |
| `config.py` | Settings via `ThbaAppSettings(AppSettings, PaySettings)` — all config keys live here |
| `models.py` | 9 SQLModel classes with `@ui_config` decorators that define admin UI layout, search fields, row actions |
| `schemas.py` | Query schemas — custom SQL via `custom_spec()` for mixed search, page ranges, sorting |
| `crud.py` | Raw DB access — the key custom query is `custom_query_book_user_page()` which JOINs 3 tables for access control |
| `services.py` | All business logic: PDF processing pipeline, AI extraction, coordinate scanning, CDN URL signing, payment Mixin, coordinate-transform Mixin |
| `routers.py` | Generic router classes (e.g., `StringPKeyRouter[Model, Crud, Query, Service]`) — custom routes for `/parse`, `/extract`, `/scanCoords`, `/webpUrl`, `/coverSignUrl` |
| `ai_helper.py` | DeepSeek API client — sends book text, receives glossary terms as JSON |
| `pdf_helper.py` | PyMuPDF engine — renders pages to WebP with smart-crop, eye-protection tinting, TOC extraction, term coordinate scanning |

**Key platform features used:**
- **`@ui_config`**: Declares admin CRUD pages, search forms, row actions entirely from annotations
- **`TaskRecord`**: Long-running tasks (PDF parse, AI extraction, coord scan) are async-tracked with progress callbacks
- **`PaymentServiceMixin`**: `TriHeartBookUserService` inherits this; after payment succeeds, the platform calls `resolve_pay_order()` to auto-add the book to the user's shelf
- **`PageRectsMixinService`**: Transforms annotation coordinates between original-image and cropped-image coordinate spaces
- **CDN signed URLs**: Supports EdgeOne and Gcore CDN providers with token-based auth

**URL structure:** `/thba/backend/...` (API), `/thba/frontend/...` (UI), configurable via `CONTEXT_PATH`, `API_PREFIX`, `UI_PATH` in `config.py`.

### Frontend: Vue 3 + Brtech Fusion SDK

The frontend depends on `brtech-fusion` (local tarball at `../../../svn.local/brtech-fusion/brtech_frontend/brtech-fusion-1.0.1.tgz`) which provides admin layout, CRUD components, auth flows, and the request client. The app's own code focuses on the reader and portal.

**Structure:**
```
src/
  api/portal/, reader/, shelf/     # API call wrappers
  components/
    portal/Header.vue              # Site header
    reader/v1-v4/                  # Reader engine iterations (v4 is production)
    shelf/                         # Book card/grid components
  stores/user.ts                   # Pinia auth store (token + userInfo)
  views/
    portal/Index.vue               # Portal layout shell
    portal/Home.vue                # Landing page
    portal/Bookshelf.vue           # Book browsing
    portal/BookDetail.vue          # Single book detail
    space/Bookshelf.vue            # User's personal shelf
    admin/Index.vue                # Admin shell (renders brtech-fusion admin)
    Login.vue                      # Login page
  router/index.ts                  # 4 routes: /, /reader/:bookId/:pageNo?, /login, /admin/*
```

**Reader v4** is the current production reader. It's a 3D CSS-transform-based book simulation with:
- `Book3DEngine.vue` — main orchestrator
- `Book3DLeaf.vue` — individual leaf rendering
- `LeafSegment.vue` — segmented page-turning with micro-arc deformation
- `BookPage.vue` — page content with term annotations, highlights, attachments
- `GroundPlane.vue` — 3D desk/surface plane
- `types.ts` — `PageData`, `BookMeta`, `ViewMode`, `FlipState`, `SegmentData`

Build output goes to `../app_backend/static/` which the backend serves as static files.

## Key conventions

- **API calls** use the `request` object from `brtech-fusion` (not raw axios)
- **Authorization**: All backend services receive `user_id` from `AuthContext`; `user_id=None` means anonymous (guest preview mode)
- **Page numbers** are 1-based throughout
- **Coordinates** stored as percentage `[x, y, w, h]` (0.0–1.0) relative to original image; transformed to crop-space on read via `imageMode=crop` query param
- **Process status** constants: `"0"` pending, `"1"` processing, `"2"` success, `"9"` failed
- **Fixtures** in `app_backend/fixtures/` auto-load on startup (dictionaries, default roles/users, menus, permissions)