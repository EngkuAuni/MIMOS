# One-time run utility script
# Generate ORB and SIFT descriptors for reference Quran images.
# Run: python app/generate_descriptors.py --input Data/reference_imgs --edition Uthmani

import os
import argparse
import cv2
from pathlib import Path
from tqdm import tqdm

import sys
sys.path.append('.')
from modules.matching import PageMatcher

def extract_page_number(filename):
    stem = Path(filename).stem
    digits_only = ''.join(c for c in stem if c.isdigit())
    if digits_only:
        return int(digits_only)
    print(f"Warning: Could not extract page number from {filename}")
    return None

def generate_descriptors(input_dir, edition="Uthmani", output_dir="Data/assets/orb_sift"):
    matcher = PageMatcher(descriptors_dir=output_dir)
    os.makedirs(output_dir, exist_ok=True)
    image_files = list(Path(input_dir).glob("*.jpg")) + \
                  list(Path(input_dir).glob("*.jpeg")) + \
                  list(Path(input_dir).glob("*.png"))
    if not image_files:
        print(f"Error: No image files found in {input_dir}")
        return False
    print(f"Found {len(image_files)} image files. Processing...")
    successful = 0
    for img_path in tqdm(image_files):
        try:
            page_num = extract_page_number(img_path)
            if not page_num:
                continue
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"Error: Could not read image {img_path}")
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            feats = matcher.extract_features(gray)
            orb_kp, orb_desc = feats['orb']
            sift_kp, sift_desc = feats['sift']
            if orb_kp is None or orb_desc is None or len(orb_kp) < 10:
                print(f"Warning: Not enough ORB features in {img_path}")
                continue
            if sift_kp is None or sift_desc is None or len(sift_kp) < 10:
                print(f"Warning: Not enough SIFT features in {img_path}")
                continue
            matcher.save_descriptors(edition, page_num, orb_kp, orb_desc, sift_kp, sift_desc)
            successful += 1
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    print(f"Successfully processed {successful}/{len(image_files)} images")
    print(f"Descriptors saved to {output_dir}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ORB and SIFT descriptors for reference Quran pages")
    parser.add_argument("--input", required=True, help="Directory containing reference page images")
    parser.add_argument("--edition", default="Uthmani", help="Edition name (e.g., 'Uthmani', 'tajweed', etc.)")
    parser.add_argument("--output", default="Data/assets/orb_sift", help="Output directory for descriptors")
    args = parser.parse_args()
    if not os.path.isdir(args.input):
        print(f"Error: Input directory {args.input} does not exist")
        sys.exit(1)
    success = generate_descriptors(args.input, args.edition, args.output)
    if success:
        print("✅ Done! You can now use ORB+SIFT based page matching in the Quran Verification Engine.")
    else:
        print("❌ Failed to generate descriptors.")