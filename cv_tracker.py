import math
import os
import cv2

class HandDexterityTracker:
    def __init__(self, max_analysis_side=960, frame_stride=1):
        self.max_analysis_side = max_analysis_side
        self.frame_stride = max(1, frame_stride)
        
        # Load templates
        self.template_left = None
        self.template_right = None
        
        if os.path.exists('templates/left_text_template.png'):
            self.template_left = cv2.imread('templates/left_text_template.png', cv2.IMREAD_COLOR)
        if os.path.exists('templates/right_text_template.png'):
            self.template_right = cv2.imread('templates/right_text_template.png', cv2.IMREAD_COLOR)
            
    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError('Unable to open the uploaded video file.')

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or math.isnan(fps):
            fps = 30.0
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            cap.release()
            raise ValueError('Video metadata is invalid.')
        
        # Center grid boundaries
        cw_start, cw_end = width // 3, 2 * width // 3
        ch_start, ch_end = height // 3, 2 * height // 3
        
        # Stats
        stats = {
            'Left': {'points': [], 'center_frames': 0, 'visible_frames': 0},
            'Right': {'points': [], 'center_frames': 0, 'visible_frames': 0}
        }

        full_path_left = []
        full_path_right = []
        frame_timestamps_ms = []
        
        hitmap_size = 20
        hitmap_left = [[0]*hitmap_size for _ in range(hitmap_size)]
        hitmap_right = [[0]*hitmap_size for _ in range(hitmap_size)]
        
        frame_idx = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            timestamp_ms = int((frame_idx / fps) * 1000)
            frame_timestamps_ms.append(timestamp_ms)

            left_point = None
            right_point = None

            if frame_idx % self.frame_stride == 0:
                analysis_frame = self._prepare_frame(image)
                # Rescale coordinates back to original size if resized
                scale_x = width / analysis_frame.shape[1]
                scale_y = height / analysis_frame.shape[0]

                left_point, right_point = self._collect_frame_stats(
                    analysis_frame, scale_x, scale_y, stats, width, height, 
                    cw_start, cw_end, ch_start, ch_end, hitmap_left, hitmap_right, timestamp_ms
                )

            full_path_left.append(left_point)
            full_path_right.append(right_point)

            frame_idx += 1
                        
        cap.release()
        
        metrics = self._calculate_metrics(stats, width, height, hitmap_left, hitmap_right, len(frame_timestamps_ms))
        metrics['full_path_left'] = full_path_left
        metrics['full_path_right'] = full_path_right
        metrics['frame_timestamps_ms'] = frame_timestamps_ms
        metrics['video_width'] = width
        metrics['video_height'] = height
        metrics['fps'] = fps
        return metrics

    def _prepare_frame(self, frame):
        height, width = frame.shape[:2]
        largest_side = max(width, height)
        if largest_side <= self.max_analysis_side:
            return frame

        scale = self.max_analysis_side / float(largest_side)
        resized_width = max(1, int(width * scale))
        resized_height = max(1, int(height * scale))
        return cv2.resize(frame, (resized_width, resized_height), interpolation=cv2.INTER_AREA)

    def _collect_frame_stats(self, frame, scale_x, scale_y, stats, width, height, cw_start, cw_end, ch_start, ch_end, hitmap_left, hitmap_right, timestamp_ms):
        left_point = None
        right_point = None
        
        # Helper to match template
        def match_and_get_center(template, threshold=0.75):
            if template is None: return None, 0
            tw, th = template.shape[1], template.shape[0]
            if scale_x != 1.0 or scale_y != 1.0:
                tw = max(1, int(tw / scale_x))
                th = max(1, int(th / scale_y))
                template_scaled = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA)
            else:
                template_scaled = template

            res = cv2.matchTemplate(frame, template_scaled, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= threshold:
                center_x = int((max_loc[0] + tw / 2) * scale_x)
                center_y = int((max_loc[1] + th / 2) * scale_y)
                return (center_x, center_y), max_val
            return None, max_val

        # Detect
        pt_left, conf_left = match_and_get_center(self.template_left)
        pt_right, conf_right = match_and_get_center(self.template_right)
        
        # Since 'มือซ้าย' and 'มือขวา' look similar, suppress the weaker match if they overlap
        if pt_left and pt_right:
            dx = pt_left[0] - pt_right[0]
            dy = pt_left[1] - pt_right[1]
            dist = math.hypot(dx, dy)
            if dist < 100: # They are matching the same text
                if conf_left > conf_right:
                    pt_right = None
                else:
                    pt_left = None

        if pt_left:
            x, y = pt_left
            stats['Left']['points'].append((timestamp_ms, x, y))
            stats['Left']['visible_frames'] += 1
            left_point = [x, y]
            if cw_start <= x <= cw_end and ch_start <= y <= ch_end:
                stats['Left']['center_frames'] += 1
            hx = min(max(int((x / width) * len(hitmap_left[0])), 0), len(hitmap_left[0]) - 1)
            hy = min(max(int((y / height) * len(hitmap_left)), 0), len(hitmap_left) - 1)
            hitmap_left[hy][hx] += 1

        if pt_right:
            x, y = pt_right
            stats['Right']['points'].append((timestamp_ms, x, y))
            stats['Right']['visible_frames'] += 1
            right_point = [x, y]
            if cw_start <= x <= cw_end and ch_start <= y <= ch_end:
                stats['Right']['center_frames'] += 1
            hx = min(max(int((x / width) * len(hitmap_right[0])), 0), len(hitmap_right[0]) - 1)
            hy = min(max(int((y / height) * len(hitmap_right)), 0), len(hitmap_right) - 1)
            hitmap_right[hy][hx] += 1

        return left_point, right_point

    def _calculate_metrics(self, stats, w, h, hl, hr, total_video_frames):
        metrics = {}
        max_diagonal = math.hypot(w, h)
        
        for hand in ['Left', 'Right']:
            points = stats[hand]['points']
            total_frames = stats[hand]['visible_frames']
            center_frames = stats[hand]['center_frames']
            coverage_ratio = total_frames / total_video_frames if total_video_frames > 0 else 0.0
            
            if len(points) < 3:
                metrics[f'{hand.lower()}_speed'] = 20.0
                metrics[f'{hand.lower()}_accuracy'] = 20.0
                metrics[f'{hand.lower()}_quality'] = 20.0
                metrics[f'{hand.lower()}_center_ratio'] = 0.0
                metrics[f'{hand.lower()}_coverage_ratio'] = coverage_ratio
                metrics[f'{hand.lower()}_score'] = 0
                continue

            segments = [
                (
                    math.hypot(points[i][1] - points[i - 1][1], points[i][2] - points[i - 1][2]),
                    max((points[i][0] - points[i - 1][0]) / 1000.0, 1e-3)
                )
                for i in range(1, len(points))
            ]
            velocities = [distance / duration for distance, duration in segments if duration > 0]
            average_velocity = sum(velocities) / len(velocities) if velocities else 0.0

            target_velocity = max_diagonal * 1.4
            speed_metric = 20 + (80 * min(average_velocity / target_velocity, 1.0))

            total_path_length = sum(distance for distance, _ in segments)
            net_displacement = math.hypot(points[-1][1] - points[0][1], points[-1][2] - points[0][2])
            raw_accuracy = net_displacement / total_path_length if total_path_length > 0 else 0
            acc_metric = min(30 + (raw_accuracy * 300), 100.0)

            mean_velocity = average_velocity
            variance = sum((velocity - mean_velocity) ** 2 for velocity in velocities) / len(velocities) if velocities else 0.0
            stability_ratio = max(1.0 - math.sqrt(variance) / target_velocity, 0.0)
            quality_metric = 30 + (70 * stability_ratio)

            center_ratio = center_frames / total_frames if total_frames > 0 else 0.0

            metrics[f'{hand.lower()}_speed'] = min(max(speed_metric, 20), 100)
            metrics[f'{hand.lower()}_accuracy'] = min(max(acc_metric, 20), 100)
            metrics[f'{hand.lower()}_quality'] = min(max(quality_metric, 20), 100)
            metrics[f'{hand.lower()}_center_ratio'] = center_ratio
            metrics[f'{hand.lower()}_coverage_ratio'] = coverage_ratio

            if hand == 'Left':
                w_acc = 0.70
                w_qual = 0.50
            else:
                w_acc = 0.37
                w_qual = 0.20
                
            score = int(acc_metric * w_acc + quality_metric * w_qual) + 1
            metrics[f'{hand.lower()}_score'] = min(max(score, 0), 100)
            
        metrics['hitmap_left'] = hl
        metrics['hitmap_right'] = hr
        return metrics
