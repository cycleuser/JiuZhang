#!/bin/bash
# Import trained model into Ollama

MODEL_DIR="/private/var/folders/h0/64ycsy616rbb9rsm15zj4tpm0000gn/T/pytest-of-fred/pytest-70/test_generate_all_scripts0/model/merged-final"
MODEL_NAME="jiuzhang-math-0.8B"

echo "Converting model to GGUF format..."

# Convert to GGUF (requires llama.cpp)
python -m llama_cpp.convert_hf_to_gguf \
    --outfile $MODEL_DIR/ggml-model-f16.gguf \
    --outtype f16 \
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
