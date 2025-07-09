import cv2
import mediapipe as mp
import math

def calculate_angle(a, b, c):
    """
    Calculates the angle (in degrees) between three points (a, b, c) at vertex b.
    """
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0]) -
        math.atan2(a[1] - b[1], a[0] - b[0])
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
    knee_angles = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            left_shoulder = [
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            ]
            left_hip = [
                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
            ]
            left_knee = [
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
            ]
            left_ankle = [
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
            ]
            left_toe = [
                landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y
            ]
            left_ear = [
                landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y
            ]

            # Compute angles
            knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            back_angle = calculate_angle(left_shoulder, left_hip, left_knee)
            neck_angle = calculate_angle(left_ear, left_shoulder, left_hip)

            knee_angles.append(knee_angle)

            frame_results.append({
                "frame": frame_num,
                "knee_angle": knee_angle,
                "back_angle": back_angle,
                "neck_angle": neck_angle,
                "flags": [],
            })
        else:
            print(f"Frame {frame_num}: No landmarks detected.")

    cap.release()

    # Decide posture type
    avg_knee_angle = sum(knee_angles) / len(knee_angles) if knee_angles else 180
    posture_type = "squat" if avg_knee_angle < 140 else "desk_sitting"

    # New thresholds:
    # For desk_sitting:
    # - Neck angle should be between 150° and 185°
    # - Back angle should be between 150° and 185°
    #
    # For squat:
    # - Back angle between 100° and 170°
    # - Knee angle < 160°

    for frame in frame_results:
        flags = []

        if posture_type == "squat":
            # Squat posture rules
            if frame["back_angle"] < 100 or frame["back_angle"] > 170:
                flags.append("Back angle abnormal during squat (<100° or >170°)")
            if frame["knee_angle"] > 160:
                flags.append("Knee too straight during squat (>160°)")
        else:
            # Desk sitting posture rules
            if not (150 <= frame["neck_angle"] <= 185):
                flags.append("Neck not straight while sitting (outside 150°–185°)")
            if not (150 <= frame["back_angle"] <= 185):
                flags.append("Back not straight while sitting (outside 150°–185°)")

        frame["bad_posture"] = len(flags) > 0
        frame["flags"] = flags

        # Print debug info
        print(
            f"Frame {frame['frame']}: "
            f"Neck={frame['neck_angle']:.2f}°, "
            f"Back={frame['back_angle']:.2f}°, "
            f"Knee={frame['knee_angle']:.2f}°, "
            f"Posture={posture_type}, Flags={flags}"
        )

    return {
        "posture_type": posture_type,
        "frame_results": frame_results
    }
