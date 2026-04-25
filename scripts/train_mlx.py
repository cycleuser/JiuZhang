#!/usr/bin/env python3
"""JiuZhang Math Model Training using MLX (Apple Silicon optimized).

This script trains a LoRA adapter on Qwen3.5-0.8B using Apple's MLX framework.
MLX is specifically optimized for Apple Silicon (M1/M2/M3/M4) and runs natively
on the GPU.

Usage:
    python train_mlx.py                    # Full training
    python train_mlx.py --epochs 1         # Quick test (1 epoch)
    python train_mlx.py --samples 100      # Use only 100 samples
"""

import json
import os
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load
from mlx_lm.lora import (
    TrainingArgs,
    linear_to_lora_layers,
    train_model,
    load_dataset as mlx_load_dataset,
)


# Configuration
MODEL_PATH = "/Users/fred/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B"
DATA_PATH = "jiuzhang_merged_training.jsonl"
OUTPUT_DIR = "jiuzhang-math-0.8b"
MAX_SEQ_LENGTH = 512
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 1e-4
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
EPOCHS = 3


def prepare_mlx_dataset(data_path, tokenizer, max_seq_length, samples=None):
    """Convert JSONL data to MLX training format."""
    print(f"Loading data from {data_path}...")
    
    messages_list = []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    sample = json.loads(line)
                    if "messages" in sample:
                        messages_list.append(sample["messages"])
                except json.JSONDecodeError:
                    continue
    
    if samples:
        messages_list = messages_list[:samples]
    
    print(f"Loaded {len(messages_list)} samples")
    
    # Convert to MLX format: list of {"text": "..."} dicts
    mlx_data = []
    for messages in messages_list:
        text = tokenizer.apply_chat_template(messages, tokenize=False)
        mlx_data.append({"text": text})
    
    print(f"Converted {len(mlx_data)} samples to MLX format")
    return mlx_data


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JiuZhang MLX Math Model Training")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--samples", type=int, default=None, help="Limit samples")
    parser.add_argument("--lora-r", type=int, default=8, help="LoRA rank")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--max-seq", type=int, default=512, help="Max sequence length")
    parser.add_argument("--output", default="jiuzhang-math-0.8b", help="Output directory")
    args = parser.parse_args()
    
    output_dir = args.output
    adapter_file = os.path.join(output_dir, "adapters.safetensors")
    
    print("=" * 60)
    print("JiuZhang Math Model Training (MLX - Apple Silicon)")
    print("=" * 60)
    print(f"Device: Apple Silicon (MLX)")
    print(f"Model: {MODEL_PATH}")
    print(f"Data: {DATA_PATH}")
    print(f"Output: {output_dir}")
    print(f"LoRA r={args.lora_r}, alpha={LORA_ALPHA}")
    print(f"Batch size: {args.batch_size}")
    print(f"Max sequence length: {args.max_seq}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning rate: {args.lr}")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load model and tokenizer
    print("\nLoading model...")
    start = time.time()
    model, tokenizer = load(MODEL_PATH)
    print(f"Model loaded in {time.time()-start:.1f}s")
    
    # Add LoRA layers
    print("Adding LoRA adapters...")
    # Freeze model first
    model.freeze()
    
    # Add LoRA without specifying keys - it will find all linear layers
    linear_to_lora_layers(
        model,
        num_layers=len(model.layers),
        config={
            "rank": args.lora_r,
            "scale": 20.0,
            "dropout": LORA_DROPOUT,
        },
    )
    
    # Count trainable parameters
    from mlx_lm.lora import print_trainable_parameters
    print_trainable_parameters(model)
    
    # Prepare dataset
    print("\nPreparing dataset...")
    
    # Create local dataset directory
    dataset_dir = os.path.join(output_dir, "dataset")
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Convert data to JSONL format expected by mlx_lm
    train_path = os.path.join(dataset_dir, "train.jsonl")
    valid_path = os.path.join(dataset_dir, "valid.jsonl")
    
    messages_list = []
    with open(DATA_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    sample = json.loads(line)
                    if "messages" in sample:
                        messages_list.append(sample["messages"])
                except json.JSONDecodeError:
                    continue
    
    if args.samples:
        messages_list = messages_list[:args.samples]
    
    print(f"Loaded {len(messages_list)} samples")
    
    # Split into train/val
    split_idx = int(0.9 * len(messages_list))
    train_messages = messages_list[:split_idx]
    val_messages = messages_list[split_idx:]
    
    # Write train.jsonl
    with open(train_path, "w") as f:
        for messages in train_messages:
            text = tokenizer.apply_chat_template(messages, tokenize=False)
            f.write(json.dumps({"text": text}) + "\n")
    
    # Write valid.jsonl
    with open(valid_path, "w") as f:
        for messages in val_messages:
            text = tokenizer.apply_chat_template(messages, tokenize=False)
            f.write(json.dumps({"text": text}) + "\n")
    
    print(f"Train: {len(train_messages)}, Val: {len(val_messages)}")
    print(f"Dataset saved to {dataset_dir}")
    
    # Create args object for load_dataset
    class DatasetArgs:
        def __init__(self):
            self.data = dataset_dir
            self.hf_dataset = False
            self.max_seq_length = args.max_seq
            self.train = True
            self.test = False
    
    dataset_args = DatasetArgs()
    train_data, val_data, _ = mlx_load_dataset(dataset_args, tokenizer)
    
    # Training arguments
    iters_per_epoch = max(1, len(train_data) // args.batch_size)
    total_iters = iters_per_epoch * args.epochs
    
    training_args = TrainingArgs(
        batch_size=args.batch_size,
        iters=total_iters,
        val_batches=min(10, len(val_data) // args.batch_size),
        steps_per_report=10,
        steps_per_eval=iters_per_epoch,
        steps_per_save=iters_per_epoch,
        max_seq_length=args.max_seq,
        adapter_file=adapter_file,
        grad_checkpoint=False,
        grad_accumulation_steps=GRADIENT_ACCUMULATION,
    )
    training_args.seed = 42
    training_args.num_layers = len(model.layers)
    training_args.learning_rate = args.lr
    training_args.fine_tune_type = "lora"
    training_args.optimizer = "adam"
    training_args.lora_parameters = {
        "rank": args.lora_r,
        "dropout": LORA_DROPOUT,
        "scale": 20.0,
    }
    training_args.resume_adapter_file = None
    training_args.adapter_path = output_dir
    training_args.optimizer_config = {"adam": {}, "adamw": {}}
    training_args.test = False
    training_args.test_batches = 500
    training_args.save_every = iters_per_epoch
    training_args.config = None
    training_args.lr_schedule = None
    training_args.mask_prompt = False
    training_args.report_to = None
    training_args.project_name = None
    
    print(f"\nTraining configuration:")
    print(f"  Iterations per epoch: {iters_per_epoch}")
    print(f"  Total iterations: {total_iters}")
    print(f"  Steps per report: {training_args.steps_per_report}")
    print(f"  Steps per eval: {training_args.steps_per_eval}")
    print(f"  Steps per save: {training_args.steps_per_save}")
    
    # Training callback
    class TrainingProgress:
        def __init__(self):
            self.start_time = time.time()
            self.best_val_loss = float("inf")
        
        def on_train_loss_report(self, train_info):
            elapsed = time.time() - self.start_time
            if isinstance(train_info, dict):
                print(f"Step {train_info.get('iteration', '?')}, "
                      f"Train Loss: {train_info.get('train_loss', '?'):.4f}, "
                      f"Time: {elapsed:.0f}s")
            else:
                print(f"Step {train_info.iteration}, "
                      f"Train Loss: {train_info.train_loss:.4f}, "
                      f"Time: {elapsed:.0f}s")
        
        def on_val_loss_report(self, val_info):
            elapsed = time.time() - self.start_time
            if isinstance(val_info, dict):
                val_loss = val_info.get('val_loss', 0)
                val_time = val_info.get('val_time', 0)
                iteration = val_info.get('iteration', '?')
            else:
                val_loss = val_info.val_loss
                val_time = val_info.val_time
                iteration = val_info.iteration
            
            print(f"Step {iteration}, "
                  f"Val Loss: {val_loss:.4f}, "
                  f"Val Time: {val_time:.1f}s, "
                  f"Total Time: {elapsed:.0f}s")
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
    
    callback = TrainingProgress()
    
    # Start training
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)
    
    start_time = time.time()
    train_model(
        training_args,
        model,
        train_data,
        val_data,
        training_callback=callback,
    )
    
    elapsed = time.time() - start_time
    print(f"\nTraining completed in {elapsed/60:.1f} minutes")
    print(f"Best validation loss: {callback.best_val_loss:.4f}")
    
    # Save adapter
    print(f"\nSaving adapter to {adapter_file}...")
    if os.path.exists(adapter_file):
        print("Adapter saved successfully!")
        print(f"File size: {os.path.getsize(adapter_file) / 1024:.1f} KB")
    else:
        print("Warning: Adapter file not found")
    
    # Generate Modelfile for Ollama
    modelfile = f"""FROM {MODEL_PATH}
ADAPTER {os.path.abspath(adapter_file)}

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER presence_penalty 0.2
PARAMETER frequency_penalty 0.2

SYSTEM \"\"\"You are JiuZhang-Math, a specialized mathematical reasoning model.
You excel at step-by-step proofs, symbolic computation, and problem solving.
Always show your reasoning and verify your answers.
Use both Chinese and English as appropriate.\"\"\"
"""
    modelfile_path = os.path.join(output_dir, "Modelfile")
    with open(modelfile_path, "w") as f:
        f.write(modelfile)
    print(f"Modelfile saved to {modelfile_path}")
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    print(f"\nTo test the model:")
    print(f"  python -c \"from mlx_lm import load, generate; m, t = load('{MODEL_PATH}', adapter_path='{adapter_file}'); print(generate(m, t, prompt='Solve: 3x + 7 = 22', max_tokens=100))\"")
    print(f"\nTo import to Ollama:")
    print(f"  ollama create jiuzhang-math-0.8b -f {modelfile_path}")


if __name__ == "__main__":
    main()
