import os
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import random

class HandDexterityTracker:
    def __init__(self):
        self.model_path = 'hand_landmarker.task'
        if not os.path.exists(self.model_path):
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            urllib.request.urlretrieve(url, self.model_path)
        
    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or math.isnan(fps):
            fps = 30.0
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Center grid boundaries
        cw_start, cw_end = width // 3, 2 * width // 3
        ch_start, ch_end = height // 3, 2 * height // 3
        
        # Stats
        stats = {
            'Left': {'path': [], 'center_frames': 0, 'total_frames': 0, 'hits': 0},
            'Right': {'path': [], 'center_frames': 0, 'total_frames': 0, 'hits': 0}
        }
        
        full_path_left = []
        full_path_right = []
        
        hitmap_size = 20
        hitmap_left = [[0]*hitmap_size for _ in range(hitmap_size)]
        hitmap_right = [[0]*hitmap_size for _ in range(hitmap_size)]
        
        target_radius = min(width, height) // 10
        current_target = self._generate_target(width, height, target_radius)
        
        combos = {'Left': 0, 'Right': 0}
        current_combo = {'Left': 0, 'Right': 0}
        
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=self.model_path),
            num_hands=2,
            running_mode=vision.RunningMode.VIDEO
        )
        detector = vision.HandLandmarker.create_from_options(options)
        
        frame_idx = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            if timestamp_ms <= 0:
                timestamp_ms = int((frame_idx / fps) * 1000)
                
            timestamp_ms = max(timestamp_ms, frame_idx * 33)
                
            results = detector.detect_for_video(mp_image, timestamp_ms)
            
            lx, ly = None, None
            rx, ry = None, None
            
            if results.hand_landmarks:
                for idx, hand_landmarks in enumerate(results.hand_landmarks):
                    label = results.handedness[idx][0].category_name
                    
                    idx_finger = hand_landmarks[8]
                    x, y = int(idx_finger.x * width), int(idx_finger.y * height)
                    
                    if label == 'Left':
                        lx, ly = x, y
                    elif label == 'Right':
                        rx, ry = x, y
                        
                    if label in stats:
                        stats[label]['path'].append((x, y))
                        stats[label]['total_frames'] += 1
                        
                        if cw_start <= x <= cw_end and ch_start <= y <= ch_end:
                            stats[label]['center_frames'] += 1
                            
                        hx = min(int((idx_finger.x) * hitmap_size), hitmap_size - 1)
                        hy = min(int((idx_finger.y) * hitmap_size), hitmap_size - 1)
                        if label == 'Left':
                            hitmap_left[hy][hx] += 1
                        else:
                            hitmap_right[hy][hx] += 1
                            
                        tx, ty = current_target
                        dist = math.hypot(x - tx, y - ty)
                        if dist <= target_radius:
                            stats[label]['hits'] += 1
                            current_combo[label] += 1
                            combos[label] = max(combos[label], current_combo[label])
                            current_target = self._generate_target(width, height, target_radius)
                            
            full_path_left.append([lx, ly] if lx is not None else None)
            full_path_right.append([rx, ry] if rx is not None else None)
                            
            frame_idx += 1
                        
        cap.release()
        
        metrics = self._calculate_metrics(stats, width, height, hitmap_left, hitmap_right, combos, fps)
        metrics['full_path_left'] = full_path_left
        metrics['full_path_right'] = full_path_right
        metrics['video_width'] = width
        metrics['video_height'] = height
        metrics['fps'] = fps
        return metrics
        
    def _generate_target(self, w, h, padding):
        return (random.randint(padding, w - padding), random.randint(padding, h - padding))
        
    def _calculate_metrics(self, stats, w, h, hl, hr, combos, fps):
        metrics = {}
        max_diagonal = math.hypot(w, h)
        
        for hand in ['Left', 'Right']:
            path = stats[hand]['path']
            total_frames = stats[hand]['total_frames']
            center_frames = stats[hand]['center_frames']
            
            if total_frames < 10:
                metrics[f'{hand.lower()}_speed'] = 20.0
                metrics[f'{hand.lower()}_accuracy'] = 20.0
                metrics[f'{hand.lower()}_quality'] = 20.0
                metrics[f'{hand.lower()}_center_ratio'] = 0.0
                metrics[f'{hand.lower()}_score'] = 0
                metrics[f'{hand.lower()}_combo'] = 0
                continue
                
            displacements = [math.hypot(path[i][0] - path[i-1][0], path[i][1] - path[i-1][1]) for i in range(1, len(path))]
            avg_disp = sum(displacements) / len(displacements) if displacements else 0
            
            speed_ratio = min(avg_disp / (0.05 * max_diagonal), 1.0)
            speed_metric = 20 + (80 * speed_ratio)
            
            total_path_length = sum(displacements)
            net_displacement = math.hypot(path[-1][0] - path[0][0], path[-1][1] - path[0][1])
            raw_accuracy = net_displacement / total_path_length if total_path_length > 0 else 0
            acc_metric = min(30 + (raw_accuracy * 300), 100.0) 
            
            mean_disp = avg_disp
            var_disp = sum((x - mean_disp) ** 2 for x in displacements) / len(displacements) if displacements else 0
            max_expected_var = (0.05 * max_diagonal)**2
            q_ratio = max(1.0 - (var_disp / max_expected_var), 0.0)
            quality_metric = 30 + (70 * q_ratio)
            
            center_ratio = center_frames / total_frames
            
            metrics[f'{hand.lower()}_speed'] = min(max(speed_metric, 20), 100)
            metrics[f'{hand.lower()}_accuracy'] = min(max(acc_metric, 20), 100)
            metrics[f'{hand.lower()}_quality'] = min(max(quality_metric, 20), 100)
            metrics[f'{hand.lower()}_center_ratio'] = center_ratio
            metrics[f'{hand.lower()}_combo'] = combos[hand]
            
            score = int((speed_metric * 0.4 + acc_metric * 0.3 + quality_metric * 0.3))
            metrics[f'{hand.lower()}_score'] = min(score, 100)
            
        metrics['hitmap_left'] = hl
        metrics['hitmap_right'] = hr
        return metrics
