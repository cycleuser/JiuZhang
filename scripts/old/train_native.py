#!/usr/bin/env python3
"""Native PyTorch training loop for JiuZhang math model."""

import torch
import time
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

MODEL_PATH = "/Users/fred/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B"
DATA_PATH = "jiuzhang_merged_training.jsonl"
OUTPUT_DIR = "jiuzhang-math-0.8b"
MAX_SEQ_LENGTH = 512
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 16
EPOCHS = 1
LEARNING_RATE = 2e-4
LORA_R = 8
LORA_ALPHA = 16

print("=" * 60)
print("JiuZhang Math Model Training (Native PyTorch)")
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

def tokenize(example):
    messages = example["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False)
    tokenized = tokenizer(text, truncation=True, max_length=MAX_SEQ_LENGTH)
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

print("Tokenizing...")
dataset = dataset.map(tokenize, remove_columns=dataset.column_names)
dataset = dataset.select(range(min(200, len(dataset))))
print(f"Using {len(dataset)} samples")

# Create DataLoader
class DatasetWrapper:
    def __init__(self, dataset):
        self.dataset = dataset
    
    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, idx):
        item = self.dataset[idx]
        return {
            "input_ids": torch.tensor(item["input_ids"], dtype=torch.long),
            "attention_mask": torch.tensor(item["attention_mask"], dtype=torch.long),
            "labels": torch.tensor(item["labels"], dtype=torch.long),
        }

wrapper = DatasetWrapper(dataset)
dataloader = DataLoader(wrapper, batch_size=BATCH_SIZE, shuffle=True)

# Optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

# Training loop
print("Starting training...")
model.train()
global_step = 0
total_loss = 0

for epoch in range(EPOCHS):
    print(f"Epoch {epoch+1}/{EPOCHS}")
    epoch_loss = 0
    
    for step, batch in enumerate(dataloader):
        # Forward pass
        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
        )
        loss = outputs.loss / GRADIENT_ACCUMULATION
        loss.backward()
        
        if (step + 1) % GRADIENT_ACCUMULATION == 0:
            optimizer.step()
            optimizer.zero_grad()
            global_step += 1
        
        epoch_loss += loss.item()
        
        if (step + 1) % 10 == 0:
            avg_loss = epoch_loss / (step + 1)
            print(f"  Step {step+1}/{len(dataloader)}, Loss: {avg_loss:.4f}")
    
    print(f"Epoch {epoch+1} completed. Avg loss: {epoch_loss/len(dataloader):.4f}")

# Save model
print(f"Saving model to {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print("Training completed!")
