# Optional Local AI

The complete product and CI suite use `MockTextProvider` plus
`PlaceholderImageProvider`. Local models are optional adapters and can be enabled one at a
time after the mock pipeline succeeds.

## OpenAI-compatible text

Point OpenStory Studio at an OpenAI-compatible server such as `mlx_lm.server`:

```bash
export OPENSTORY_TEXT_PROVIDER=openai_compatible
export OPENSTORY_TEXT_BASE_URL=http://127.0.0.1:8080/v1
export OPENSTORY_TEXT_API_KEY=local
export OPENSTORY_TEXT_MODEL=local-model
```

Start the server using the command supported by the installed `mlx-lm` version and chosen
model, then verify its OpenAI-compatible model list before starting OpenStory Studio:

```bash
curl --fail http://127.0.0.1:8080/v1/models
```

The adapter sends structured prompts through chat completions, parses JSON, validates the
requested Pydantic schema, and performs one bounded repair retry. It does not require tool
calling or provider-specific response formats.

Return to deterministic text at any time:

```bash
export OPENSTORY_TEXT_PROVIDER=mock
```

## MLX-Gen images

The image adapter wraps the CLI instead of embedding a model runtime:

```bash
export OPENSTORY_IMAGE_PROVIDER=mlxgen
export OPENSTORY_MLXGEN_EXECUTABLE=mlxgen
export OPENSTORY_MLXGEN_MODEL=AbstractFramework/flux.2-klein-9b-8bit
command -v "$OPENSTORY_MLXGEN_EXECUTABLE"
```

Conceptually the adapter invokes:

```bash
mlxgen generate \
  --model MODEL \
  --prompt PROMPT \
  --width WIDTH \
  --height HEIGHT \
  --seed SEED \
  --output OUTPUT
```

It uses an argument array with no shell interpolation, captures stdout/stderr, checks the
exit code, and verifies the output PNG and dimensions. Selecting MLX-Gen while it is
unavailable does not prevent API startup; render requests become failed jobs and return a
concise 503 response.

MLX-Gen was absent during Gate 0, so its exact CLI flags must be verified on the target
Apple-Silicon machine against that machine's installed MLX-Gen version before the first
real render. No model weights are downloaded by normal setup or tests.

Return to the required fallback with:

```bash
export OPENSTORY_IMAGE_PROVIDER=placeholder
```

## Unified-memory guidance

On a 24 GB Apple-Silicon machine, run text inference and heavyweight image inference as
separate jobs. Do not require both large models to remain resident. The persisted story,
canon, storyboard, and render metadata survive provider restarts and model replacement.

## Opt-in proofs

Only run hardware-backed tests after explicitly configuring the local runtimes:

```bash
export OPENSTORY_RUN_LOCAL_AI=1
uv run pytest -m local_ai -q
```

Without that opt-in, local-AI tests skip and the normal suite remains offline and
deterministic.
