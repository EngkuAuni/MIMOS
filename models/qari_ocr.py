# Qari OCR wrapper, checkpoint loader

import os
from PIL import Image

class QariOCR:
    def __init__(self, model_path, fallback_warn=False):
        self.model_path = model_path
        self.model = None
        self.processor = None
        self.device = "cpu"  # Default to CPU for Intel Mac
        self.max_new_tokens = 2048  # Full page extraction (was 128 - too low!)
        self.last_error = None
        
        # Try to load the full model with PyTorch + PEFT adapter on CPU (no bitsandbytes)
        try:
            # Ensure libraries import
            import torch
            
            # Compatibility shim for older PyTorch versions
            if not hasattr(torch.compiler, 'is_compiling'):
                torch.compiler.is_compiling = lambda: False
            
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            from peft import PeftModel
            from qwen_vl_utils import process_vision_info

            # Check for available acceleration: CUDA (NVIDIA), MPS (Apple Metal), or CPU
            use_gpu = os.environ.get("USE_GPU", "false").lower() == "true"
            use_mps = os.environ.get("USE_MPS", "false").lower() == "true"
            
            # Determine best device
            if torch.cuda.is_available() and use_gpu:
                self.device = "cuda"
                print(f"🔍 CUDA Available: True")
                print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
                print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() and use_mps:
                self.device = "mps"
                print(f"🔍 Apple Metal (MPS) Available: True")
                print(f"🍎 Running on Apple Silicon with Metal Performance Shaders")
                print(f"⚡ GPU acceleration enabled for Mac Studio M4")
            else:
                self.device = "cpu"
                print(f"🔍 Using CPU (no GPU acceleration)")
            
            print(f"🎯 Selected device: {self.device}")

            # Load base Qwen2-VL Instruct model
            base_model_id = "Qwen/Qwen2-VL-2B-Instruct"
            
            # Configure model loading based on device
            if self.device == "cuda":
                # NVIDIA GPU mode - use FP16 for faster inference
                print("📦 Loading model for NVIDIA GPU (FP16)...")
                base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                    base_model_id,
                    device_map="auto",  # Automatic GPU placement
                    torch_dtype=torch.float16  # FP16 for speed
                )
            elif self.device == "mps":
                # Apple Metal mode - use FP16 for Mac Studio M4
                print("📦 Loading model for Apple Metal (FP16)...")
                base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                    base_model_id,
                    device_map=None,  # MPS doesn't use device_map
                    torch_dtype=torch.float16  # FP16 works on M4
                )
                # Move to MPS device
                base_model = base_model.to(self.device)
            else:
                # CPU mode - use FP32
                print("📦 Loading model for CPU (FP32)...")
                base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                    base_model_id,
                    device_map=None,
                    torch_dtype=torch.float32
                )

            # Attach PEFT adapter weights from the provided repo (model_path)
            self.model = PeftModel.from_pretrained(
                base_model,
                model_path,
                is_trainable=False
            )

            # Processor (tokenizer + image processor)
            self.processor = AutoProcessor.from_pretrained(base_model_id)
            print(f"✅ Qari OCR model loaded with PEFT adapter from {model_path} on {self.device}")

        except ImportError as e:
            if fallback_warn:
                print(f"Warning: PyTorch/PEFT or required dependencies not installed. Error: {e}")
                print("Falling back to basic OCR functionality...")
                print("To use the full Qari OCR model, please install:")
                print("  pip install torch torchvision torchaudio")
                print("  pip install qwen-vl-utils accelerate PEFT")
            self.model = None
            self.processor = None
            self.last_error = str(e)
        except Exception as e:
            if fallback_warn:
                print(f"Warning: Could not load Qari OCR PEFT adapter at {model_path}. Error: {e}")
                print("Falling back to basic OCR functionality...")
            self.model = None
            self.processor = None
            self.last_error = str(e)

    def extract(self, image, prompt=None):
        """
        Extract text from Quran page image.
        
        Args:
            image: PIL Image or numpy array
            prompt: Custom prompt (None = use strict verification prompt)
        """
        # Enhanced strict verification prompt - tells model NOT to correct errors
        if prompt is None:
            prompt = """Extract the Quranic text from this image. Extract each line only once. Do not repeat any text."""
        if self.model is None or self.processor is None:
            # Fallback to basic text extraction
            return self._fallback_extract(image)
        
        try:
            from qwen_vl_utils import process_vision_info
            import numpy as np
            
            # Save image temporarily
            temp_path = "temp_image.png"
            # Ensure image is PIL.Image and RGB format
            if not isinstance(image, Image.Image):
                # Convert numpy array to PIL
                if isinstance(image, np.ndarray):
                    # Convert to uint8 if needed
                    if image.dtype != np.uint8:
                        image = (image * 255).astype(np.uint8) if image.max() <= 1 else image.astype(np.uint8)
                    image = Image.fromarray(image)
                else:
                    image = Image.fromarray(np.array(image))
            
            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image.save(temp_path)
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"file://{os.path.abspath(temp_path)}"},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            
            # Process the input
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(self.device)
            
            # Generate text
            print("[QariOCR] Generating on CPU... (this may take ~30-90s)")
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=0.0
            )
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                "text": output_text, 
                "confidences": [0.9],
                "qari_text": output_text,
                "method": "qari_ocr_fine_tuned"
            }
            
        except Exception as e:
            print(f"Error in Qari OCR extraction: {e}")
            return self._fallback_extract(image)
    
    def _fallback_extract(self, image):
        """Fallback OCR method when the main model fails"""
        try:
            import pytesseract
            import numpy as np
            import re
            
            # Convert image to PIL if needed
            if not isinstance(image, Image.Image):
                if isinstance(image, np.ndarray):
                    if image.dtype != np.uint8:
                        image = (image * 255).astype(np.uint8) if image.max() <= 1 else image.astype(np.uint8)
                    image = Image.fromarray(image)
                else:
                    image = Image.fromarray(np.array(image))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Try multiple Tesseract configurations for better Arabic text extraction
            configs = [
                r'--oem 3 --psm 6 -l ara',  # Arabic, single text block
                r'--oem 3 --psm 4 -l ara',  # Arabic, single column
                r'--oem 3 --psm 3 -l ara',  # Arabic, fully automatic
                r'--oem 3 --psm 6 -l ara+eng',  # Arabic + English
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config in configs:
                try:
                    # Get text and confidence
                    data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                    text = pytesseract.image_to_string(image, config=config)
                    
                    # Calculate average confidence
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Clean up the text
                    text = text.strip()
                    
                    # Filter out mostly numbers and non-Arabic text
                    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
                    total_chars = len(text.replace(' ', '').replace('\n', ''))
                    arabic_ratio = arabic_chars / total_chars if total_chars > 0 else 0
                    
                    # Prefer text with more Arabic characters and higher confidence
                    if arabic_ratio > 0.3 and avg_confidence > best_confidence:
                        best_text = text
                        best_confidence = avg_confidence
                        
                except Exception as e:
                    continue
            
            # If no good Arabic text found, try a simpler approach
            if not best_text or best_confidence < 30:
                try:
                    # Simple Arabic extraction
                    simple_config = r'--oem 3 --psm 6 -l ara'
                    best_text = pytesseract.image_to_string(image, config=simple_config)
                    best_text = best_text.strip()
                except:
                    pass
            
            # Final cleanup
            if not best_text:
                best_text = "No Arabic text detected"
            else:
                # Remove excessive whitespace and clean up
                best_text = re.sub(r'\n+', '\n', best_text)
                best_text = re.sub(r' +', ' ', best_text)
                best_text = best_text.strip()
            
            return {
                "text": best_text,
                "confidences": [best_confidence / 100.0 if best_confidence > 0 else 0.5]
            }
            
        except ImportError:
            return {
                "text": "🔧 OCR Setup Required\n\nTo use the full Qari OCR functionality, please install the required dependencies:\n\n1. Install PyTorch (CPU version for Intel Mac):\n   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu\n\n2. Install additional dependencies:\n   pip install qwen-vl-utils accelerate PEFT\n\n3. Install Tesseract for fallback OCR:\n   brew install tesseract tesseract-lang\n\n4. Restart the application\n\nFor now, using fallback OCR mode.",
                "confidences": [0.1]
            }
        except Exception as e:
            return {
                "text": f"OCR extraction failed: {str(e)}",
                "confidences": [0.0]
            }