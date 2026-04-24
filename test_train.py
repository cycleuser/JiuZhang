#!/usr/bin/env python3
"""Quick test to verify training works on CPU."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

MODEL_PATH = "/Users/fred/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading model on CPU...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="cpu",
    torch_dtype=torch.float32,
)

print("Applying LoRA...")
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Create tiny dataset
print("Creating test dataset...")
data = {
    "input_ids": [tokenizer.encode("Solve: 2+2=?", return_tensors="pt")[0].tolist()],
    "labels": [tokenizer.encode("Solve: 2+2=?", return_tensors="pt")[0].tolist()],
    "attention_mask": [[1] * len(tokenizer.encode("Solve: 2+2=?"))]
}
dataset = Dataset.from_dict(data)

print("Setting up training...")
training_args = TrainingArguments(
    output_dir="test-output",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    num_train_epochs=1,
    learning_rate=2e-4,
    logging_steps=1,
    save_steps=1,
    optim="adamw_torch",
    seed=42,
    report_to="none",
    remove_unused_columns=False,
    torch_compile=False,
    dataloader_pin_memory=False,
    gradient_checkpointing=False,
    fp16=False,
    bf16=False,
)

trainer = Trainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
)

print("Starting training...")
trainer.train()
print("Training completed!")
