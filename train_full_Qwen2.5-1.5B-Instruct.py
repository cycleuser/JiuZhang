#!/usr/bin/env python3
"""JiuZhang Math Model Training Script (HuggingFace Full Fine-tuning)"""

import os
os.environ["WANDB_DISABLED"] = "true"

from transformers import (
    AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForSeq2Seq
)
from datasets import load_dataset
import torch

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DATA_PATH = "jiuzhang_distilled.jsonl"
OUTPUT_DIR = "/private/var/folders/h0/64ycsy616rbb9rsm15zj4tpm0000gn/T/pytest-of-fred/pytest-39/test_generate_training_script_1/model"
MAX_SEQ_LENGTH = 2048
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 8
EPOCHS = 3
LEARNING_RATE = 5e-5

# Resolve ModelScope model path
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
    torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    device_map="auto",
)

dataset = load_dataset("json", data_files=DATA_PATH, split="train")

def tokenize(example):
    text = tokenizer.apply_chat_template(example["messages"], tokenize=False)
    return tokenizer(text, truncation=True, max_length=MAX_SEQ_LENGTH)

tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)

trainer = Trainer(
    model=model,
    args=TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        warmup_ratio=0.06,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=200,
        seed=42,
        fp16=True,
        gradient_checkpointing=True,
    ),
    train_dataset=tokenized,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
)

print("Starting training...")
trainer.train()

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Model saved to {OUTPUT_DIR}")