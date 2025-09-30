# Handles page matching algorithms (ORB + SIFT)

import os
import cv2
import numpy as np

class PageMatcher:
    """Match a page to a reference database using ORB and SIFT features."""
    
    def __init__(self, descriptors_dir="Data/assets/orb_sift"):
        """
        Initialize with the directory containing feature descriptors.
        
        Args:
            descriptors_dir (str): Path to the descriptors directory
        """
        self.descriptors_dir = descriptors_dir
        # ORB (fast, binary)
        self.orb = cv2.ORB_create()
        self.orb_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        # SIFT (accurate, float)
        self.sift = cv2.SIFT_create()
        self.sift_matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        
        # Load precomputed descriptors
        self.reference_descriptors = self._load_descriptors()
    
    def _load_descriptors(self):
        """
        Load precomputed feature descriptors from files.
        
        Returns:
            dict: Dictionary of descriptors by edition and page
        """
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
                    # ORB
                    orb_keypoints_data = data['orb_keypoints']
                    orb_descriptors_data = data['orb_descriptors']
                    orb_keypoints = [cv2.KeyPoint(x=kp[0], y=kp[1], _size=kp[2], _angle=kp[3],
                                                  _response=kp[4], _octave=int(kp[5]), _class_id=int(kp[6]))
                                     for kp in orb_keypoints_data]

                    # SIFT
                    sift_keypoints_data = data['sift_keypoints']
                    sift_descriptors_data = data['sift_descriptors']
                    sift_keypoints = [cv2.KeyPoint(x=kp[0], y=kp[1], _size=kp[2], _angle=kp[3],
                                                  _response=kp[4], _octave=int(kp[5]), _class_id=int(kp[6]))
                                     for kp in sift_keypoints_data] 
 
                    
                    # Store in the dictionary
                    if edition not in descriptors:
                        descriptors[edition] = {}
                    
                    descriptors[edition][page] = {
                        'orb_keypoints': orb_keypoints,
                        'orb_descriptors': orb_descriptors_data,
                        'sift_keypoints' : sift_keypoints,
                        'sift_descriptors' : sift_descriptors_data
                    }
                    
                except Exception as e:
                    print(f"Error loading descriptor file {filename}: {e}")
        
        return descriptors
    
    def extract_features(self, image):
        """
        Extract ORB and SIFT features from an image.     
        Returns:
            dict: {'orb': (keypoints, descriptors), 'sift': (keypoints, descriptors)}
        """
        orb_kp, orb_desc = self.orb.detectAndCompute(image, None)
        sift_kp, sift_desc = self.sift.detectAndCompute(image, None)
        return {'orb': (orb_kp, orb_desc), 'sift': (sift_kp, sift_desc)}
    
    def save_descriptors(self, edition, page, orb_keypoints, orb_descriptors, sift_keypoints, sift_descriptors):
        """
        Save ORB and SIFT descriptors to a file."""
                
        # Create directory if it doesn't exist
        os.makedirs(self.descriptors_dir, exist_ok=True)
        
        # Convert keypoints to a numpy array of their properties
        orb_keypoints_data = np.array([[kp.pt[0], kp.pt[1], kp.size, kp.angle, kp.response, kp.octave, kp.class_id] for kp in orb_keypoints])
        sift_keypoints_data = np.array([[kp.pt[0], kp.pt[1], kp.size, kp.angle, kp.response, kp.octave, kp.class_id] for kp in sift_keypoints])
        
        # Save to a .npz file
        filename = f"{edition}_{page}.npz"
        np.savez(
            os.path.join(self.descriptors_dir, filename),
            orb_keypoints=orb_keypoints_data,
            orb_descriptors=orb_descriptors,
            sift_keypoints=sift_keypoints_data,
            sift_descriptors=sift_descriptors
        )
        
        # Add to in-memory dictionary
        if edition not in self.reference_descriptors:
            self.reference_descriptors[edition] = {}
        
        self.reference_descriptors[edition][page] = {
            'orb_keypoints': orb_keypoints,
            'orb_descriptors': orb_descriptors,
            'sift_keypoints': sift_keypoints,
            'sift_descriptors': sift_descriptors
        }

    def match_page(self, query_image, threshold=0.7):
        """
        Match a query image to the reference database usiing ORB and SIFT.            
        Returns (edition, page, similarity, method) or None if no match is found.
        """
        # Extract features from query image
        feats = self.extract_features(query_image)
        orb_kp, orb_desc = feats['orb']
        sift_kp, sift_desc = feats['sift']
        best_match = None
        best_similarity = 0
        best_method = None
        
        # Match against all reference descriptors
        for edition in self.reference_descriptors:
            for page in self.reference_descriptors[edition]:
                ref = self.reference_descriptors[edition][page]
                
                # ORB matching
                if orb_desc is not None and ref['orb_descriptors'] is not None and len(orb_desc) >= 10 and len(ref['orb_descriptors']) >= 10:
                    matches = self.orb_matcher.match(orb_desc, ref['orb_descriptors'])
                    good_matches = [m for m in matches if m.distance < 50]
                    orb_similarity = len(good_matches) / max(len(orb_desc), len(ref['orb_descriptors']))
                    if orb_similarity > best_similarity and orb_similarity >= threshold:
                        best_match = (edition, page, orb_similarity, 'ORB')
                        best_similarity = orb_similarity
                        best_method = 'ORB'
                # SIFT matching
                if sift_desc is not None and ref['sift_descriptors'] is not None and len(sift_desc) >= 10 and len(ref['sift_descriptors']) >= 10:
                    matches = self.sift_matcher.match(sift_desc, ref['sift_descriptors'])
                    good_matches = [m for m in matches if m.distance < 250]
                    sift_similarity = len(good_matches) / max(len(sift_desc), len(ref['sift_descriptors']))
                    if sift_similarity > best_similarity and sift_similarity >= threshold:
                        best_match = (edition, page, sift_similarity, 'SIFT')
                        best_similarity = sift_similarity
                        best_method = 'SIFT'
        if best_match:
            return best_match
        return None