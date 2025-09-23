# Handles page matching algorithms

import os
import cv2
import numpy as np
import pickle

class PageMatcher:
    """Match a page to a reference database using ORB features."""
    
    def __init__(self, descriptors_dir="Data/assets/orb"):
        """Initialize with the directory containing ORB descriptors."""
        self.descriptors_dir = descriptors_dir
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.orb = cv2.ORB_create()
        
        # Load precomputed descriptors
        self.reference_descriptors = self._load_descriptors()
    
    def _load_descriptors(self):
        """Load precomputed ORB descriptors from files."""
        descriptors = {}
        
        # Create directory if it doesn't exist
        os.makedirs(self.descriptors_dir, exist_ok=True)
        
        # Look for .npz files
        for filename in os.listdir(self.descriptors_dir):
            if filename.endswith('.npz'):
                try:
                    # Parse filename to get edition and page
                    parts = filename[:-4].split('_')
                    edition = parts[0]
                    page = int(parts[1])
                    
                    # Load descriptors
                    data = np.load(os.path.join(self.descriptors_dir, filename), allow_pickle=True)
                    keypoints_data = data['keypoints']
                    descriptors_data = data['descriptors']
                    
                    # Reconstruct keypoints
                    keypoints = []
                    for kp_data in keypoints_data:
                        kp = cv2.KeyPoint(
                            x=kp_data[0], y=kp_data[1],
                            _size=kp_data[2], _angle=kp_data[3],
                            _response=kp_data[4], _octave=int(kp_data[5]),
                            _class_id=int(kp_data[6])
                        )
                        keypoints.append(kp)
                    
                    # Store in the dictionary
                    if edition not in descriptors:
                        descriptors[edition] = {}
                    
                    descriptors[edition][page] = {
                        'keypoints': keypoints,
                        'descriptors': descriptors_data
                    }
                    
                except Exception as e:
                    print(f"Error loading descriptor file {filename}: {e}")
        
        return descriptors
    
    def extract_features(self, image):
        """Extract ORB features from an image."""
        keypoints, descriptors = self.orb.detectAndCompute(image, None)
        return keypoints, descriptors
    
    def save_descriptors(self, edition, page, keypoints, descriptors):
        """Save ORB descriptors to a file."""
        # Create directory if it doesn't exist
        os.makedirs(self.descriptors_dir, exist_ok=True)
        
        # Convert keypoints to a numpy array of their properties
        keypoints_data = np.array([
            [kp.pt[0], kp.pt[1], kp.size, kp.angle, kp.response, kp.octave, kp.class_id]
            for kp in keypoints
        ])
        
        # Save to a .npz file
        filename = f"{edition}_{page}.npz"
        np.savez(
            os.path.join(self.descriptors_dir, filename),
            keypoints=keypoints_data,
            descriptors=descriptors
        )
        
        # Add to in-memory dictionary
        if edition not in self.reference_descriptors:
            self.reference_descriptors[edition] = {}
        
        self.reference_descriptors[edition][page] = {
            'keypoints': keypoints,
            'descriptors': descriptors
        }
    
    def match_page(self, query_image, threshold=0.7):
        """
        Match a query image to the reference database.
        Returns (edition, page, similarity) or None if no match is found.
        """
        # Extract features from query image
        query_keypoints, query_descriptors = self.extract_features(query_image)
        
        if query_descriptors is None or len(query_descriptors) < 10:
            # Not enough features detected
            return None
        
        best_match = None
        best_similarity = 0
        
        # Match against all reference descriptors
        for edition in self.reference_descriptors:
            for page in self.reference_descriptors[edition]:
                ref_descriptors = self.reference_descriptors[edition][page]['descriptors']
                
                # Skip if reference descriptors are empty
                if ref_descriptors is None or len(ref_descriptors) < 10:
                    continue
                
                # Match descriptors
                matches = self.matcher.match(query_descriptors, ref_descriptors)
                
                # Calculate similarity score (number of good matches / total features)
                # Only consider good matches (low distance)
                good_matches = [m for m in matches if m.distance < 50]
                similarity = len(good_matches) / max(len(query_descriptors), len(ref_descriptors))
                
                # Update best match if this is better
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (edition, page, similarity)
        
        # Return the best match if it meets the threshold
        if best_match and best_match[2] >= threshold:
            return best_match
        
        return None