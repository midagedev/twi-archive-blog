#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <prompt_file> <output_file> <lora_url> [image_size] [seed] [lora_scale]"
  echo "Example: $0 prompts/sheet.txt assets/out.jpg https://.../anime_lora.safetensors square_hd 12345 0.95"
  exit 1
fi

PROMPT_FILE="$1"
OUTPUT_FILE="$2"
LORA_URL="$3"
IMAGE_SIZE="${4:-square_hd}"
SEED="${5:-}"
LORA_SCALE="${6:-1.0}"
MODEL="fal-ai/flux-lora"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Prompt file not found: $PROMPT_FILE"
  exit 1
fi

if [[ -z "${FAL_KEY:-}" ]]; then
  echo "FAL_KEY is not set. Export it first."
  exit 1
fi

PROMPT="$(cat "$PROMPT_FILE")"

PAYLOAD="$(jq -n \
  --arg prompt "$PROMPT" \
  --arg image_size "$IMAGE_SIZE" \
  --arg lora_url "$LORA_URL" \
  --arg lora_scale "$LORA_SCALE" \
  --arg seed "$SEED" \
  '{
    prompt: $prompt,
    image_size: $image_size,
    num_images: 1,
    loras: [{path: $lora_url, scale: ($lora_scale|tonumber)}]
  } + (if $seed == "" then {} else {seed:($seed|tonumber)} end)')"

RESULT="$(curl -sS -X POST "https://fal.run/${MODEL}" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")"

IMAGE_URL="$(echo "$RESULT" | jq -r '.images[0].url // empty')"
if [[ -z "$IMAGE_URL" ]]; then
  echo "Generation failed:"
  echo "$RESULT"
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"
curl -sS "$IMAGE_URL" -o "$OUTPUT_FILE"
echo "Saved: $OUTPUT_FILE"
