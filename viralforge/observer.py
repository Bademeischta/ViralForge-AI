import os
import cv2
import json
import logging
import numpy as np
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GameObserver:
    """
    Analyzes game footage frames to detect specific in-game events using computer vision.
    """
    # Regions of Interest defined as relative coordinates (x1, y1, x2, y2)
    ROI_KILLFEED_RELATIVE = (0.807, 0.074, 0.99, 0.44) # 80.7% to 99% width, 7.4% to 44% height

    def __init__(self, frames_dir: str, video_resolution: Tuple[int, int], assets_dir: str = "assets"):
        """
        Initializes the GameObserver.

        Args:
            frames_dir (str): The directory containing extracted game frames.
            video_resolution (Tuple[int, int]): The (width, height) of the video.
            assets_dir (str): The directory containing template images.
        """
        self.frames_dir = frames_dir
        self.assets_dir = assets_dir
        self.video_width, self.video_height = video_resolution

        # Calculate absolute ROI pixels from relative coordinates
        self.roi_killfeed_abs = self._calculate_absolute_roi(self.ROI_KILLFEED_RELATIVE)

        self.templates_valid = True
        self.templates = self._load_templates()
        self.last_detection_map = {}

    def _calculate_absolute_roi(self, relative_roi: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
        """Calculates absolute pixel coordinates for an ROI based on video resolution."""
        x1_rel, y1_rel, x2_rel, y2_rel = relative_roi
        x1 = int(x1_rel * self.video_width)
        y1 = int(y1_rel * self.video_height)
        x2 = int(x2_rel * self.video_width)
        y2 = int(y2_rel * self.video_height)
        return (x1, y1, x2 - x1, y2 - y1) # Return as (x, y, width, height)

    def _load_templates(self) -> Dict[str, np.ndarray]:
        """Loads all template images from the assets directory and validates them."""
        templates = {}
        valorant_templates_path = os.path.join(self.assets_dir, "templates", "valorant")
        if not os.path.exists(valorant_templates_path):
            logging.error(f"Valorant templates directory not found at: {valorant_templates_path}")
            self.templates_valid = False
            return {}

        for icon_file in os.listdir(valorant_templates_path):
            if icon_file.endswith(".png"):
                icon_name = os.path.splitext(icon_file)[0]
                icon_path = os.path.join(valorant_templates_path, icon_file)

                # Check if file is empty or too small
                if not os.path.exists(icon_path) or os.path.getsize(icon_path) < 100: # 100 bytes as a reasonable minimum
                    logging.warning(f"Template file is missing, empty or too small: {icon_path}")
                    self.templates_valid = False
                    continue

                template = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    templates[icon_name] = template
                    logging.info(f"Loaded template: {icon_name}")
                else:
                    logging.warning(f"Could not load template with OpenCV: {icon_path}")
                    self.templates_valid = False

        if not templates:
            logging.error("No valid templates were loaded.")
            self.templates_valid = False

        return templates

    def detect_events_in_frame(self, frame_path: str) -> List[Dict]:
        """
        Analyzes a single frame image for game events.

        Args:
            frame_path (str): The path to the frame image.

        Returns:
            A list of event dictionaries found in this frame.
        """
        events = []
        frame = cv2.imread(frame_path)
        if frame is None:
            return events

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- Killfeed Analysis ---
        x, y, w, h = self.roi_killfeed_abs
        killfeed_roi = gray_frame[y:y+h, x:x+w]

        for template_name, template_img in self.templates.items():
            res = cv2.matchTemplate(killfeed_roi, template_img, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.85) # Confidence threshold

            for pt in zip(*loc[::-1]): # Switch x and y
                # This gives us a unique identifier for a detection at a specific location
                detection_id = f"{template_name}_{pt[1]}" # Use y-coordinate as part of the ID

                # Debouncing: only register if this exact detection is new
                if detection_id not in self.last_detection_map:
                    event_type = 'headshot' if 'headshot' in template_name else 'kill'
                    events.append({
                        'event': 'kill',
                        'type': event_type,
                        'confidence': float(res[pt[1], pt[0]]),
                        'id': detection_id
                    })
                    # Mark this detection as seen in this frame
                    self.last_detection_map[detection_id] = True

        return events

    def analyze_all_frames(self) -> List[Dict]:
        """
        Iterates over all frames, detects events, and performs debouncing.

        Returns:
            A chronologically sorted list of unique, debounced events.
        """
        if not self.templates_valid:
            logging.error("FEHLER: Valorant-Template-Bilder in 'assets/templates/valorant/' fehlen oder sind leer. Der V2-Modus kann ohne gültige Vorlagen nicht ausgeführt werden.")
            return []

        logging.info("Starting analysis of all extracted frames...")
        all_events = []

        frame_files = sorted(os.listdir(self.frames_dir))

        for frame_file in frame_files:
            if not frame_file.endswith(".jpg"):
                continue

            # Reset the "seen" map for each new frame to allow new detections
            current_frame_detections = {}

            frame_path = os.path.join(self.frames_dir, frame_file)
            timestamp_ms = int(os.path.splitext(frame_file)[0].split('_')[1])

            # --- Perform Detection ---
            # We create a temporary map for this frame's detections to handle debouncing
            frame_detection_map = {}

            gray_frame = cv2.cvtColor(cv2.imread(frame_path), cv2.COLOR_BGR2GRAY)
            x, y, w, h = self.roi_killfeed_abs
            killfeed_roi = gray_frame[y:y+h, x:x+w]

            for template_name, template_img in self.templates.items():
                res = cv2.matchTemplate(killfeed_roi, template_img, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= 0.85)

                for pt in zip(*loc[::-1]):
                    # A unique ID based on template and y-position
                    y_pos = pt[1]
                    is_new_event = True

                    # Check against last frame's detections for the same template
                    # to see if this is a continuation of a previous event.
                    for last_y_pos in self.last_detection_map.get(template_name, []):
                        if abs(y_pos - last_y_pos) < 5: # Allow 5-pixel tolerance
                            is_new_event = False
                            break

                    if is_new_event:
                        event_type = 'headshot' if 'headshot' in template_name else 'bodyshot'
                        all_events.append({
                            "timestamp": timestamp_ms / 1000.0,
                            "event": "kill",
                            "details": {"type": event_type, "confidence": float(res[pt[1], pt[0]])}
                        })

                    # Record this detection for the next frame's comparison
                    if template_name not in frame_detection_map:
                        frame_detection_map[template_name] = []
                    frame_detection_map[template_name].append(y_pos)

            # The current frame's detections become the last frame's detections for the next iteration
            self.last_detection_map = frame_detection_map

        logging.info(f"Analysis complete. Found {len(all_events)} unique game events.")

        # Save the result to a JSON file
        output_path = os.path.join(os.path.dirname(self.frames_dir), "analysis.json")
        with open(output_path, 'w') as f:
            json.dump(all_events, f, indent=2)
        logging.info(f"Event analysis saved to {output_path}")

        return all_events