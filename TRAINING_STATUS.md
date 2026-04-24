# JiuZhang 数学模型训练状态报告

## 当前状态

### 已完成
- ✅ 训练数据准备：1,957 样本（curriculum + self-correction + rejection sampling）
- ✅ 模型下载：Qwen/Qwen3.5-0.8B 从 ModelScope 下载成功
- ✅ MLX 训练脚本：`train_mlx.py` 已创建并测试通过
- ✅ LoRA 适配器训练成功（50 样本测试）
- ✅ 完整训练进行中（200 样本，3 epochs）

### 训练进度
- **当前**: 30/540 次迭代（5.6%）
- **Train loss**: 0.716（从 2.132 持续下降）
- **速度**: 0.007 it/sec
- **预计完成**: 约 21 小时
- **峰值内存**: 8.3 GB

### 关键设置
```bash
MLX_MEMORY_LIMIT=8000 python train_mlx.py \
    --epochs 3 \
    --samples 200 \
    --batch-size 1 \
    --max-seq 256 \
    --lora-r 8
```

### 测试结果（50 样本模型）
- ✅ 加法：2 + 2 = 4
- ✅ 导数：x^2 的导数 = 2x
- ✅ 乘法：15 * 23 = 345
- ✅ 证明：使用了数学定义和逻辑推导
- ⚠️ 方程：需要更多训练数据

## 训练脚本说明

| 脚本 | 用途 | 状态 |
|------|------|------|
| `train_mlx.py` | MLX 训练脚本（Apple Silicon）| ✅ 可用 |
| `TRAINING_GUIDE.md` | 训练使用指南 | ✅ 可用 |

## 使用方法

### 快速测试（5 分钟）
```bash
MLX_MEMORY_LIMIT=8000 python train_mlx.py --epochs 1 --samples 50 --batch-size 1 --max-seq 128 --lora-r 4
```

### 完整训练（约 21 小时）
```bash
MLX_MEMORY_LIMIT=8000 python train_mlx.py --epochs 3 --samples 200 --batch-size 1 --max-seq 256 --lora-r 8
```

### 测试训练好的模型
```bash
python -c "
from mlx_lm import load, generate
model, tokenizer = load('/Users/fred/.cache/modelscope/hub/models/Qwen/Qwen3___5-0___8B', adapter_path='jiuzhang-math-0.8b')
print(generate(model, tokenizer, prompt='Solve: 3x + 7 = 22', max_tokens=100))
"
```

## 硬件要求

| 配置 | 内存 | 时间 |
|------|------|------|
| Apple Silicon M4 (16GB) | 8.3 GB | ~21 小时 |
| Apple Silicon M1/M2 (16GB) | 8.3 GB | ~30 小时 |

## 下一步

1. 等待当前训练完成（约 21 小时）
2. 测试训练好的模型
3. 根据需要调整参数重新训练
