# JiuZhang 数学模型训练指南 / Math Model Training Guide

## 概述 / Overview

本指南介绍如何使用 JiuZhang 项目训练一个专门的数学推理小模型（基于 Qwen3.5-0.8B）。

This guide explains how to train a specialized mathematical reasoning model using JiuZhang (based on Qwen3.5-0.8B).

## 训练数据 / Training Data

### 数据来源 / Data Sources

| 文件 | 样本数 | 说明 |
|------|--------|------|
| `jiuzhang_curriculum.jsonl` | 1,799 | 课程学习数据（算术→方程→微积分→证明）|
| `jiuzhang_self_correction.jsonl` | 98 | 自我纠正数据（错误→纠正）|
| `jiuzhang_rejection_sampling.jsonl` | 60 | 拒绝采样数据（SymPy 验证正确）|
| **总计** | **1,957** | |

### 数据分布 / Data Distribution

```
proof_induction_power_sum:   133  #############
proof_induction_sum :   133  #############
proof_irrational    :   133  #############
limit               :   125  ############
derivative          :   125  ############
integral            :   125  ############
linear_eq           :   125  ############
square              :   100  ##########
addition            :   100  ##########
lcm_gcd             :   100  ##########
...
```

## 快速开始 / Quick Start

### 一键训练 / One-Command Training

```bash
# 完整流程：准备数据 → 下载模型 → 生成训练脚本
python train_math_model_end_to_end.py

# 或分步执行：
python train_math_model_end_to_end.py --step prepare   # 仅准备数据
python train_math_model_end_to_end.py --step download  # 仅下载模型
python train_math_model_end_to_end.py --step train     # 仅生成训练脚本
python train_math_model_end_to_end.py --step export    # 仅导出到 Ollama
```

### 训练步骤 / Training Steps

#### 1. 准备训练数据

```bash
python train_math_model_end_to_end.py --step prepare
```

输出：`jiuzhang_merged_training.jsonl`（1,957 样本）

#### 2. 下载模型

```bash
python train_math_model_end_to_end.py --step download
```

从 ModelScope 下载 `Qwen/Qwen3.5-0.8B`（约 1.6GB）。

#### 3. 开始训练

```bash
# 生成训练脚本
python train_math_model_end_to_end.py --step train

# 运行训练（需要安装依赖）
python train_jiuzhang_math.py
```

训练时间估计：
- Apple Silicon (M1/M2/M3): ~6 小时
- NVIDIA GPU (RTX 3060+): ~3 小时
- CPU: ~24 小时（不推荐）

#### 4. 导出到 Ollama

```bash
python train_math_model_end_to_end.py --step export
```

## 依赖安装 / Dependencies

### 基础依赖

```bash
pip install flask requests rich sympy numpy matplotlib
```

### 训练依赖

```bash
pip install modelscope transformers peft trl datasets bitsandbytes accelerate
```

### Apple Silicon 优化

```bash
# PyTorch with MPS support
pip install torch torchvision torchaudio
```

### NVIDIA GPU 优化

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
pip install unsloth  # 可选，加速训练
```

## 训练配置 / Training Configuration

### 默认配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 基础模型 | `Qwen/Qwen3.5-0.8B` | 0.8B 参数 |
| LoRA rank | 16 | 低秩适应器维度 |
| LoRA alpha | 32 | 缩放因子 |
| 学习率 | 2e-4 | 余弦衰减 |
| 批次大小 | 1 | 最小显存占用 |
| 梯度累积 | 32 | 有效批次 = 32 |
| 训练轮数 | 3 | 可根据需要调整 |
| 最大序列长度 | 1024 | 适合数学问题 |
| 量化 | 4-bit NF4 | 减少显存使用 |

### 自定义配置

```bash
python train_math_model_end_to_end.py \
    --epochs 5 \
    --lora-r 32 \
    --output my-math-model
```

## 训练脚本说明 / Training Scripts

### 生成的文件

| 文件 | 说明 |
|------|------|
| `train_jiuzhang_math.py` | 主训练脚本（QLoRA）|
| `jiuzhang_merged_training.jsonl` | 合并的训练数据 |
| `jiuzhang-math-0.8b/` | 输出模型目录 |

### 分阶段训练脚本

如果需要更细粒度的控制，可以使用分阶段训练：

```bash
python train_stage_1_arithmetic.py   # 阶段 1: 算术
python train_stage_2_equations.py    # 阶段 2: 方程
python train_stage_3_calculus.py     # 阶段 3: 微积分
python train_stage_4_proofs.py       # 阶段 4: 证明
```

## 模型评估 / Model Evaluation

训练完成后，可以使用 JiuZhang 的基准测试评估模型：

```bash
jiuzhang benchmark --model jiuzhang-math-0.8b
```

## 常见问题 / FAQ

### Q: 训练需要多少显存？

A: 使用 4-bit 量化 + LoRA，约需 4-6GB 显存。Apple Silicon 使用统一内存，建议 8GB+。

### Q: 可以在 CPU 上训练吗？

A: 可以，但会非常慢（约 24 小时）。建议使用 GPU 或 Apple Silicon。

### Q: 如何恢复中断的训练？

A: 训练脚本会自动保存检查点。修改 `train_jiuzhang_math.py` 中的 `resume_from_checkpoint` 参数。

### Q: 模型质量如何？

A: 训练后的模型应该能够：
- 解决基础代数方程
- 计算导数和积分
- 进行简单的数学证明
- 使用 SymPy 验证答案

### Q: 如何改进模型质量？

A: 
1. 增加训练轮数（`--epochs 5`）
2. 增加 LoRA rank（`--lora-r 32`）
3. 添加更多训练数据
4. 使用分阶段训练

## 技术支持 / Support

- GitHub Issues: https://github.com/cycleuser/JiuZhang/issues
- 文档: https://github.com/cycleuser/JiuZhang#readme
