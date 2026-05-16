#!/usr/bin/env python3
"""JiuZhang Math Model Training Script (Unsloth QLoRA)"""

import os
os.environ["WANDB_DISABLED"] = "true"

from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DATA_PATH = "jiuzhang_distilled.jsonl"
OUTPUT_DIR = "/private/var/folders/h0/64ycsy616rbb9rsm15zj4tpm0000gn/T/pytest-of-fred/pytest-0/test_generate_training_script_0/model"
MAX_SEQ_LENGTH = 2048
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 8
EPOCHS = 3
LEARNING_RATE = 2e-4

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

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_PATH,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    use_gradient_checkpointing=True,
    random_state=42,
)

dataset = load_dataset("json", data_files=DATA_PATH, split="train")

def format_chatml(example):
    return {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False)}

dataset = dataset.map(format_chatml)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_ratio=0.03,
        max_steps=-1,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=200,
        output_dir=OUTPUT_DIR,
        seed=42,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        optim="adamw_8bit",
    ),
)

print("Starting training...")
trainer.train()

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Model saved to {OUTPUT_DIR}")

model.save_pretrained_gguf(OUTPUT_DIR, tokenizer)
print(f"GGUF model exported to {OUTPUT_DIR}")