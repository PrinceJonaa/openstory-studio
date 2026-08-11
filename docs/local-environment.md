# Local Environment

Measured during Gate 0 and rechecked on 2026-08-11 in the hosted development workspace.

| Component | Result |
| --- | --- |
| Python | 3.12.13 |
| Node.js | 24.14.0 |
| npm | 11.9.0 |
| uv | 0.11.33 |
| Host architecture | x86_64 Linux (not the target Apple-Silicon machine) |
| OpenAI-compatible server at 127.0.0.1:8080 | unavailable |
| mlxgen executable | unavailable |

The deterministic mock text provider and placeholder image provider are the defaults.
Neither optional local-AI runtime is required to develop, test, or demonstrate the
milestone-one pipeline.

uv's default global cache is read-only in this hosted workspace. Development commands
here set UV_CACHE_DIR to a temporary writable directory; normal local clones can use uv's
default cache.

The checks were:

```bash
python3 --version
node --version
npm --version
uv --version
curl --max-time 2 http://127.0.0.1:8080/v1/models || true
mlxgen --help || true
```

The text endpoint refused the connection and `mlxgen` was not on `PATH`. Those findings
did not block implementation: all source-to-export behavior runs through deterministic
mocks, while the two optional adapters are unit-tested without downloading weights.

Target-machine proof remains separate:

1. start an OpenAI-compatible local text server and repeat extraction, adaptation, and
   storyboard construction;
2. verify the installed MLX-Gen CLI flags;
3. render one 512 × 512 panel through the opt-in `local_ai` test.
