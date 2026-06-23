class DexterityClassifier:
    def __init__(self, model_path='dexterity_model.pkl'):
        # Using a rule-based expert system instead of scikit-learn 
        # to ensure compatibility with Python 3.15 without C++ Build Tools
        self.classes = ['Natural Left-handed', 'Natural Right-handed', 'Ambidextrous', 'Learned Non-Use']

    def predict(self, features):
        """
        features: dict containing metrics from cv_tracker
        """
        l_score = features.get('left_score', 0)
        r_score = features.get('right_score', 0)
        
        l_center = features.get('left_center_ratio', 0)
        r_center = features.get('right_center_ratio', 0)
        
        # Check for Learned Non-Use (Extreme asymmetry)
        # If one hand is very low score and rarely goes to center, while other is high
        if (l_score < 30 and r_score > 50 and l_center < 0.1) or \
           (r_score < 30 and l_score > 50 and r_center < 0.1):
            return self.classes[3] # Learned Non-Use
            
        # Check Ambidextrous
        if abs(l_score - r_score) < 15 and l_center > 0.2 and r_center > 0.2:
            return self.classes[2] # Ambidextrous
            
        # Left vs Right
        if l_score > r_score and l_center > r_center:
            return self.classes[0] # Natural Left-handed
        else:
            return self.classes[1] # Natural Right-handed
