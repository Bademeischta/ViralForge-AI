import os
import cv2
import json
import logging
import pytesseract
import numpy as np
from typing import List, Dict, Tuple, Union
from thefuzz import fuzz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GameObserver:
    """
    Analyzes game footage frames to detect ego-centric kill events using
    a multi-factor verification process.
    """
    ROI_KILLFEED_RELATIVE = (0.80, 0.15, 0.99, 0.40)
    ROI_NAME_IN_ENTRY_RELATIVE = (0.10, 0.10, 0.45, 0.90)

    EGO_KILL_COLOR_LOWER_HSV = np.array([30, 100, 100])
    EGO_KILL_COLOR_UPPER_HSV = np.array([70, 255, 255])

    def __init__(self, frames_dir: str, video_resolution: Tuple[int, int], player_name: str, assets_dir: str = "assets"):
        self.frames_dir = frames_dir
        self.video_width, self.video_height = video_resolution
        self.player_name = player_name
        self.assets_dir = assets_dir

        self.agent_templates = self._load_templates_from_dir("agents")
        self.icon_templates = self._load_templates_from_dir("icons")

        self.last_killfeed_text = ""

    def _calculate_absolute_roi(self, relative_roi: Tuple[float, float, float, float], base_shape) -> Tuple[int, int, int, int]:
        base_h, base_w = base_shape[:2]
        x1 = int(relative_roi[0] * base_w)
        y1 = int(relative_roi[1] * base_h)
        x2 = int(relative_roi[2] * base_w)
        y2 = int(relative_roi[3] * base_h)
        return (x1, y1, x2 - x1, y2 - y1)

    def _load_templates_from_dir(self, dir_name: str) -> Dict[str, np.ndarray]:
        templates = {}
        template_path = os.path.join(self.assets_dir, "templates", "valorant", dir_name)
        if not os.path.exists(template_path): return templates
        for f_name in os.listdir(template_path):
            if f_name.endswith(".png"):
                name = os.path.splitext(f_name)[0]
                path = os.path.join(template_path, f_name)
                if os.path.getsize(path) > 10:
                    templates[name] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        return templates

    def _is_ego_kill_color(self, image_entry: np.ndarray) -> bool:
        hsv_image = cv2.cvtColor(image_entry, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_image, self.EGO_KILL_COLOR_LOWER_HSV, self.EGO_KILL_COLOR_UPPER_HSV)
        green_percentage = (cv2.countNonZero(mask) / (image_entry.shape[0] * image_entry.shape[1])) * 100
        return green_percentage > 10

    def _verify_player_name(self, image_entry: np.ndarray) -> bool:
        x, y, w, h = self._calculate_absolute_roi(self.ROI_NAME_IN_ENTRY_RELATIVE, image_entry.shape)
        name_roi = image_entry[y:y+h, x:x+w]
        preprocessed_roi = self._preprocess_for_ocr(name_roi)
        try:
            extracted_text = pytesseract.image_to_string(preprocessed_roi, config=r'--oem 3 --psm 7').strip()
            return fuzz.ratio(extracted_text.lower(), self.player_name.lower()) > 85
        except Exception:
            return False

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh

    def _find_template_in_roi(self, roi: np.ndarray, templates: Dict[str, np.ndarray]) -> bool:
        """Checks if any of the provided templates match within the ROI."""
        for t_name, t_img in templates.items():
            if t_img is None or roi.shape[0] < t_img.shape[0] or roi.shape[1] < t_img.shape[1]:
                continue
            res = cv2.matchTemplate(roi, t_img, cv2.TM_CCOEFF_NORMED)
            if np.max(res) > 0.8: # Confidence threshold
                return True
        return False

    def analyze_all_frames(self) -> List[Dict]:
        logging.info("Starting V2 Ego-Centric Analysis...")
        all_events = []
        frame_files = sorted(os.listdir(self.frames_dir))

        for frame_file in frame_files:
            frame_path = os.path.join(self.frames_dir, frame_file)
            timestamp_ms = int(os.path.splitext(frame_file)[0].split('_')[1])
            frame = cv2.imread(frame_path)
            if frame is None: continue

            # This is a simplified logic that treats the whole killfeed as one entry
            # A real implementation would use contour detection to find individual entries
            x, y, w, h = self._calculate_absolute_roi(self.ROI_KILLFEED_RELATIVE, frame.shape)
            killfeed_entry_roi = frame[y:y+h, x:x+w]

            # --- The Four-Factor Check ---
            # 1. Color Filter
            if not self._is_ego_kill_color(killfeed_entry_roi):
                continue

            # 2. & 3. Template Checks (simplified: check if present anywhere in the entry)
            agent_found = self._find_template_in_roi(cv2.cvtColor(killfeed_entry_roi, cv2.COLOR_BGR2GRAY), self.agent_templates)
            icon_found = self._find_template_in_roi(cv2.cvtColor(killfeed_entry_roi, cv2.COLOR_BGR2GRAY), self.icon_templates)

            # 4. Name Check
            name_verified = self._verify_player_name(killfeed_entry_roi)

            # --- Debouncing & Event Creation ---
            # Create a unique string for the current state to debounce
            current_text = f"agent:{agent_found}_icon:{icon_found}_name:{name_verified}"
            if name_verified and agent_found and icon_found and current_text != self.last_killfeed_text:
                all_events.append({
                    "timestamp": timestamp_ms / 1000.0,
                    "event": "kill",
                    "details": { "type": "Ego-Kill (Verified)", "text": f"{self.player_name} kill" }
                })
            self.last_killfeed_text = current_text

        logging.info(f"V2 Analysis complete. Found {len(all_events)} verified ego-centric game events.")

        output_path = os.path.join(os.path.dirname(self.frames_dir), "analysis.json")
        with open(output_path, 'w') as f:
            json.dump(all_events, f, indent=2)
        logging.info(f"Event analysis saved to {output_path}")

        return all_events