#!/usr/bin/env python3
"""
JiuZhang MLX LoRA 低资源长期训练脚本
─────────────────────────────────────
• 专为 Apple MacBook Air M4 16GB 持续运行优化
• 后台 nice + nohup 运行时不影响前台操作
• 每 N 步自动保存，Ctrl+C 安全中断并可恢复

用法:
    python scripts/train_mlx_lora.py               # 首次训练
    python scripts/train_mlx_lora.py --resume      # 恢复上次训练
    python scripts/train_mlx_lora.py --epochs 1    # 快速验证 (约5分钟)
"""
import os
import sys
import time
import json
import argparse
import signal
from pathlib import Path
from types import SimpleNamespace

import mlx.core as mx
from mlx_lm import load
from mlx_lm.lora import (
    load_dataset as mlx_load_dataset,
    train_model as mlx_train_model,
)

# ════════════════════════════════════════
#  默认配置（越小越省资源）
# ════════════════════════════════════════
DEFAULTS = {
    "model":   "/Users/fred/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B",
    "data":    "jiuzhang_merged_training.jsonl",
    "output":  "outputs/jiuzhang-math-0.8b",
    "max_seq": 256,
    "lora_r":  4,
    "lora_alpha": 8,
    "lora_dropout": 0.05,
    "lr":      8e-5,
    "epochs":  5,
    "batch_size":   1,
    "grad_accum":   8,
    "val_batches":  5,
    "steps_report": 10,
    "steps_eval":   200,
    "steps_save":   100,
    "seed": 42,
}


# ──────────────────────────────────────
#  进度回调
# ──────────────────────────────────────
class ProgressCB:
    """mlx_lm TrainingCallback 兼容"""
    def __init__(self):
        self.start = time.time()
        self.best_val = float("inf")

    def on_train_loss_report(self, info):
        it  = info.iteration if hasattr(info, "iteration") else info.get("iteration", 0)
        loss = float(info.train_loss if hasattr(info, "train_loss")
                     else info.get("train_loss", float("inf")))
        t = time.time() - self.start
        print(f"[{t:07.0f}s] Step {it:05d} | train_loss={loss:.5f}", flush=True)

    def on_val_loss_report(self, info):
        it  = int(info.iteration if hasattr(info, "iteration") else info.get("iteration", 0))
        vloss = float(info.val_loss if hasattr(info, "val_loss")
                      else info.get("val_loss", float("inf")))
        t = time.time() - self.start
        if vloss < self.best_val:
            self.best_val = vloss
            print(f"[{t:07.0f}s] Step {it:05d} | 🔥 NEW BEST val_loss={vloss:.5f}", flush=True)
        else:
            print(f"[{t:07.0f}s] Step {it:05d} | val_loss={vloss:.5f}", flush=True)


# ──────────────────────────────────────
#  CLI
# ──────────────────────────────────────
def build_args():
    p = argparse.ArgumentParser(description="JiuZhang Low-Resource MLX LoRA Training")
    p.add_argument("--model",      default=DEFAULTS["model"],      help="Base model local path")
    p.add_argument("--data",       default=DEFAULTS["data"],       help="Training JSONL")
    p.add_argument("--output",     default=DEFAULTS["output"],     help="Output directory")
    p.add_argument("--max-seq",    type=int, default=DEFAULTS["max_seq"])
    p.add_argument("--lora-r",     type=int, default=DEFAULTS["lora_r"])
    p.add_argument("--lora-alpha", type=int, default=DEFAULTS["lora_alpha"])
    p.add_argument("--lora-dropout", type=float, default=DEFAULTS["lora_dropout"])
    p.add_argument("--lr",         type=float, default=DEFAULTS["lr"])
    p.add_argument("--epochs",     type=int, default=DEFAULTS["epochs"])
    p.add_argument("--batch-size", type=int, default=DEFAULTS["batch_size"])
    p.add_argument("--grad-accum", type=int, default=DEFAULTS["grad_accum"])
    p.add_argument("--val-batches", type=int, default=DEFAULTS["val_batches"])
    p.add_argument("--steps-report", type=int, default=DEFAULTS["steps_report"])
    p.add_argument("--steps-eval",   type=int, default=DEFAULTS["steps_eval"])
    p.add_argument("--steps-save",   type=int, default=DEFAULTS["steps_save"])
    p.add_argument("--seed",       type=int, default=DEFAULTS["seed"])
    p.add_argument("--resume",     action="store_true", help="Resume from latest checkpoint")
    return p.parse_args()


