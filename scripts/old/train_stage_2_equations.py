#!/usr/bin/env python3
"""JiuZhang Math Model - Stage 2: Equations
Stage 2 of 4
Epochs: 2
"""

import os
import json
import time
from pathlib import Path

os.environ["WANDB_DISABLED"] = "true"

try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False

import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    BitsAndBytesConfig, TrainingArguments, Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from datasets import load_dataset, Dataset

# Configuration
STAGE = 2
STAGE_NAME = "equations"
MODEL_NAME = "Qwen/Qwen3.5-0.8B"
OUTPUT_DIR = "/private/var/folders/h0/64ycsy616rbb9rsm15zj4tpm0000gn/T/pytest-of-fred/pytest-70/test_generate_all_scripts0/model/stage_2"
PREV_STAGE_DIR = "/private/var/folders/h0/64ycsy616rbb9rsm15zj4tpm0000gn/T/pytest-of-fred/pytest-70/test_generate_all_scripts0/model/stage_1" if stage_num > 1 else None
MAX_SEQ_LENGTH = 1024
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 32
EPOCHS = 2
LEARNING_RATE = 0.0001
LORA_R = 16
LORA_ALPHA = 8

print(f"Stage {STAGE}: {STAGE_NAME.title()}")
print(f"Loading data for stage {STAGE}...")

# Load stage-specific data
all_data = load_dataset("json", data_files="jiuzhang_distilled.jsonl", split="train")

# Filter by stage category (assuming data has "category" field)
stage_data = all_data.filter(lambda x: "equations" in x.get("category", "").lower() or 
                             "equations" in x.get("problem_id", "").lower())

if len(stage_data) == 0:
    print(f"No data found for stage {STAGE}. Using all data.")
    stage_data = all_data

print(f"Stage {STAGE} data: {len(stage_data)} samples")

def format_chatml(example):
    return {
        "text": tokenizer.apply_chat_template(example["messages"], tokenize=False)
    }

# Device setup
device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

# Quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=True,
)

# Load model
if PREV_STAGE_DIR and Path(PREV_STAGE_DIR).exists():
    print(f"Loading model from previous stage: {PREV_STAGE_DIR}")
    tokenizer = AutoTokenizer.from_pretrained(PREV_STAGE_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        PREV_STAGE_DIR,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=compute_dtype,
    )
else:
    print("Loading base model...")
    # Resolve ModelScope model to local path if needed
    MODEL_PATH = MODEL_NAME
    try:
        from modelscope import snapshot_download
        MODEL_PATH = snapshot_download(MODEL_NAME)
        print(f"ModelScope model resolved to: {MODEL_PATH}")
    except ImportError:
        print("modelscope not installed, falling back to HuggingFace path")
    except Exception as e:
        print(f"ModelScope download failed: {e}, trying HuggingFace path")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=compute_dtype,
    )

# Apply LoRA
model = prepare_model_for_kbit_training(model)
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Format dataset
stage_data = stage_data.map(format_chatml)

# Training
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    warmup_ratio=0.05,
    num_train_epochs=EPOCHS,
    learning_rate=LEARNING_RATE,
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    seed=42,
    bf16=compute_dtype == torch.bfloat16,
    fp16=compute_dtype == torch.float16,
    optim="adamw_8bit",
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    dataloader_num_workers=0,
    report_to="none",
)

trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=stage_data,
    args=training_args,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
)

print(f"\nTraining Stage {STAGE}: {STAGE_NAME.title()}...")
start_time = time.time()
trainer.train()
elapsed = time.time() - start_time

# Save
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Stage {STAGE} completed in {elapsed/60:.1f} minutes")
print(f"Model saved to: {OUTPUT_DIR}")
