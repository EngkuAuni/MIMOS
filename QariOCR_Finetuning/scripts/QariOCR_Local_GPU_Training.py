"""
QariOCR Local GPU Fine-Tuning Script
Optimized for local high-GPU machines (RTX 4090, A100, etc.)
Based on Unsloth framework for efficient training
"""

import os
import json
import torch
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Unsloth imports
from unsloth import FastVisionModel
from unsloth.trainer import UnslothVisionDataCollator
from trl import SFTTrainer, SFTConfig
from datasets import Dataset
from transformers import TextStreamer
from PIL import Image

class LocalQariOCRTrainer:
    """Local GPU trainer for QariOCR fine-tuning"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
    def setup_environment(self):
        """Setup training environment"""
        print("🔧 Setting up training environment...")
        
        # Set CUDA device
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"✅ Found {device_count} GPU(s)")
            for i in range(device_count):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("❌ No CUDA GPUs found!")
            return False
        
        # Set memory optimization
        os.environ["CUDA_VISIBLE_DEVICES"] = self.config.get("gpu_ids", "0")
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        return True
    
    def load_model(self):
        """Load base model and configure for training"""
        print("🤖 Loading Qwen2-VL model...")
        
        try:
            # Load model with optimizations
            self.model, self.tokenizer = FastVisionModel.from_pretrained(
                model_name=self.config["base_model"],
                max_seq_length=self.config["max_seq_length"],
                dtype=self.config.get("dtype", None),
                load_in_4bit=self.config.get("load_in_4bit", True),
                use_gradient_checkpointing="unsloth",
                device_map="auto"
            )
            
            print(f"✅ Model loaded: {self.config['base_model']}")
            print(f"   Max sequence length: {self.config['max_seq_length']}")
            print(f"   4-bit quantization: {self.config.get('load_in_4bit', True)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False
    
    def configure_lora(self):
        """Configure LoRA adapter"""
        print("🔧 Configuring LoRA adapter...")
        
        try:
            self.model = FastVisionModel.get_peft_model(
                model=self.model,
                r=self.config["lora_r"],
                target_modules=self.config.get("target_modules", "all-linear"),
                lora_alpha=self.config["lora_alpha"],
                lora_dropout=self.config["lora_dropout"],
                bias=self.config.get("bias", "none"),
                use_gradient_checkpointing="unsloth",
                random_state=3407,
                use_rslora=False,
                loftq_config=None,
            )
            
            print(f"✅ LoRA configured:")
            print(f"   r: {self.config['lora_r']}")
            print(f"   alpha: {self.config['lora_alpha']}")
            print(f"   dropout: {self.config['lora_dropout']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure LoRA: {e}")
            return False
    
    def load_dataset(self):
        """Load and prepare training dataset"""
        print("📚 Loading training dataset...")
        
        try:
            # Load training data
            train_data_path = self.config["train_data_path"]
            val_data_path = self.config["val_data_path"]
            
            with open(train_data_path, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            
            with open(val_data_path, 'r', encoding='utf-8') as f:
                val_data = json.load(f)
            
            print(f"✅ Dataset loaded:")
            print(f"   Training samples: {len(train_data)}")
            print(f"   Validation samples: {len(val_data)}")
            
            # Convert to datasets
            train_dataset = Dataset.from_list(train_data)
            val_dataset = Dataset.from_list(val_data)
            
            return train_dataset, val_dataset
            
        except Exception as e:
            print(f"❌ Failed to load dataset: {e}")
            return None, None
    
    def setup_trainer(self, train_dataset, val_dataset):
        """Setup SFT trainer"""
        print("🏋️ Setting up trainer...")
        
        try:
            # Configure training arguments
            training_args = SFTConfig(
                per_device_train_batch_size=self.config["per_device_train_batch_size"],
                per_device_eval_batch_size=self.config["per_device_eval_batch_size"],
                gradient_accumulation_steps=self.config["gradient_accumulation_steps"],
                warmup_steps=self.config["warmup_steps"],
                num_train_epochs=self.config["num_train_epochs"],
                learning_rate=self.config["learning_rate"],
                fp16=not torch.cuda.is_bf16_supported(),
                bf16=torch.cuda.is_bf16_supported(),
                logging_steps=self.config["logging_steps"],
                optim=self.config.get("optim", "adamw_8bit"),
                weight_decay=self.config.get("weight_decay", 0.01),
                lr_scheduler_type=self.config.get("lr_scheduler_type", "linear"),
                seed=self.config.get("seed", 3407),
                output_dir=self.config["output_dir"],
                save_steps=self.config["save_steps"],
                save_total_limit=self.config.get("save_total_limit", 1),
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                eval_strategy="steps",
                eval_steps=self.config["eval_steps"],
                report_to="none",
                remove_unused_columns=False,
                dataset_text_field="",
                dataset_kwargs={"skip_prepare_dataset": True},
            )
            
            # Create trainer
            self.trainer = SFTTrainer(
                model=self.model,
                tokenizer=self.tokenizer,
                data_collator=UnslothVisionDataCollator(self.model, self.tokenizer),
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                args=training_args,
            )
            
            print("✅ Trainer configured:")
            print(f"   Batch size: {self.config['per_device_train_batch_size']}")
            print(f"   Epochs: {self.config['num_train_epochs']}")
            print(f"   Learning rate: {self.config['learning_rate']}")
            print(f"   Output dir: {self.config['output_dir']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup trainer: {e}")
            return False
    
    def train(self):
        """Start training"""
        print("🚀 Starting training...")
        
        try:
            # Enable training mode
            FastVisionModel.for_training(self.model)
            
            # Start training
            trainer_stats = self.trainer.train()
            
            print("✅ Training completed!")
            print(f"   Training loss: {trainer_stats.training_loss:.4f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    
    def save_model(self):
        """Save the trained model"""
        print("💾 Saving model...")
        
        try:
            # Save model
            self.model.save_pretrained(self.config["output_dir"])
            self.tokenizer.save_pretrained(self.config["output_dir"])
            
            # Save training metadata
            metadata = {
                "model_name": self.config.get("model_name", "QariOCR-Local"),
                "version": self.config.get("version", "1.0"),
                "type": "finetuned",
                "base_model": self.config["base_model"],
                "training_date": datetime.now().isoformat(),
                "training_config": self.config,
                "dataset": {
                    "train_samples": len(self.trainer.train_dataset),
                    "val_samples": len(self.trainer.eval_dataset)
                },
                "performance": {
                    "final_loss": getattr(self.trainer.state, 'log_history', [{}])[-1].get('train_loss', 0),
                    "eval_loss": getattr(self.trainer.state, 'log_history', [{}])[-1].get('eval_loss', 0)
                },
                "capabilities": [
                    "Uthmani text extraction",
                    "Error detection (CRITICAL/MAJOR/MINOR)",
                    "Diacritic verification",
                    "Letter form verification",
                    "Rasm Uthmani compliance",
                    "KDN standard alignment"
                ],
                "status": "available"
            }
            
            metadata_path = os.path.join(self.config["output_dir"], "training_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Model saved to: {self.config['output_dir']}")
            print(f"   Metadata saved to: {metadata_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save model: {e}")
            return False
    
    def test_model(self):
        """Test the trained model"""
        print("🧪 Testing model...")
        
        try:
            # Switch to inference mode
            FastVisionModel.for_inference(self.model)
            
            # Test with a sample image
            test_image_path = self.config.get("test_image_path")
            if test_image_path and os.path.exists(test_image_path):
                test_image = Image.open(test_image_path).convert("RGB")
                
                # Prepare test prompt
                test_prompt = "Extract the Arabic text from this Quran page with high accuracy."
                
                # Generate response
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": test_prompt},
                            {"type": "image", "image": test_image}
                        ]
                    }
                ]
                
                input_text = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                
                inputs = self.tokenizer(
                    input_text, 
                    images=[test_image], 
                    return_tensors="pt"
                ).to(self.model.device)
                
                # Generate
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=512,
                        temperature=0.0,
                        do_sample=False
                    )
                
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                print("✅ Model test successful!")
                print(f"   Test response: {response[:100]}...")
                
            return True
            
        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return False

def load_config(config_path: str) -> Dict:
    """Load training configuration"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_default_config(output_path: str):
    """Create default training configuration"""
    config = {
        # Model configuration
        "base_model": "unsloth/qwen2-vl-2b-instruct-bnb-4bit",
        "max_seq_length": 2048,
        "dtype": None,  # Auto-detect
        "load_in_4bit": True,
        
        # LoRA configuration
        "lora_r": 16,
        "lora_alpha": 16,
        "lora_dropout": 0.1,
        "bias": "none",
        "target_modules": "all-linear",
        
        # Training configuration
        "per_device_train_batch_size": 2,
        "per_device_eval_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "warmup_steps": 50,
        "num_train_epochs": 3,
        "learning_rate": 2e-4,
        "logging_steps": 5,
        "eval_steps": 25,
        "save_steps": 25,
        "save_total_limit": 1,
        "optim": "adamw_8bit",
        "weight_decay": 0.01,
        "lr_scheduler_type": "linear",
        "seed": 3407,
        
        # Data configuration
        "train_data_path": "training_data/enhanced/train_enhanced.json",
        "val_data_path": "training_data/enhanced/val_enhanced.json",
        
        # Output configuration
        "output_dir": "models/FT2_QariOCR",
        "model_name": "QariOCR-Local-v2",
        "version": "2.0",
        
        # GPU configuration
        "gpu_ids": "0",  # Comma-separated for multi-GPU
        
        # Test configuration
        "test_image_path": "database/reference_imgs/001.jpg"
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Default configuration created: {output_path}")

def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="QariOCR Local GPU Training")
    parser.add_argument("--config", type=str, default="training_config.json", 
                       help="Path to training configuration file")
    parser.add_argument("--create-config", action="store_true",
                       help="Create default configuration file")
    parser.add_argument("--test-only", action="store_true",
                       help="Only test existing model")
    
    args = parser.parse_args()
    
    # Create default config if requested
    if args.create_config:
        create_default_config(args.config)
        return
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"❌ Configuration file not found: {args.config}")
        print("   Use --create-config to create a default configuration")
        return
    
    config = load_config(args.config)
    
    # Initialize trainer
    trainer = LocalQariOCRTrainer(config)
    
    # Test only mode
    if args.test_only:
        if trainer.setup_environment() and trainer.load_model():
            trainer.test_model()
        return
    
    # Full training pipeline
    print("🚀 Starting QariOCR Local GPU Training")
    print("=" * 50)
    
    # Setup environment
    if not trainer.setup_environment():
        return
    
    # Load model
    if not trainer.load_model():
        return
    
    # Configure LoRA
    if not trainer.configure_lora():
        return
    
    # Load dataset
    train_dataset, val_dataset = trainer.load_dataset()
    if train_dataset is None:
        return
    
    # Setup trainer
    if not trainer.setup_trainer(train_dataset, val_dataset):
        return
    
    # Train model
    if not trainer.train():
        return
    
    # Save model
    if not trainer.save_model():
        return
    
    # Test model
    trainer.test_model()
    
    print("=" * 50)
    print("🎉 Training completed successfully!")
    print(f"   Model saved to: {config['output_dir']}")
    print("   Ready for production use!")

if __name__ == "__main__":
    main()
