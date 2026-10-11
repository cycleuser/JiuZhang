"""Low-VRAM Training Pipeline for JiuZhang Math Model.

"Slow and Steady" Training Strategy:
- Minimal VRAM usage (4-8GB) through aggressive memory optimization
- Extended training time acceptable for quality
- Supports Apple Silicon (MPS), NVIDIA GPU, and even CPU-only training

Memory Optimization Techniques:
1. QLoRA 4-bit quantization (already minimal base model memory)
2. Gradient accumulation (effective batch size without VRAM cost)
3. Gradient checkpointing (trade compute for memory)
4. CPU offloading (optimizer states on CPU RAM)
5. Minimal LoRA target modules (only most important layers)
6. Batch size = 1 (absolute minimum)
7. Mixed precision training (fp16/bf16)
8. DeepSpeed ZeRO-3 (optional, for distributed training)

Training Strategy:
- Stage 1: Arithmetic & Basic Algebra (easy patterns)
- Stage 2: Equations & Calculus Foundations
- Stage 3: Proofs & Advanced Topics
- Stage 4: Research-Level Problems
- Each stage builds on the previous, allowing gradual learning

This approach is inspired by:
- Qwen-Math training methodology
- DeepSeek-Math curriculum learning
- Microsoft's Phi series training techniques
"""

import json
import os
import time
import platform
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class LowVRAMConfig:
    """Configuration optimized for low VRAM training."""
    
    # Model settings
    base_model: str = "Qwen/Qwen3.5-0.8B"  # 0.8B from ModelScope, fits in 6GB
    model_size: str = "0.8B"
    use_modelscope: bool = True  # Use ModelScope for Chinese models
    
    # Memory optimization
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"  # Normal Float 4-bit
    bnb_4bit_compute_dtype: str = "float16"  # or bfloat16
    bnb_4bit_use_double_quant: bool = True  # Double quantization saves more memory
    
    # LoRA settings (minimal for low VRAM)
    lora_r: int = 16  # Lower rank = less memory
    lora_alpha: int = 8  # Alpha = 2 * r for stability
    lora_dropout: float = 0.05
    
    # Only train the most important layers
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "v_proj",  # Attention is most important
    ])
    
    # Training settings (slow but memory-efficient)
    batch_size: int = 1  # Absolute minimum
    gradient_accumulation: int = 32  # Effective batch = 32
    max_seq_length: int = 1024  # Shorter sequences = less memory
    num_epochs: int = 5  # More epochs to compensate for small batches
    
    # Optimization
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.05
    lr_scheduler: str = "cosine"
    gradient_checkpointing: bool = True
    optim: str = "adamw_8bit"  # 8-bit optimizer saves memory
    
    # Output
    output_dir: str = "jiuzhang-math-low-vram"
    save_steps: int = 100
    logging_steps: int = 10
    seed: int = 42
    
    # Hardware detection
    use_cpu_offload: bool = False  # Move optimizer to CPU
    use_mps: bool = False  # Apple Silicon
    use_deepspeed: bool = False
    
    # Staged training
    use_curriculum: bool = True
    stages: Dict[int, Dict] = field(default_factory=lambda: {
        1: {"name": "arithmetic", "epochs": 2, "data_filter": "arithmetic"},
        2: {"name": "equations", "epochs": 2, "data_filter": "equations"},
        3: {"name": "calculus", "epochs": 2, "data_filter": "calculus"},
        4: {"name": "proofs", "epochs": 2, "data_filter": "proofs"},
    })
    
    # Resume training
    resume_from_checkpoint: Optional[str] = None
    
    def get_effective_batch_size(self) -> int:
        return self.batch_size * self.gradient_accumulation
    
    def get_device_info(self) -> str:
        """Detect available hardware and recommend settings."""
        info = []
        
        # Check for Apple Silicon
        if platform.system() == "Darwin" and platform.processor() == "arm":
            info.append("Apple Silicon detected (MPS supported)")
            self.use_mps = True
            self.use_cpu_offload = True  # CPU offloading works well on Mac
            self.bnb_4bit_compute_dtype = "float16"
        
        # Check for NVIDIA GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                info.append(f"NVIDIA GPU: {gpu_name} ({gpu_mem:.1f}GB)")
                
                if gpu_mem < 8:
                    info.append("Low VRAM detected - using aggressive optimization")
                    self.lora_r = 8
                    self.gradient_accumulation = 64
                    self.use_cpu_offload = True
                elif gpu_mem < 16:
                    info.append("Medium VRAM - using standard optimization")
                    self.lora_r = 16
                    self.gradient_accumulation = 32
                else:
                    info.append("High VRAM - can use larger batches")
                    self.lora_r = 32
                    self.gradient_accumulation = 16
                    self.batch_size = 2
                
                if torch.cuda.is_bf16_supported():
                    self.bnb_4bit_compute_dtype = "bfloat16"
        except ImportError:
            info.append("PyTorch not installed - CPU training only")
            self.use_cpu_offload = True
            self.batch_size = 1
            self.gradient_accumulation = 64
        
        return "\n".join(info)


