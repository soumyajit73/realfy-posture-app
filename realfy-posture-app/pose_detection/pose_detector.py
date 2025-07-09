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
    pose = mp_pose.Pose()

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

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            lmk = mp_pose.PoseLandmark

            def xy(lm):
                return [landmarks[lm.value].x, landmarks[lm.value].y]

            def visibility(lm):
                return landmarks[lm.value].visibility

            left_shoulder = xy(lmk.LEFT_SHOULDER)
            left_hip = xy(lmk.LEFT_HIP)
            left_knee = xy(lmk.LEFT_KNEE)
            left_ankle = xy(lmk.LEFT_ANKLE)
            left_toe = xy(lmk.LEFT_FOOT_INDEX)
            left_ear = xy(lmk.LEFT_EAR)

            knee_vis = visibility(lmk.LEFT_KNEE)
            knee_visible = knee_vis > 0.8

            posture_this_frame = "desk_sitting"
            knee_angle = None

            if knee_visible:
                knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                if knee_angle < 140:
                    posture_this_frame = "squat"

            back_angle = calculate_angle(left_shoulder, left_hip, left_knee)
            neck_angle = calculate_angle(left_ear, left_shoulder, left_hip)

            posture_votes[posture_this_frame] += 1

            flags = []
            if posture_this_frame == "squat":
                if back_angle < 100 or back_angle > 170:
                    flags.append("Back angle abnormal during squat (<100° or >170°)")
                if knee_angle is not None and knee_angle > 160:
                    flags.append("Knee too straight during squat (>160°)")
                # Check knee-over-toe
                if knee_visible and left_knee[0] > left_toe[0] + 0.02:
                    flags.append("Knee over toe during squat")
            else:
                if not (150 <= neck_angle <= 185):
                    flags.append("Neck not straight while sitting (outside 150°–185°)")
                if not (150 <= back_angle <= 185):
                    flags.append("Back not straight while sitting (outside 150°–185°)")

            frame_results.append({
                "frame": frame_num,
                "posture_type": posture_this_frame,
                "neck_angle": neck_angle,
                "back_angle": back_angle,
                "knee_angle": knee_angle,
                "flags": flags,
                "bad_posture": len(flags) > 0,
            })

            # Draw landmarks
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )

            # Overlay posture and flags
            y = 30
            cv2.putText(frame, f"Posture (this frame): {posture_this_frame}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            y += 30
            for flag in flags:
                cv2.putText(frame, flag, (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                y += 25

            out.write(frame)

            print(
                f"Frame {frame_num}: "
                f"Posture={posture_this_frame}, "
                f"Neck={neck_angle:.2f}°, "
                f"Back={back_angle:.2f}°, "
                f"Knee={knee_angle if knee_angle else 'N/A'}°, "
                f"Flags={flags}"
            )
        else:
            print(f"Frame {frame_num}: No landmarks detected.")

    cap.release()
    out.release()

    # Majority vote
    dominant_posture = max(posture_votes, key=posture_votes.get)
    print(f"\n[INFO] Dominant posture detected: {dominant_posture}")

    return {
        "posture_type": dominant_posture,
        "frame_results": frame_results
    }
