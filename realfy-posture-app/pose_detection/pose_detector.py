import cv2
import mediapipe as mp
import math
import sys
import json

# Helper to calculate angle between 3 points
def calculate_angle(a, b, c):
    angle = math.degrees(
        math.atan2(c[1]-b[1], c[0]-b[0]) -
        math.atan2(a[1]-b[1], a[0]-b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle

def process_video(video_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(video_path)

    frame_results = []
    frame_num = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = pose.process(rgb_frame)

        posture_flags = []

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Example points for back angle
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]

            back_angle = calculate_angle(left_shoulder, left_hip, left_knee)

            if back_angle < 150:
                posture_flags.append("Back angle too small (< 150°)")

            frame_results.append({
                "frame": frame_num,
                "bad_posture": len(posture_flags) > 0,
                "flags": posture_flags,
                "back_angle": back_angle
            })

    cap.release()

    print(json.dumps(frame_results, indent=2))

if __name__ == "__main__":
    video_path = sys.argv[1]
    process_video(video_path)
