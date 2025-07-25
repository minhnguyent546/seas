#!/usr/bin/env bash

# Run marker to convert pdf to markdown using gpt-4o

FILE_PATH="2_Phu-luc-1_Nganh-tuyen-thang-2025_chinh-thuc.pdf"

marker_single "$FILE_PATH" \
  --output_format markdown \
  --output_dir marker-gpt-outputs \
  --use_llm \
  --llm_service=marker.services.openai.OpenAIService \
  --openai_model=gpt-4o \
  --openai_api_key="$OPENAI_API_KEY" \
  --timeout=150
