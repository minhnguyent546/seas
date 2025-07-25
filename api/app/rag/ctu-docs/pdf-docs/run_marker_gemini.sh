#!/usr/bin/env bash

# Run marker to convert pdf to markdown using gemini-2.5-flash/pro

FILE_PATH="2_Phu-luc-1_Nganh-tuyen-thang-2025_chinh-thuc.pdf"

marker_single "$FILE_PATH" \
  --output_format markdown \
  --output_dir marker-gemini-outputs \
  --use_llm \
  --llm_service=marker.services.gemini.GoogleGeminiService \
  --gemini_model_name=gemini-2.5-flash \
  --gemini_api_key="$GEMINI_API_KEY" \
  --timeout=150
