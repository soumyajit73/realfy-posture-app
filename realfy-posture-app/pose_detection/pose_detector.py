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

def process_video(video_path, output_path="output.mp4"):
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )

    cap = cv2.VideoCapture(video_path)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_results = []
    frame_num = 0

    posture_votes = {"squat": 0, "desk_sitting": 0}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        posture_this_frame = "desk_sitting"
        knee_angle = None
        back_angle = None
        neck_angle = None
        knee_side = None
        flags = []

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            lmk = mp_pose.PoseLandmark

            def xy(lm):
                return [landmarks[lm.value].x, landmarks[lm.value].y]

            def visibility(lm):
                return landmarks[lm.value].visibility

            # Get landmarks
            left_shoulder = xy(lmk.LEFT_SHOULDER)
            left_hip = xy(lmk.LEFT_HIP)
            left_knee = xy(lmk.LEFT_KNEE)
            left_ankle = xy(lmk.LEFT_ANKLE)
            left_ear = xy(lmk.LEFT_EAR)

            right_shoulder = xy(lmk.RIGHT_SHOULDER)
            right_hip = xy(lmk.RIGHT_HIP)
            right_knee = xy(lmk.RIGHT_KNEE)
            right_ankle = xy(lmk.RIGHT_ANKLE)
            right_ear = xy(lmk.RIGHT_EAR)

            left_knee_vis = visibility(lmk.LEFT_KNEE)
            right_knee_vis = visibility(lmk.RIGHT_KNEE)

            knee_candidates = []
            if left_knee_vis > 0.1:
                knee_candidates.append((left_hip, left_knee, left_ankle, left_knee_vis, "left"))
            if right_knee_vis > 0.1:
                knee_candidates.append((right_hip, right_knee, right_ankle, right_knee_vis, "right"))

            if knee_candidates:
                best = max(knee_candidates, key=lambda x: x[3])
                knee_angle = calculate_angle(best[0], best[1], best[2])
                knee_side = best[4]
                print(f"Frame {frame_num}: Using {knee_side} knee, angle={knee_angle:.2f}")

            # Compute other angles
            back_angle = calculate_angle(left_shoulder, left_hip, left_knee)
            neck_angle = calculate_angle(left_ear, left_shoulder, left_hip)

            # Determine posture
            if knee_angle is not None and knee_angle < 140:
                posture_this_frame = "squat"
            elif back_angle is not None and back_angle < 150:
                posture_this_frame = "squat"
            else:
                posture_this_frame = "desk_sitting"

            posture_votes[posture_this_frame] += 1

            # Check for bad posture flags
            if posture_this_frame == "squat":
                if back_angle < 100 or back_angle > 170:
                    flags.append("Back angle abnormal during squat (<100° or >170°)")
                if knee_angle is not None and knee_angle > 160:
                    flags.append("Knee too straight during squat (>160°)")
            elif posture_this_frame == "desk_sitting":
                if neck_angle is not None and not (150 <= neck_angle <= 185):
                    flags.append("Neck not straight while sitting (outside 150°–185°)")
                if back_angle is not None and not (150 <= back_angle <= 185):
                    flags.append("Back not straight while sitting (outside 150°–185°)")

            result_dict = {
                "frame": frame_num,
                "posture_type": posture_this_frame,
                "flags": flags,
                "bad_posture": len(flags) > 0,
            }

            # Include angles only for the relevant posture
            if posture_this_frame == "squat":
                result_dict["knee_angle"] = knee_angle
                result_dict["back_angle"] = back_angle
            elif posture_this_frame == "desk_sitting":
                result_dict["neck_angle"] = neck_angle
                result_dict["back_angle"] = back_angle

            frame_results.append(result_dict)

            # Draw landmarks and overlay text
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )

            y = 30
            cv2.putText(frame, f"Posture: {posture_this_frame}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            y += 30

            if posture_this_frame == "desk_sitting":
                if neck_angle is not None:
                    cv2.putText(frame, f"Neck Angle: {neck_angle:.1f}", (10, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    y += 25
                if back_angle is not None:
                    cv2.putText(frame, f"Back Angle: {back_angle:.1f}", (10, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    y += 25
            elif posture_this_frame == "squat":
                if knee_side is not None:
                    cv2.putText(frame, f"Knee: {knee_side} | Angle: {knee_angle:.1f}", (10, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    y += 25
                if back_angle is not None:
                    cv2.putText(frame, f"Back Angle: {back_angle:.1f}", (10, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    y += 25

            for flag in flags:
                cv2.putText(frame, flag, (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                y += 25

            print(f"Frame {frame_num}: Posture={posture_this_frame}, Angles={result_dict}, Flags={flags}")
            out.write(frame)

        else:
            print(f"Frame {frame_num}: No landmarks detected.")

    cap.release()
    out.release()

    dominant_posture = max(posture_votes, key=posture_votes.get)
    print(f"\n[INFO] Dominant posture detected: {dominant_posture}")

    return {
        "posture_type": dominant_posture,
        "frame_results": frame_results
    }