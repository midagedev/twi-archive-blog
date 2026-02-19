#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <model_endpoint> <prompt_file> <output_file> [image_size] [seed] [mode]"
  echo "mode: sync (default) | queue"
  echo "Example: $0 fal-ai/flux/dev prompts/key-visual-pastel-v2.txt assets/key-visuals/key-visual-pastel-v2.jpg landscape_16_9 424242 sync"
  exit 1
fi

MODEL="$1"
PROMPT_FILE="$2"
OUTPUT_FILE="$3"
IMAGE_SIZE="${4:-landscape_16_9}"
SEED="${5:-}"
MODE="${6:-sync}"

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
  --arg seed "$SEED" \
  '{prompt:$prompt, image_size:$image_size, num_images:1} + (if $seed == "" then {} else {seed:($seed|tonumber)} end)')"

if [[ "$MODE" == "sync" ]]; then
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
  exit 0
fi

if [[ "$MODE" != "queue" ]]; then
  echo "Invalid mode: $MODE (use sync or queue)"
  exit 1
fi

SUBMIT="$(curl -sS -X POST "https://queue.fal.run/${MODEL}" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")"

RESPONSE_URL="$(echo "$SUBMIT" | jq -r '.response_url // empty')"
if [[ -z "$RESPONSE_URL" ]]; then
  echo "Failed to submit request:"
  echo "$SUBMIT"
  exit 1
fi

for _ in $(seq 1 60); do
  RESULT="$(curl -sS "$RESPONSE_URL" -H "Authorization: Key ${FAL_KEY}")"
  IMAGE_URL="$(echo "$RESULT" | jq -r '.images[0].url // empty')"
  ERROR_MSG="$(echo "$RESULT" | jq -r '.error.message // empty')"
  DETAIL_MSG="$(echo "$RESULT" | jq -r '.detail // empty')"
  STATUS="$(echo "$RESULT" | jq -r '.status // empty')"
  if [[ -n "$IMAGE_URL" ]]; then
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    curl -sS "$IMAGE_URL" -o "$OUTPUT_FILE"
    echo "Saved: $OUTPUT_FILE"
    exit 0
  fi
  if [[ -n "$ERROR_MSG" ]] || [[ "$STATUS" == "FAILED" ]]; then
    echo "Generation failed:"
    echo "$RESULT"
    exit 1
  fi
  if [[ -n "$DETAIL_MSG" ]] && [[ "$DETAIL_MSG" != "Request is still in progress" ]]; then
    echo "Generation failed:"
    echo "$RESULT"
    exit 1
  fi
  sleep 2
done

echo "Timed out waiting for generation result."
exit 1
