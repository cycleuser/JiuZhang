"""Tests for Low-VRAM Training Pipeline."""

import pytest
import os
import json
from pathlib import Path

from jiuzhang.low_vram_training import LowVRAMConfig, LowVRAMTrainer


class TestLowVRAMConfig:
    def test_default_config(self):
        cfg = LowVRAMConfig()
        assert cfg.base_model == "Qwen/Qwen3.5-0.8B"
        assert cfg.load_in_4bit is True
        assert cfg.batch_size == 1
        assert cfg.gradient_accumulation == 32
        assert cfg.get_effective_batch_size() == 32

    def test_effective_batch_size(self):
        cfg = LowVRAMConfig(batch_size=1, gradient_accumulation=64)
        assert cfg.get_effective_batch_size() == 64

    def test_device_info(self):
        cfg = LowVRAMConfig()
        info = cfg.get_device_info()
        assert isinstance(info, str)
        assert len(info) > 0

    def test_custom_config(self):
        cfg = LowVRAMConfig(
            base_model="Qwen/Qwen2.5-1.5B-Instruct",
            lora_r=32,
            gradient_accumulation=16,
            num_epochs=3,
        )
        assert cfg.base_model == "Qwen/Qwen2.5-1.5B-Instruct"
        assert cfg.lora_r == 32
        assert cfg.get_effective_batch_size() == 16


class TestLowVRAMTrainer:
    def test_generate_training_script(self, tmp_path):
        cfg = LowVRAMConfig(output_dir=str(tmp_path / "model"))
        trainer = LowVRAMTrainer(cfg)
        script_path = trainer.generate_training_script()
        
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        
        assert "BitsAndBytesConfig" in content
        assert "load_in_4bit=True" in content
        assert "gradient_accumulation_steps" in content
        assert "gradient_checkpointing" in content

    def test_generate_staged_training_script(self, tmp_path):
        cfg = LowVRAMConfig(output_dir=str(tmp_path / "model"))
        trainer = LowVRAMTrainer(cfg)
        scripts = trainer.generate_staged_training_script()
        
        assert len(scripts) == 4  # 4 stages
        for script_path in scripts:
            assert os.path.exists(script_path)
            with open(script_path) as f:
                content = f.read()
            assert "Stage" in content
            assert "BitsAndBytesConfig" in content

    def test_generate_merge_script(self, tmp_path):
        cfg = LowVRAMConfig(output_dir=str(tmp_path / "model"))
        trainer = LowVRAMTrainer(cfg)
        script_path = trainer.generate_merge_script()
        
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "merge_and_unload" in content

    def test_generate_ollama_import_script(self, tmp_path):
        cfg = LowVRAMConfig(output_dir=str(tmp_path / "model"))
        trainer = LowVRAMTrainer(cfg)
        script_path = trainer.generate_ollama_import_script()
        
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "ollama create" in content
        assert "jiuzhang-math" in content

    def test_generate_all_scripts(self, tmp_path):
        cfg = LowVRAMConfig(output_dir=str(tmp_path / "model"))
        trainer = LowVRAMTrainer(cfg)
        scripts = trainer.generate_all_scripts()
        
        assert "main" in scripts
        assert "stages" in scripts
        assert "merge" in scripts
        assert "ollama" in scripts
        assert len(scripts["stages"]) == 4

    def test_print_training_guide(self, capsys):
        cfg = LowVRAMConfig()
        trainer = LowVRAMTrainer(cfg)
        trainer.print_training_guide()
        
        captured = capsys.readouterr()
        assert "Low VRAM Training Guide" in captured.out
        assert "TRAINING CONFIGURATION" in captured.out
        assert "MEMORY OPTIMIZATIONS" in captured.out
        assert "ESTIMATED TRAINING TIME" in captured.out