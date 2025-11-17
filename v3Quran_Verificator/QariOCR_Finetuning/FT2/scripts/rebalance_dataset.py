"""
Dataset Rebalancing Script for FT2
===================================

This script combines FT1 data, augmented perfect pages, and new synthetic errors
into balanced FT2 datasets with 40% correct / 60% errors split.

It creates two variant datasets:
1. FT2_Extraction - For raw text extraction without auto-correction
2. FT2_Verification - For error detection and reporting

Key Changes from FT1:
- Updated prompts to prevent auto-correction
- 40/60 split (was 53/47)
- More diverse error samples
- Specialized prompts per task
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

# New prompts for FT2
EXTRACTION_PROMPT = """Extract the Quranic text from this image EXACTLY as printed.
DO NOT auto-correct any errors.
DO NOT fill in missing characters.
DO NOT match to memorized text.
Report exactly what you see, character by character.
If a character is unclear or missing, use underscore (_).
Preserve all spacing and line breaks as shown."""

VERIFICATION_PROMPT = """Verify this Quranic text against the Uthmani standard. 
Read EXACTLY what is printed in the image.
DO NOT auto-correct errors - report them.
Detect any errors in:
- Missing or wrong diacritics (fatha, kasra, damma, sukun, shadda)
- Missing or extra letters
- Wrong letter forms (dots, hamza)
- Non-Uthmani script usage

If errors found, list each error with:
- Type
- Location
- Description  
- Severity (CRITICAL/MAJOR/MINOR)

If no errors, respond: "VERIFIED: No errors detected"

