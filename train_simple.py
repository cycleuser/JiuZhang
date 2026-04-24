#!/usr/bin/env python3
"""Simplified training script for JiuZhang math model on CPU."""

import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

MODEL_PATH = "/Users/fred/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B"
DATA_PATH = "jiuzhang_merged_training.jsonl"
OUTPUT_DIR = "jiuzhang-math-0.8b"
MAX_SEQ_LENGTH = 512  # Shorter sequences for faster training
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 16  # Effective batch = 16
EPOCHS = 1  # Start with 1 epoch for testing
LEARNING_RATE = 2e-4
LORA_R = 8
LORA_ALPHA = 16

print("=" * 60)
print("JiuZhang Math Model Training (Simplified)")
print("=" * 60)

# Load tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load model on CPU
print("Loading model on CPU...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="cpu",
    torch_dtype=torch.float32,
)

# Apply LoRA
print("Applying LoRA adapters...")
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
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

# Load and tokenize data
print("Loading training data...")
dataset = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"Loaded {len(dataset)} samples")

def tokenize(example):
    messages = example["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False)
    tokenized = tokenizer(text, truncation=True, max_length=MAX_SEQ_LENGTH)
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

print("Tokenizing...")
dataset = dataset.map(tokenize, remove_columns=dataset.column_names)
print(f"Tokenized {len(dataset)} samples")
print(f"Columns: {dataset.column_names}")

# Use only first 200 samples for quick test
dataset = dataset.select(range(min(200, len(dataset))))
print(f"Using {len(dataset)} samples for training")

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    num_train_epochs=EPOCHS,
    learning_rate=LEARNING_RATE,
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    logging_steps=1,
    save_steps=50,
    save_total_limit=3,
    optim="adamw_torch",
    seed=42,
    report_to="none",
    torch_compile=False,
    dataloader_num_workers=0,
    dataloader_pin_memory=False,
    fp16=False,
    bf16=False,
)

# Train
print("Starting training...")
start_time = time.time()

trainer = Trainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
)

trainer.train()

elapsed = time.time() - start_time
print(f"Training completed in {elapsed/60:.1f} minutes")

# Save
print(f"Saving model to {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print("Model saved!")