# ──────────────────────────────────────
#  主流程
# ──────────────────────────────────────
def main():
    cli = build_args()
    os.makedirs(cli.output, exist_ok=True)

    print("=" * 60)
    print("JiuZhang Math – Low-Resource MLX LoRA Training")
    print("=" * 60)
    print(f"  Device      : Apple Silicon M4 (MLX)")
    print(f"  Model       : {cli.model}")
    print(f"  Data        : {cli.data}")
    print(f"  Output      : {cli.output}")
    print(f"  Max Seq     : {cli.max_seq}")
    print(f"  LoRA        : r={cli.lora_r}, α={cli.lora_alpha}")
    print(f"  Epochs      : {cli.epochs}")
    print(f"  Batch/Accum : {cli.batch_size} / {cli.grad_accum}")
    print(f"  LR          : {cli.lr}")
    print(f"  Save every  : {cli.steps_save} steps")
    print("=" * 60)

    # ── 加载模型 ──
    print("\n⏳ Loading model...")
    t0 = time.time()
    model, tokenizer = load(cli.model)
    print(f"✅ Model loaded ({time.time() - t0:.1f}s)")

    # 保存 tokenizer
    tokenizer.save_pretrained(cli.output)

    # ── 准备数据集 ──
    print("\n📂 Preparing dataset...")
    all_msgs = []
    with open(cli.data, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "messages" in obj:
                    all_msgs.append(obj["messages"])
            except json.JSONDecodeError:
                continue

    split = int(len(all_msgs) * 0.95)
    train_msgs, val_msgs = all_msgs[:split], all_msgs[split:]
    print(f"   Train: {len(train_msgs)} | Val: {len(val_msgs)}")

    dataset_dir = Path(cli.output) / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    train_path = dataset_dir / "train.jsonl"
    valid_path = dataset_dir / "valid.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for msgs in train_msgs:
            text = tokenizer.apply_chat_template(msgs, tokenize=False)
            f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

    with open(valid_path, "w", encoding="utf-8") as f:
        for msgs in val_msgs:
            text = tokenizer.apply_chat_template(msgs, tokenize=False)
            f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

    # mlx_lm 格式化加载
    ds_ns = SimpleNamespace(
        data=str(dataset_dir), hf_dataset=False,
        max_seq_length=cli.max_seq, train=True, test=False,
    )
    train_set, valid_set, _ = mlx_load_dataset(ds_ns, tokenizer)

    # ── 统计与计划 ──
    iters_per_epoch = max(1, len(train_msgs) // cli.batch_size)
    total_iters = iters_per_epoch * cli.epochs
    print(f"\n📊 Plan: {iters_per_epoch} it/epoch × {cli.epochs} epochs = {total_iters} total")
    print(f"   ~{total_iters * 20 // 60:02d}:{total_iters * 20 % 60:02d} h est. (background low-prio)")
    print("=" * 60)

    # ── 组装 train_model 所需 Namespace ──
    adapter_path = Path(cli.output)
    resume_file = None
    if cli.resume:
        cand = adapter_path / "adapters.safetensors"
        if cand.exists():
            resume_file = str(cand)
            print(f"\n🔄 Resuming from {resume_file}")

    tune_ns = SimpleNamespace(
        model=cli.model,
        data=str(dataset_dir),
        hf_dataset=False,

        fine_tune_type="lora",
        num_layers=len(model.layers),
        lora_parameters={
            "rank": cli.lora_r,
            "alpha": cli.lora_alpha,
            "dropout": cli.lora_dropout,
            "scale": cli.lora_alpha / cli.lora_r,
        },
        learning_rate=cli.lr,
        lr_schedule=None,
        optimizer="adam",
        optimizer_config={"adam": {}, "adamw": {}, "sgd": {}, "adafactor": {}, "muon": {}},
        grad_checkpoint=True,
        grad_accumulation_steps=cli.grad_accum,

        iters=total_iters,
        batch_size=cli.batch_size,
        val_batches=cli.val_batches,
        steps_per_report=cli.steps_report,
        steps_per_eval=cli.steps_eval,
        steps_per_save=cli.steps_save,
        max_seq_length=cli.max_seq,

        save_every=cli.steps_save,
        adapter_path=str(adapter_path),
        resume_adapter_file=resume_file,
        seed=cli.seed,

        test=False,
        test_batches=500,
        config=None,
        report_to=None,
        project_name=None,
        mask_prompt=False,
    )

    # 安全中断
    def _on_sigint(*_):
        print("\n⚠️ SIGINT received – checkpoint will auto-save after current step.", flush=True)
    signal.signal(signal.SIGINT, _on_sigint)

    # ── 训练 ──
    print("\n🚀 Starting training (Ctrl+C to interrupt)…\n")
    try:
        mlx_train_model(tune_ns, model, train_set, valid_set, training_callback=ProgressCB())
    except KeyboardInterrupt:
        print("\n✅ Interrupted. Use --resume to continue.\n")
        return
    except Exception as e:
        print(f"\n❌ Training error: {e}\n")
        raise

    # ── 结束 ──
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("🎉 Training complete!")
    print(f"   Elapsed: {elapsed / 3600:.2f} h")
    print(f"   Output: {cli.output}")
    print("=" * 60)

    # 生成 Ollama Modelfile
    adapter_file = adapter_path / "adapters.safetensors"
    if adapter_file.exists():
        modelfile = adapter_path / "Modelfile"
        modelfile.write_text(
            f"""FROM {cli.model}\nADAPTER {os.path.abspath(adapter_file)}\n\nPARAMETER temperature 0.1\nPARAMETER top_p 0.9\nPARAMETER num_ctx 4096\n\nSYSTEM \"\"\"You are JiuZhang-Math, a specialized mathematical reasoning model.
You excel at step-by-step proofs, symbolic computation, and problem solving.\"\"\"
"""
        )
        print(f"\n📝 Ollama Modelfile written: {modelfile}")
        print(f"   Import: ollama create jiuzhang-math -f {modelfile}")


if __name__ == "__main__":
    main()
