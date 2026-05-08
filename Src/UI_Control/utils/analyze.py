import numpy as np
import pandas as pd
from skeleton.detect_skeleton import PoseEstimater


class PoseAnalyzer:
    def __init__(self, pose_estimater:PoseEstimater):
        self.pose_estimater = pose_estimater
        self.angle_dict = self.pose_estimater.joints['haple']['angle_dict']
        self.analyze_info = []
        self.analyze_df = pd.DataFrame()
        self.processed_frames = set()
        self.distancePerPixel = 0

    def _calculate_angle(self, A, B, C):
        BA = np.array(A) - np.array(B)
        BC = np.array(C) - np.array(B)
        dot_product = np.dot(BA, BC)
        magnitude_BA = np.linalg.norm(BA)
        magnitude_BC = np.linalg.norm(BC)
        cos_angle = dot_product / (magnitude_BA * magnitude_BC)
        angle_rad = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        return np.degrees(angle_rad)

    def _update_analyze_information(self, person_kpt):
        info = {}
        for angle_name, kpt_list in self.angle_dict.items():
            A = person_kpt[kpt_list[0]][:2]
            B = person_kpt[kpt_list[1]][:2]
            C = person_kpt[kpt_list[2]][:2]
            info[angle_name] = [self._calculate_angle(A, B, C), [np.array(A), np.array(B), np.array(C)]]
        return info

    def get_frame_angle_data(self, frame_num: int = None, angle_name: str = None):
        if self.analyze_df.empty:
            return pd.DataFrame(), []
        condition = pd.Series([True] * len(self.analyze_df))
        if frame_num is not None:
            condition &= (self.analyze_df['frame_number'] == frame_num)
        data = self.analyze_df.loc[condition]
        if data.empty:
            return None, []
        if angle_name is not None:
            if frame_num is not None:
                angle_value = data['angle'].iloc[0][angle_name]
                return data, angle_value
            else:
                frame_numbers = self.analyze_df['frame_number'].unique()
                angles = [row['angle'][angle_name][0] for _, row in self.analyze_df.iterrows() if angle_name in row['angle']]
                return frame_numbers, angles
        return data, []

    def reset(self):
        self.analyze_info = []
        self.analyze_df = pd.DataFrame()
        self.processed_frames = set()