class LowVRAMTrainer:
    """Orchestrates low-VRAM math model training."""
    
    def __init__(self, config: LowVRAMConfig):
        self.config = config
        self.checkpoint_dir = Path(config.output_dir) / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_training_script(self) -> str:
        """Generate a complete low-VRAM training script."""
        cfg = self.config
        device_info = cfg.get_device_info()
        
        # Determine device setup
        if cfg.use_mps:
            device_code = 'device = "mps"'
            dtype_code = 'torch.float16'
        elif cfg.use_cpu_offload:
            device_code = 'device = "cpu"'
            dtype_code = 'torch.float16'
        else:
            device_code = 'device = "cuda" if torch.cuda.is_available() else "cpu"'
            dtype_code = 'torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16'
        
        # LoRA target modules based on VRAM
        target_modules_str = json.dumps(cfg.target_modules)
        
        script = f'''#!/usr/bin/env python3
"""JiuZhang Math Model - Low VRAM Training Script
Generated by LowVRAMTrainer
Hardware: {device_info}
Effective batch size: {cfg.get_effective_batch_size()}
"""

import os
import json
import time
from pathlib import Path

os.environ["WANDB_DISABLED"] = "true"

# Memory-efficient imports
try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False
    print("Unsloth not installed. Using standard transformers.")

import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, 
    BitsAndBytesConfig,
    TrainingArguments, Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

# Configuration
MODEL_NAME = "{cfg.base_model}"
DATA_PATH = "jiuzhang_distilled.jsonl"
OUTPUT_DIR = "{cfg.output_dir}"
CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, "checkpoints")
MAX_SEQ_LENGTH = {cfg.max_seq_length}
BATCH_SIZE = {cfg.batch_size}
GRADIENT_ACCUMULATION = {cfg.gradient_accumulation}
EPOCHS = {cfg.num_epochs}
LEARNING_RATE = {cfg.learning_rate}
LORA_R = {cfg.lora_r}
LORA_ALPHA = {cfg.lora_alpha}
TARGET_MODULES = {target_modules_str}

print("=" * 60)
print("JiuZhang Math Model - Low VRAM Training")
print("=" * 60)
print(f"Hardware: {device_info}")
print(f"Effective batch size: {{BATCH_SIZE * GRADIENT_ACCUMULATION}}")
print(f"LoRA rank: {{LORA_R}}")
print(f"4-bit quantization: {cfg.load_in_4bit}")
print(f"CPU offloading: {cfg.use_cpu_offload}")
print("=" * 60)

# Device setup
{device_code}
compute_dtype = {dtype_code}

# Quantization config (4-bit for minimal memory)
bnb_config = BitsAndBytesConfig(
    load_in_4bit={cfg.load_in_4bit},
    bnb_4bit_quant_type="{cfg.bnb_4bit_quant_type}",
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant={cfg.bnb_4bit_use_double_quant},
)

# Load model with quantization
print("Loading model with 4-bit quantization...")

# Resolve ModelScope model to local path if needed
MODEL_PATH = MODEL_NAME
if "{cfg.use_modelscope}":
    try:
        from modelscope import snapshot_download
        MODEL_PATH = snapshot_download(MODEL_NAME)
        print(f"ModelScope model resolved to: {{MODEL_PATH}}")
    except ImportError:
        print("modelscope not installed, falling back to HuggingFace path")
    except Exception as e:
        print(f"ModelScope download failed: {{e}}, trying HuggingFace path")

if HAS_UNSLOTH:
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_PATH,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )
else:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto" if not {cfg.use_cpu_offload} else {{"": device}},
        torch_dtype=compute_dtype,
    )

# Apply LoRA
print("Applying LoRA adapters...")
if HAS_UNSLOTH:
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
        use_gradient_checkpointing=True,
        random_state={cfg.seed},
    )
else:
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout={cfg.lora_dropout},
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

# Load dataset
print("Loading training data...")
dataset = load_dataset("json", data_files=DATA_PATH, split="train")

def format_chatml(example):
    return {{
        "text": tokenizer.apply_chat_template(example["messages"], tokenize=False)
    }}

dataset = dataset.map(format_chatml)
print(f"Loaded {{len(dataset)}} training samples")

# Training arguments (memory-optimized)
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    warmup_ratio={cfg.warmup_ratio},
    max_steps=-1,
    num_train_epochs=EPOCHS,
    learning_rate=LEARNING_RATE,
    weight_decay={cfg.weight_decay},
    lr_scheduler_type="{cfg.lr_scheduler}",
    logging_steps={cfg.logging_steps},
    save_steps={cfg.save_steps},
    save_total_limit=3,  # Keep only last 3 checkpoints
    output_dir=OUTPUT_DIR,
    seed={cfg.seed},
    bf16=compute_dtype == torch.bfloat16,
    fp16=compute_dtype == torch.float16,
    optim="{cfg.optim}",
    gradient_checkpointing={cfg.gradient_checkpointing},
    gradient_checkpointing_kwargs={{"use_reentrant": False}},
    dataloader_num_workers=0,  # Avoid memory overhead from workers
    report_to="none",
)

# Trainer
trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=training_args,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
)

# Resume from checkpoint if specified
resume_from = None
{f'resume_from = "{cfg.resume_from_checkpoint}"' if cfg.resume_from_checkpoint else '# No checkpoint to resume'}
if resume_from and Path(resume_from).exists():
    print(f"Resuming from checkpoint: {{resume_from}}")

# Training
print("\\nStarting training...")
print(f"Expected time: ~{{len(dataset) * EPOCHS // (BATCH_SIZE * GRADIENT_ACCUMULATION)}} steps")
start_time = time.time()

trainer.train(resume_from_checkpoint=resume_from)

elapsed = time.time() - start_time
print(f"\\nTraining completed in {{elapsed/60:.1f}} minutes")

# Save model
print("Saving model...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Save LoRA adapter only (much smaller)
lora_dir = os.path.join(OUTPUT_DIR, "lora-adapter")
model.save_pretrained(lora_dir)
print(f"LoRA adapter saved to {{lora_dir}}")

# Export to GGUF for Ollama
try:
    if HAS_UNSLOTH:
        model.save_pretrained_gguf(OUTPUT_DIR, tokenizer)
        print("GGUF model exported for Ollama")
except Exception as e:
    print(f"GGUF export failed: {{e}}")
    print("You can manually convert using: python -m transformers.commands.pt_to_tf")

print("\\n" + "=" * 60)
print("Training complete!")
print(f"Model: {{OUTPUT_DIR}}")
print(f"LoRA adapter: {{lora_dir}}")
print(f"Training time: {{elapsed/60:.1f}} minutes")
print("=" * 60)
'''
        
        script_path = f"train_low_vram_{cfg.model_size.replace('.', '_')}.py"
        Path(script_path).write_text(script, encoding="utf-8")
        print(f"Low-VRAM training script generated: {script_path}")
        return script_path
    
    def generate_staged_training_script(self) -> List[str]:
        """Generate separate scripts for each training stage."""
        scripts = []
        
        for stage_num, stage_config in self.config.stages.items():
            stage_name = stage_config["name"]
            stage_epochs = stage_config["epochs"]
            
            script = f'''#!/usr/bin/env python3
"""JiuZhang Math Model - Stage {stage_num}: {stage_name.title()}
Stage {stage_num} of {len(self.config.stages)}
Epochs: {stage_epochs}
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
STAGE = {stage_num}
STAGE_NAME = "{stage_name}"
MODEL_NAME = "{self.config.base_model}"
OUTPUT_DIR = "{self.config.output_dir}/stage_{stage_num}"
PREV_STAGE_DIR = "{self.config.output_dir}/stage_{stage_num - 1}" if stage_num > 1 else None
MAX_SEQ_LENGTH = {self.config.max_seq_length}
BATCH_SIZE = {self.config.batch_size}
GRADIENT_ACCUMULATION = {self.config.gradient_accumulation}
EPOCHS = {stage_epochs}
LEARNING_RATE = {self.config.learning_rate}
LORA_R = {self.config.lora_r}
LORA_ALPHA = {self.config.lora_alpha}

print(f"Stage {{STAGE}}: {{STAGE_NAME.title()}}")
print(f"Loading data for stage {{STAGE}}...")

# Load stage-specific data
all_data = load_dataset("json", data_files="jiuzhang_distilled.jsonl", split="train")

# Filter by stage category (assuming data has "category" field)
stage_data = all_data.filter(lambda x: "{stage_name}" in x.get("category", "").lower() or 
                             "{stage_name}" in x.get("problem_id", "").lower())

if len(stage_data) == 0:
    print(f"No data found for stage {{STAGE}}. Using all data.")
    stage_data = all_data

print(f"Stage {{STAGE}} data: {{len(stage_data)}} samples")

def format_chatml(example):
    return {{
        "text": tokenizer.apply_chat_template(example["messages"], tokenize=False)
    }}

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
    print(f"Loading model from previous stage: {{PREV_STAGE_DIR}}")
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
        print(f"ModelScope model resolved to: {{MODEL_PATH}}")
    except ImportError:
        print("modelscope not installed, falling back to HuggingFace path")
    except Exception as e:
        print(f"ModelScope download failed: {{e}}, trying HuggingFace path")
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
    gradient_checkpointing_kwargs={{"use_reentrant": False}},
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

print(f"\\nTraining Stage {{STAGE}}: {{STAGE_NAME.title()}}...")
start_time = time.time()
trainer.train()
elapsed = time.time() - start_time

# Save
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Stage {{STAGE}} completed in {{elapsed/60:.1f}} minutes")
print(f"Model saved to: {{OUTPUT_DIR}}")
'''
            
            script_path = f"train_stage_{stage_num}_{stage_name}.py"
            Path(script_path).write_text(script, encoding="utf-8")
            scripts.append(script_path)
            print(f"Stage {stage_num} script generated: {script_path}")
        
        return scripts
    
    def generate_merge_script(self) -> str:
        """Generate script to merge all staged checkpoints."""
        script = f'''#!/usr/bin/env python3
"""Merge all staged training checkpoints into final model."""

import os
from pathlib import Path
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

OUTPUT_DIR = "{self.config.output_dir}"
NUM_STAGES = {len(self.config.stages)}

print("Merging staged checkpoints...")

# Load the last stage model
final_dir = os.path.join(OUTPUT_DIR, f"stage_{{NUM_STAGES}}")
print(f"Loading final stage model from: {{final_dir}}")

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

print(f"Merged model saved to: {{merged_dir}}")
print("Ready for GGUF export or Ollama import!")
'''
        
        script_path = "merge_stages.py"
        Path(script_path).write_text(script, encoding="utf-8")
        print(f"Merge script generated: {script_path}")
        return script_path
    
    def generate_ollama_import_script(self) -> str:
        """Generate script to import trained model into Ollama."""
        script = f'''#!/bin/bash
# Import trained model into Ollama

MODEL_DIR="{self.config.output_dir}/merged-final"
MODEL_NAME="jiuzhang-math-{self.config.model_size}"

echo "Converting model to GGUF format..."

# Convert to GGUF (requires llama.cpp)
python -m llama_cpp.convert_hf_to_gguf \\
    --outfile $MODEL_DIR/ggml-model-f16.gguf \\
    --outtype f16 \\
    $MODEL_DIR

echo "Creating Ollama model..."

# Create Modelfile
cat > Modelfile.$MODEL_NAME << EOF
FROM $MODEL_DIR/ggml-model-f16.gguf

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER presence_penalty 0.2
PARAMETER frequency_penalty 0.2

SYSTEM """You are JiuZhang-Math, a specialized mathematical reasoning model.
You excel at step-by-step proofs, symbolic computation, and problem solving.
Always show your reasoning and verify your answers."""
EOF

# Import to Ollama
ollama create $MODEL_NAME -f Modelfile.$MODEL_NAME

echo "Model imported as: $MODEL_NAME"
echo "Test with: ollama run $MODEL_NAME 'Solve: 3x + 7 = 22'"
'''
        
        script_path = "import_to_ollama.sh"
        Path(script_path).write_text(script, encoding="utf-8")
        os.chmod(script_path, 0o755)
        print(f"Ollama import script generated: {script_path}")
        return script_path
    
    def generate_all_scripts(self) -> Dict[str, str]:
        """Generate all training scripts."""
        scripts = {}
        
        # Main low-VRAM script
        scripts["main"] = self.generate_training_script()
        
        # Staged training scripts
        scripts["stages"] = self.generate_staged_training_script()
        
        # Merge script
        scripts["merge"] = self.generate_merge_script()
        
        # Ollama import script
        scripts["ollama"] = self.generate_ollama_import_script()
        
        return scripts
    
    def print_training_guide(self):
        """Print a comprehensive training guide."""
        cfg = self.config
        device_info = cfg.get_device_info()
        
        guide = f"""
{'='*70}
JiuZhang Math Model - Low VRAM Training Guide
{'='*70}

HARDWARE DETECTION:
{device_info}

TRAINING CONFIGURATION:
  Base Model:      {cfg.base_model}
  4-bit Quant:     {cfg.load_in_4bit} ({cfg.bnb_4bit_quant_type})
  LoRA Rank:       {cfg.lora_r}
  LoRA Alpha:      {cfg.lora_alpha}
  Target Modules:  {cfg.target_modules}
  Batch Size:      {cfg.batch_size}
  Grad Accum:      {cfg.gradient_accumulation}
  Effective Batch: {cfg.get_effective_batch_size()}
  Max Seq Length:  {cfg.max_seq_length}
  Epochs:          {cfg.num_epochs}
  Learning Rate:   {cfg.learning_rate}

MEMORY OPTIMIZATIONS:
  ✓ 4-bit quantization (NF4)
  ✓ Double quantization
  ✓ Gradient checkpointing
  ✓ 8-bit Adam optimizer
  ✓ CPU offloading: {cfg.use_cpu_offload}
  ✓ Minimal LoRA targets
  ✓ Single batch size
  ✓ No dataloader workers

ESTIMATED TRAINING TIME:
  Assuming 1000 samples:
  - Steps per epoch: {1000 // cfg.get_effective_batch_size()}
  - Total steps: {1000 * cfg.num_epochs // cfg.get_effective_batch_size()}
  - Estimated time: ~{1000 * cfg.num_epochs // cfg.get_effective_batch_size() * 2 / 60:.0f} minutes
  (Actual time depends on hardware and data size)

TRAINING WORKFLOW:
  
  Option A: Single-stage training (simpler)
  ─────────────────────────────────────────
  1. python train_low_vram_{cfg.model_size.replace('.', '_')}.py
  2. bash import_to_ollama.sh
  3. ollama run jiuzhang-math-{cfg.model_size} "Solve: 3x + 7 = 22"

  Option B: Staged training (better quality)
  ──────────────────────────────────────────
  1. python train_stage_1_arithmetic.py
  2. python train_stage_2_equations.py
  3. python train_stage_3_calculus.py
  4. python train_stage_4_proofs.py
  5. python merge_stages.py
  6. bash import_to_ollama.sh
  7. ollama run jiuzhang-math-{cfg.model_size} "Solve: 3x + 7 = 22"

RESUMING TRAINING:
  If training is interrupted, resume with:
  python train_low_vram_{cfg.model_size.replace('.', '_')}.py --resume_from_checkpoint <checkpoint_path>

TROUBLESHOOTING:
  - Out of memory: Reduce lora_r, increase gradient_accumulation
  - Training too slow: Increase batch_size if VRAM allows
  - Model not learning: Increase epochs, check data quality
  - Ollama import fails: Ensure llama.cpp is installed

{'='*70}
"""
        print(guide)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JiuZhang Low-VRAM Math Model Trainer")
    parser.add_argument("--model", default="Qwen/Qwen3.5-0.8B", help="Base model (ModelScope)")
    parser.add_argument("--size", default="0.8B", help="Model size label")
    parser.add_argument("--output", default="jiuzhang-math-low-vram", help="Output directory")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--grad-accum", type=int, default=32, help="Gradient accumulation steps")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--seq-len", type=int, default=1024, help="Max sequence length")
    parser.add_argument("--resume", default="", help="Resume from checkpoint")
    parser.add_argument("--staged", action="store_true", help="Use staged training")
    parser.add_argument("--guide", action="store_true", help="Print training guide only")
    args = parser.parse_args()

    config = LowVRAMConfig(
        base_model=args.model,
        model_size=args.size,
        output_dir=args.output,
        lora_r=args.lora_r,
        gradient_accumulation=args.grad_accum,
        num_epochs=args.epochs,
        max_seq_length=args.seq_len,
        resume_from_checkpoint=args.resume if args.resume else None,
    )

    trainer = LowVRAMTrainer(config)

    if args.guide:
        trainer.print_training_guide()
        return

    if args.staged:
        scripts = trainer.generate_all_scripts()
        trainer.print_training_guide()
    else:
        trainer.generate_training_script()
        trainer.generate_ollama_import_script()
        trainer.print_training_guide()


if __name__ == "__main__":
    main()