Extract the text first, then analyze for errors."""

PERFECT_EXTRACTION_PROMPT = """Extract the Quranic text from this image with 100% accuracy.
Read character by character, including all diacritics.
Preserve exact spacing and line breaks.
Include all harakat: fatha (َ), kasra (ِ), damma (ُ), sukun (ْ), shadda (ّ), tanween.
Do not skip any characters or diacritics.
Report exactly what is printed."""

class FT2DatasetRebalancer:
    """Rebalance and combine datasets for FT2"""
    
    def __init__(self,
                 ft1_data_dir: str = "../training_data/enhanced",
                 augmented_perfect_dir: str = "../training_data/augmented_perfect",
                 synthetic_errors_dir: str = "../training_data/synthetic_errors_v2_full",
                 output_dir: str = "../training_data/ft2"):
        """
        Initialize the rebalancer
        
        Args:
            ft1_data_dir: Directory containing FT1 training data
            augmented_perfect_dir: Directory with augmented perfect pages
            synthetic_errors_dir: Directory with new synthetic errors
            output_dir: Output directory for FT2 datasets
        """
        self.ft1_dir = Path(ft1_data_dir)
        self.augmented_dir = Path(augmented_perfect_dir)
        self.errors_dir = Path(synthetic_errors_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "ft2_extraction").mkdir(exist_ok=True)
        (self.output_dir / "ft2_verification").mkdir(exist_ok=True)
    
    def load_ft1_data(self) -> Tuple[List, List]:
        """Load FT1 training data"""
        print("📂 Loading FT1 data...")
        
        ft1_train_path = self.ft1_dir / "train_enhanced.json"
        ft1_val_path = self.ft1_dir / "val_enhanced.json"
        
        train_data = []
        val_data = []
        
        if ft1_train_path.exists():
            with open(ft1_train_path, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            print(f"   Loaded {len(train_data)} FT1 training samples")
        
        if ft1_val_path.exists():
            with open(ft1_val_path, 'r', encoding='utf-8') as f:
                val_data = json.load(f)
            print(f"   Loaded {len(val_data)} FT1 validation samples")
        
        return train_data, val_data
    
    def load_augmented_perfect(self) -> List:
        """Load augmented perfect pages"""
        print("📂 Loading augmented perfect pages...")
        
        metadata_path = self.augmented_dir / "metadata_augmented.json"
        
        if not metadata_path.exists():
            print("   ⚠️ Augmented perfect pages not found, skipping")
            return []
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        samples = metadata.get('samples', [])
        print(f"   Loaded {len(samples)} augmented samples")
        
        return samples
    
    def load_synthetic_errors(self) -> List:
        """Load new synthetic errors"""
        print("📂 Loading synthetic errors v2...")
        
        metadata_path = self.errors_dir / "metadata_errors_v2.json"
        
        if not metadata_path.exists():
            print("   ⚠️ Synthetic errors v2 not found, using empty list")
            return []
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        samples = metadata.get('samples', [])
        print(f"   Loaded {len(samples)} synthetic error samples")
        
        return samples
    
    def apply_prompts(self, sample: Dict, model_type: str) -> Dict:
        """Apply appropriate prompt to sample"""
        
        # Check if sample has error
        has_error = sample.get('has_error', False) or sample.get('is_synthetic', False)
        
        # Determine prompt based on model type and error status
        if model_type == 'extraction':
            if has_error:
                prompt = EXTRACTION_PROMPT
            else:
                prompt = PERFECT_EXTRACTION_PROMPT
        else:  # verification
            if has_error:
                prompt = VERIFICATION_PROMPT
            else:
                # For perfect pages in verification mode, still extract then verify
                prompt = PERFECT_EXTRACTION_PROMPT
        
        # Update messages with new prompt
        if 'messages' in sample:
            updated_messages = sample['messages'].copy()
            
            # Find the text prompt in messages
            for i, msg in enumerate(updated_messages):
                if msg.get('role') == 'user' and 'content' in msg:
                    if isinstance(msg['content'], list):
                        # Update text content
                        for j, content_item in enumerate(msg['content']):
                            if content_item.get('type') == 'text':
                                updated_messages[i]['content'][j]['text'] = prompt
                                break
            
            sample['messages'] = updated_messages
        
        return sample
    
    def rebalance_dataset(self, perfect_samples: List, error_samples: List, 
                         target_ratio: float = 0.4) -> Tuple[List, List]:
        """
        Rebalance dataset to target ratio
        
        Args:
            perfect_samples: List of perfect/error-free samples
            error_samples: List of error samples
            target_ratio: Target ratio of perfect samples (default: 0.4 = 40%)
        
        Returns:
            (balanced_perfect, balanced_errors) - Both resized to achieve target ratio
        """
        print(f"\n🔄 Rebalancing dataset to {target_ratio*100}% perfect / {(1-target_ratio)*100}% errors...")
        
        # Calculate target counts
        total_perfect = len(perfect_samples)
        total_errors = len(error_samples)
        
        if len(error_samples) == 0:
            print("   ⚠️ No error samples, returning all perfect samples")
            return perfect_samples, []
        
        # Target: 40% perfect, 60% errors
        # Given error samples, how many perfect samples do we need?
        target_perfect = int(total_errors * target_ratio / (1 - target_ratio))
        
        print(f"   Perfect samples: {total_perfect}")
        print(f"   Error samples: {total_errors}")
        print(f"   Target perfect (for balance): {target_perfect}")
        
        # If we have more perfect than needed, sample randomly
        if len(perfect_samples) > target_perfect:
            balanced_perfect = random.sample(perfect_samples, target_perfect)
        else:
            balanced_perfect = perfect_samples
        
        # Use all error samples
        balanced_errors = error_samples
        
        print(f"   Balanced perfect samples: {len(balanced_perfect)}")
        print(f"   Balanced error samples: {len(balanced_errors)}")
        print(f"   Actual ratio: {len(balanced_perfect)/(len(balanced_perfect)+len(balanced_errors)):.1%} / {len(balanced_errors)/(len(balanced_perfect)+len(balanced_errors)):.1%}")
        
        return balanced_perfect, balanced_errors
    
    def split_train_val(self, samples: List, split_ratio: float = 0.85) -> Tuple[List, List]:
        """
        Split samples into train and validation sets
        
        Args:
            samples: List of samples
            split_ratio: Ratio for training (default: 0.85 = 85% train, 15% val)
        
        Returns:
            (train_samples, val_samples)
        """
        # Shuffle
        random.shuffle(samples)
        
        # Split
        split_idx = int(len(samples) * split_ratio)
        train = samples[:split_idx]
        val = samples[split_idx:]
        
        return train, val
    
    def create_ft2_dataset(self, model_type: str = 'extraction'):
        """
        Create FT2 dataset for specific model type
        
        Args:
            model_type: 'extraction' or 'verification'
        """
        print(f"\n{'='*60}")
        print(f"Creating FT2_{model_type} dataset...")
        print(f"{'='*60}")
        
        # Load all data sources
        ft1_train, ft1_val = self.load_ft1_data()
        augmented_perfect = self.load_augmented_perfect()
        synthetic_errors = self.load_synthetic_errors()
        
        # Combine perfect samples
        perfect_samples = ft1_train + ft1_val + augmented_perfect
        print(f"\n   Total perfect samples: {len(perfect_samples)}")
        
        # Combine error samples
        error_samples = synthetic_errors
        # Filter FT1 data for errors
        for sample in ft1_train + ft1_val:
            if sample.get('has_error') or sample.get('is_synthetic'):
                error_samples.append(sample)
        
        print(f"   Total error samples: {len(error_samples)}")
        
        # Rebalance (40% perfect, 60% errors)
        balanced_perfect, balanced_errors = self.rebalance_dataset(
            perfect_samples, error_samples, target_ratio=0.4
        )
        
        # Combine and apply prompts
        all_samples = []
        
        print(f"\n🔄 Applying {model_type} prompts to samples...")
        for sample in balanced_perfect + balanced_errors:
            updated_sample = self.apply_prompts(sample, model_type)
            all_samples.append(updated_sample)
        
        # Split into train/val
        print(f"\n🔄 Splitting into train/val (85/15)...")
        train_samples, val_samples = self.split_train_val(all_samples, split_ratio=0.85)
        
        # Save datasets
        output_path = self.output_dir / f"ft2_{model_type}"
        
        train_path = output_path / "train.json"
        val_path = output_path / "val.json"
        metadata_path = output_path / "metadata.json"
        
        print(f"\n💾 Saving datasets...")
        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump(train_samples, f, indent=2, ensure_ascii=False)
        print(f"   Training samples: {len(train_samples)} → {train_path}")
        
        with open(val_path, 'w', encoding='utf-8') as f:
            json.dump(val_samples, f, indent=2, ensure_ascii=False)
        print(f"   Validation samples: {len(val_samples)} → {val_path}")
        
        # Create metadata
        metadata = {
            "dataset_name": f"FT2 {model_type.title()} Dataset",
            "version": "2.0",
            "model_type": model_type,
            "total_samples": len(all_samples),
            "train_samples": len(train_samples),
            "val_samples": len(val_samples),
            "split_ratio": 0.85,
            "perfect_ratio": len(balanced_perfect) / len(all_samples) if all_samples else 0,
            "error_ratio": len(balanced_errors) / len(all_samples) if all_samples else 0,
            "prompt_strategy": EXTRACTION_PROMPT if model_type == 'extraction' else VERIFICATION_PROMPT,
            "data_sources": {
                "ft1_data": len(ft1_train + ft1_val),
                "augmented_perfect": len(augmented_perfect),
                "synthetic_errors": len(synthetic_errors)
            }
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"   Metadata saved → {metadata_path}")
        
        print(f"\n✅ FT2_{model_type} dataset created successfully!")
        return metadata
    
    def create_both_datasets(self):
        """Create both extraction and verification datasets"""
        
        # Create extraction dataset
        ext_metadata = self.create_ft2_dataset('extraction')
        
        # Create verification dataset
        ver_metadata = self.create_ft2_dataset('verification')
        
        print(f"\n{'='*60}")
        print("📊 Final Summary:")
        print(f"{'='*60}")
        print(f"\nExtraction Dataset:")
        print(f"   Total samples: {ext_metadata['total_samples']}")
        print(f"   Train: {ext_metadata['train_samples']}, Val: {ext_metadata['val_samples']}")
        print(f"   Perfect: {ext_metadata['perfect_ratio']:.1%}, Errors: {ext_metadata['error_ratio']:.1%}")
        
        print(f"\nVerification Dataset:")
        print(f"   Total samples: {ver_metadata['total_samples']}")
        print(f"   Train: {ver_metadata['train_samples']}, Val: {ver_metadata['val_samples']}")
        print(f"   Perfect: {ver_metadata['perfect_ratio']:.1%}, Errors: {ver_metadata['error_ratio']:.1%}")
        
        print(f"\n{'='*60}")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebalance datasets for FT2")
    parser.add_argument("--ft1-dir", type=str, default="../training_data/enhanced",
                       help="FT1 data directory")
    parser.add_argument("--augmented-dir", type=str, 
                       default="../training_data/augmented_perfect",
                       help="Augmented perfect pages directory")
    parser.add_argument("--errors-dir", type=str,
                       default="../training_data/synthetic_errors_v2_full",
                       help="Synthetic errors directory")
    parser.add_argument("--output-dir", type=str, default="../training_data/ft2",
                       help="Output directory")
    parser.add_argument("--model-type", type=str, choices=['extraction', 'verification', 'both'],
                       default='both', help="Which dataset to create")
    
    args = parser.parse_args()
    
    # Create rebalancer
    rebalancer = FT2DatasetRebalancer(
        ft1_data_dir=args.ft1_dir,
        augmented_perfect_dir=args.augmented_dir,
        synthetic_errors_dir=args.errors_dir,
        output_dir=args.output_dir
    )
    
    # Create datasets
    if args.model_type == 'both':
        rebalancer.create_both_datasets()
    else:
        rebalancer.create_ft2_dataset(args.model_type)

if __name__ == "__main__":
    main()

