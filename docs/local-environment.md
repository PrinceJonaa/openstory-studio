# Local Environment

Measured on 2026-08-10 in the initial development workspace.

| Component | Result |
| --- | --- |
| Python | 3.12.13 |
| Node.js | 24.14.0 |
| npm | 11.9.0 |
| uv | 0.11.33 |
| OpenAI-compatible server at 127.0.0.1:8080 | unavailable |
| mlxgen executable | unavailable |

The deterministic mock text provider and placeholder image provider are the defaults.
Neither optional local-AI runtime is required to develop, test, or demonstrate the
milestone-one pipeline.

uv's default global cache is read-only in this hosted workspace. Development commands
here set UV_CACHE_DIR to a temporary writable directory; normal local clones can use uv's
default cache.

