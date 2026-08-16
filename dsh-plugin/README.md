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
dsh plugin --profile demo add ./dsh-plugin
```

**Option B — from GitHub:**

```sh
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
