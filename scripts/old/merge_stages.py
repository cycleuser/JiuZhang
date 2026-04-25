#!/usr/bin/env python3
"""Merge all staged training checkpoints into final model."""

import os
from pathlib import Path
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

OUTPUT_DIR = "/private/var/folders/h0/64ycsy616rbb9rsm15zj4tpm0000gn/T/pytest-of-fred/pytest-70/test_generate_all_scripts0/model"
NUM_STAGES = 4

print("Merging staged checkpoints...")

# Load the last stage model
final_dir = os.path.join(OUTPUT_DIR, f"stage_{NUM_STAGES}")
print(f"Loading final stage model from: {final_dir}")

tokenizer = AutoTokenizer.from_pretrained(final_dir)
model = AutoModelForCausalLM.from_pretrained(
    final_dir,
    torch_dtype="auto",
    device_map="cpu",
)

# Merge and save
print("Merging LoRA weights...")
model = model.merge_and_unload()

merged_dir = os.path.join(OUTPUT_DIR, "merged-final")
model.save_pretrained(merged_dir)
tokenizer.save_pretrained(merged_dir)

print(f"Merged model saved to: {merged_dir}")
print("Ready for GGUF export or Ollama import!")
