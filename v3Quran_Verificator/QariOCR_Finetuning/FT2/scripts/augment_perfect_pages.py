"""
Data Augmentation Script for Perfect Quran Pages
=================================================

This script generates augmented versions of the 604 reference images to:
1. Prevent model memorization of specific images
2. Improve generalization to different image conditions
3. Force the model to learn features rather than memorize patterns

Augmentation techniques:
- Rotation (±2-5 degrees)
- Brightness/contrast variations
- Slight blur/noise
- Cropping/scaling
- Color temperature adjustments

Output: 1,200-1,500 augmented perfect samples (2-2.5x original)
"""

import os
import json
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from pathlib import Path
from typing import Dict, List, Tuple
import random
from tqdm import tqdm

class PerfectPageAugmentor:
    """Augment perfect Quran pages for better model generalization"""
    
    def __init__(self, 
                 reference_imgs_dir: str = "../../database/reference_imgs",
                 output_dir: str = "../training_data/augmented_perfect",
                 ground_truth_db: str = "../../database/quran_verses.db"):
        """
        Initialize the augmentor
        
        Args:
            reference_imgs_dir: Path to reference images (604 pages)
            output_dir: Output directory for augmented images
            ground_truth_db: Path to database with ground truth text
        """
        self.reference_imgs_dir = Path(reference_imgs_dir)
        self.output_dir = Path(output_dir)
        self.ground_truth_db = ground_truth_db
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Augmentation parameters
        self.augmentations_per_image = 2  # Generate 2-2.5x original
        
        # Load ground truth
        self.ground_truth = self._load_ground_truth()
        
    def _load_ground_truth(self) -> Dict:
        """Load ground truth text from database"""
        import sqlite3
        
        ground_truth = {}
        
        try:
            conn = sqlite3.connect(self.ground_truth_db)
            cursor = conn.cursor()
            
            # Get all verses
            cursor.execute("SELECT sura_number, aya_number, text_original FROM verses ORDER BY sura_number, aya_number")
            verses = cursor.fetchall()
            
            # Group by page (simplified - you may need page_mapper.py for accurate mapping)
            # For now, we'll store all verses and let the training script handle page mapping
            for sura, aya, text in verses:
                key = f"{sura}_{aya}"
                ground_truth[key] = text
            
            conn.close()
            print(f"✅ Loaded {len(ground_truth)} verses as ground truth")
            
        except Exception as e:
            print(f"⚠️ Could not load ground truth from database: {e}")
            print("   Will use image filenames only")
        
        return ground_truth
    
    def augment_rotation(self, image: np.ndarray, angle_range: Tuple[float, float] = (-5, 5)) -> np.ndarray:
        """Rotate image by small angle"""
        angle = random.uniform(*angle_range)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate with white background
        rotated = cv2.warpAffine(image, M, (w, h), 
                                 borderMode=cv2.BORDER_CONSTANT, 
                                 borderValue=(255, 255, 255))
        return rotated
    
    def augment_brightness_contrast(self, image: np.ndarray) -> np.ndarray:
        """Adjust brightness and contrast"""
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Random brightness (0.8 to 1.2)
        brightness_factor = random.uniform(0.85, 1.15)
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(brightness_factor)
        
        # Random contrast (0.8 to 1.2)
        contrast_factor = random.uniform(0.85, 1.15)
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(contrast_factor)
        
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def augment_blur_noise(self, image: np.ndarray) -> np.ndarray:
        """Add slight blur or noise"""
        choice = random.choice(['blur', 'noise', 'none'])
        
        if choice == 'blur':
            # Slight Gaussian blur
            kernel_size = random.choice([3, 5])
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        
        elif choice == 'noise':
            # Add slight Gaussian noise
            noise = np.random.normal(0, 3, image.shape).astype(np.uint8)
            return cv2.add(image, noise)
        
        return image
    
    def augment_scale_crop(self, image: np.ndarray, scale_range: Tuple[float, float] = (0.95, 1.05)) -> np.ndarray:
        """Scale and crop image"""
        h, w = image.shape[:2]
        scale = random.uniform(*scale_range)
        
        # Resize
        new_w, new_h = int(w * scale), int(h * scale)
        scaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Crop or pad to original size
        if scale > 1.0:
            # Crop center
            start_x = (new_w - w) // 2
            start_y = (new_h - h) // 2
            return scaled[start_y:start_y+h, start_x:start_x+w]
        else:
            # Pad with white
            pad_x = (w - new_w) // 2
            pad_y = (h - new_h) // 2
            padded = np.full((h, w, 3), 255, dtype=np.uint8)
            padded[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = scaled
            return padded
    
    def augment_color_temperature(self, image: np.ndarray) -> np.ndarray:
        """Adjust color temperature (warmer/cooler)"""
        # Random temperature shift
        temp_shift = random.uniform(-10, 10)
        
        # Convert to float
        img_float = image.astype(np.float32)
        
        # Adjust blue and red channels
        img_float[:, :, 0] = np.clip(img_float[:, :, 0] - temp_shift, 0, 255)  # Blue
        img_float[:, :, 2] = np.clip(img_float[:, :, 2] + temp_shift, 0, 255)  # Red
        
        return img_float.astype(np.uint8)
    
    def apply_augmentation_pipeline(self, image: np.ndarray, augmentation_level: str = 'medium') -> np.ndarray:
        """Apply a pipeline of augmentations"""
        
        if augmentation_level == 'light':
            # Light augmentation - 1-2 techniques
            techniques = random.sample([
                self.augment_brightness_contrast,
                self.augment_rotation,
            ], k=random.randint(1, 2))
        
        elif augmentation_level == 'medium':
            # Medium augmentation - 2-3 techniques
            techniques = random.sample([
                self.augment_brightness_contrast,
                self.augment_rotation,
                self.augment_blur_noise,
                self.augment_scale_crop,
            ], k=random.randint(2, 3))
        
        else:  # heavy
            # Heavy augmentation - 3-4 techniques
            techniques = random.sample([
                self.augment_brightness_contrast,
                self.augment_rotation,
                self.augment_blur_noise,
                self.augment_scale_crop,
                self.augment_color_temperature,
            ], k=random.randint(3, 4))
        
        # Apply techniques sequentially
        augmented = image.copy()
        for technique in techniques:
            augmented = technique(augmented)
        
        return augmented
    
    def augment_single_image(self, image_path: Path, page_number: int) -> List[Dict]:
        """Augment a single image and return metadata"""
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"⚠️ Could not load image: {image_path}")
            return []
        
        augmented_samples = []
        
        # Generate augmented versions
        for i in range(self.augmentations_per_image):
            # Determine augmentation level
            if i == 0:
                level = 'light'
            elif i == 1:
                level = 'medium'
            else:
                level = 'heavy'
            
            # Apply augmentation
            augmented = self.apply_augmentation_pipeline(image, level)
            
            # Save augmented image
            output_filename = f"page_{page_number:03d}_aug_{i+1}.jpg"
            output_path = self.output_dir / output_filename
            cv2.imwrite(str(output_path), augmented, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # Create metadata
            sample = {
                "id": f"perfect_aug_{page_number:03d}_{i+1}",
                "image_path": str(output_path.relative_to(self.output_dir.parent)),
                "original_page": page_number,
                "augmentation_level": level,
                "is_augmented": True,
                "has_error": False,
                "task": "text_extraction"
            }
            
            augmented_samples.append(sample)
        
        return augmented_samples
    
    def generate_augmented_dataset(self) -> Dict:
        """Generate complete augmented dataset"""
        
        print("🔄 Starting data augmentation for perfect pages...")
        print(f"   Reference images: {self.reference_imgs_dir}")
        print(f"   Output directory: {self.output_dir}")
        print(f"   Augmentations per image: {self.augmentations_per_image}")
        
        # Find all reference images
        image_files = sorted(self.reference_imgs_dir.glob("*.jpg"))
        print(f"   Found {len(image_files)} reference images")
        
        if len(image_files) == 0:
            print("❌ No reference images found!")
            return {}
        
        all_samples = []
        
        # Process each image
        for image_path in tqdm(image_files, desc="Augmenting images"):
            # Extract page number from filename (e.g., "001.jpg" -> 1)
            page_number = int(image_path.stem)
            
            # Augment image
            samples = self.augment_single_image(image_path, page_number)
            all_samples.extend(samples)
        
        # Generate metadata
        metadata = {
            "dataset_name": "Augmented Perfect Quran Pages",
            "version": "1.0",
            "total_samples": len(all_samples),
            "original_images": len(image_files),
            "augmentations_per_image": self.augmentations_per_image,
            "augmentation_techniques": [
                "rotation", "brightness/contrast", "blur/noise", 
                "scale/crop", "color_temperature"
            ],
            "purpose": "Prevent memorization and improve generalization",
            "samples": all_samples
        }
        
        # Save metadata
        metadata_path = self.output_dir / "metadata_augmented.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Augmentation complete!")
        print(f"   Total augmented samples: {len(all_samples)}")
        print(f"   Metadata saved to: {metadata_path}")
        
        return metadata

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Augment perfect Quran pages for FT2")
    parser.add_argument("--reference-dir", type=str, 
                       default="../../database/reference_imgs",
                       help="Directory containing reference images")
    parser.add_argument("--output-dir", type=str,
                       default="../training_data/augmented_perfect",
                       help="Output directory for augmented images")
    parser.add_argument("--augmentations", type=int, default=2,
                       help="Number of augmentations per image (default: 2)")
    parser.add_argument("--db-path", type=str,
                       default="../../database/quran_verses.db",
                       help="Path to ground truth database")
    
    args = parser.parse_args()
    
    # Create augmentor
    augmentor = PerfectPageAugmentor(
        reference_imgs_dir=args.reference_dir,
        output_dir=args.output_dir,
        ground_truth_db=args.db_path
    )
    
    # Set augmentations per image
    augmentor.augmentations_per_image = args.augmentations
    
    # Generate augmented dataset
    metadata = augmentor.generate_augmented_dataset()
    
    print("\n" + "="*50)
    print("📊 Augmentation Summary:")
    print(f"   Original images: {metadata.get('original_images', 0)}")
    print(f"   Augmented samples: {metadata.get('total_samples', 0)}")
    print(f"   Multiplication factor: {metadata.get('total_samples', 0) / metadata.get('original_images', 1):.1f}x")
    print("="*50)

if __name__ == "__main__":
    main()

