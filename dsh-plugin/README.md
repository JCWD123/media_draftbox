# dsh-draftbox

A DeepSeek Harness plugin that bridges the core capabilities of
[media_draftbox](https://github.com/JCWD123/media_draftbox) (a WeChat public-account
draft editor) into tools your Harness agent can call.

media_draftbox's backend is Python / FastAPI. It orchestrates **three-modality AI
writing**: text (DeepSeek/MiMo) → illustrations (Ark Seedream, Pexels fallback) →
video (Seedance) → WeChat-compatible typesetting → quality gates → draft management.
This plugin wraps those capabilities as Harness tools so an agent can "write a fully
illustrated, typeset public-account article" from a single prompt.

> Pure ESM (no build step). Only depends on harness-bundled
> `@deepseek-ai/dsh-tools` and `@deepseek-ai/cordis`.

## Quick start

### Prerequisite: run the media_draftbox backend

```sh
cd draftbox_v2/backend
uvicorn main:app --host 127.0.0.1 --port 8502 --reload
```

Make sure model / image / video providers are configured via `draftbox model`
(see the media_draftbox repo README).

### Install the plugin

**Option A — local checkout (development):**

```sh
# 1. Install the plugin's own deps (pnpm installs @deepseek-ai/dsh-tools /
#    @deepseek-ai/cordis into dsh-plugin/node_modules; required because
#    `dsh plugin add` installs via a pnpm `link:` that must resolve them)
cd dsh-plugin && pnpm install && cd ..

# 2. Install into a dsh headless / custom profile
dsh plugin --profile demo add ./dsh-plugin
```

**Option B — from GitHub:**

```sh
# Requires Node >= 22.19 and `dsh` installed (npx @deepseek-ai/dsh or npm i -g @deepseek-ai/dsh)
dsh plugin --profile demo add github:JCWD123/media_draftbox
```

Then run:

```sh
dsh --profile demo
```

Verify the layer is active:

```sh
dsh --profile demo --dump-config   # look for the "# == dsh-draftbox" layer
```

Then just ask the agent, e.g.:

> Write an article about "DeepSeek Harness explained", pick a few hot news items as
> material, add 4 illustrations, typeset with the `midnight` theme, and save it to the draft box.

## One-shot regression test

After installing dsh + pnpm (see above), run the end-to-end self-test with one command:

```sh
cd dsh-plugin
bash test-e2e.sh               # tool-layer checks: start/reuse backend + real
                               #   list/get/save/typeset/search assertions (no LLM cost)
bash test-e2e.sh --with-agent  # reproducible full linkage: a real dsh agent runs
                               #   write_article (incl. 1 Seedream image) -> save_draft -> list_drafts
                               #   + the script independently verifies persistence via curl and cleans up
                               #   (requires DEEPSEEK_API_KEY + a Volcano Ark key configured in the backend)
bash test-e2e.sh --keep-backend # do not stop the backend it started after the run
```

- Exit code `0` = all pass; `1` = some failures; `2` = missing prerequisites (node/pnpm/dsh).
- Test drafts are auto-cleaned; a backend started by the script is stopped by default (`--keep-backend` keeps it).
- The tool-layer self-test never calls an LLM: the 5 regular tools get real assertions
  (list/get/save/typeset/search); the 3 multimodal tools (write_article/illustrate/video_status)
  get contract-level assertions (hit backend validation/error branches without actually
  triggering LLM / Seedream / Seedance).

## Tools exposed

| Tool | What it does | Backend endpoint |
|---|---|---|
| `draftbox_write_article` | Full three-modality article (text + images + optional video) | `POST /api/write/generate` |
| `draftbox_typeset` | Markdown → WeChat-compatible inline-style HTML (20 themes) | `POST /api/convert` |
| `draftbox_save_draft` | Save a draft (with typeset HTML) | `POST /api/drafts` |
| `draftbox_list_drafts` | List the draft box | `GET /api/drafts` |
| `draftbox_get_draft` | Read a single draft | `GET /api/drafts/{filename}` |
| `draftbox_illustrate` | Illustrate article HTML from a "发布物料.md" material file | `POST /api/illustrate` |
| `draftbox_search_images` | Pexels real-photo search | `POST /api/images/search` |
| `draftbox_video_status` | Poll background video task status | `GET /api/write/media-status` |

## Configuration

Defaults to `http://127.0.0.1:8502`. To point at a Docker/VPS backend, override
`baseUrl` in your profile's `cordis.patch.yml`:

```yaml
# $DSH_HOME/profiles/<name>/cordis.patch.yml
- patch:
    - id: dsh-draftbox
      config:
        baseUrl: http://your-host:8502
```

| Key | Default | Notes |
|---|---|---|
| `baseUrl` | `http://127.0.0.1:8502` | media_draftbox backend address |
| `timeoutMs` | `180000` | per-request timeout (writing/illustration can be slow) |

## Capability notes

- Video generation (`with_video: true`) is slow/expensive and runs as a background
  task — poll `draft_id` via `draftbox_video_status`.
- Image source: Ark Seedream first; falls back to Pexels on account errors; remaining
  failures surface in the tool's `warnings` field.
- `draftbox_get_draft` rewrites `/media/` relative paths to `baseUrl` absolute URLs so
  generated images/videos are directly accessible.

## License

MIT. This is part of the DeepSeek Harness plugin ecosystem — tag the repo with the
[`dsh-plugin`](https://github.com/topics/dsh-plugin) topic for discoverability.
