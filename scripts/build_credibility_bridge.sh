#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/build"
OUTPUT_BIN="$OUTPUT_DIR/factify_credibility_bridge"

mkdir -p "$OUTPUT_DIR"

c++ -std=c++17 -O3 -Wall -Wextra \
  -I"$ROOT_DIR/vendor/factify_engine/include" \
  "$ROOT_DIR/src/ml/algorithms/credibility_bridge.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/preprocessing.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/source_validator.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/phrase_indexer.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/string_matcher.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/frequency_analyzer.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/temporal_analyzer.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/greedy_filter.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/claim_verifier.cpp" \
  "$ROOT_DIR/vendor/factify_engine/src/scoring_engine.cpp" \
  -o "$OUTPUT_BIN" \
  -pthread

echo "$OUTPUT_BIN"
