import cv2
import mediapipe as mp

mp_face = mp.solutions.face_mesh
# Keep FaceMesh persistent to avoid re-creating each call
face_mesh = mp_face.FaceMesh(static_image_mode=False, refine_landmarks=True,
                             max_num_faces=1, min_detection_confidence=0.5,
                             min_tracking_confidence=0.5)


def get_eye_direction(frame):
    """Return a tuple (direction, blink) where direction is 'LEFT'/'RIGHT'/None and
    blink is True when a blink is detected.

    Blink detection is a simple EAR-like heuristic using vertical eyelid landmarks.
    """
    h, w = frame.shape[:2]
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    if not results or not results.multi_face_landmarks:
        return None, False

    landmarks = results.multi_face_landmarks[0].landmark
    # Guard against unexpected results length
    if len(landmarks) <= 263:
        return None, False

    left_eye_x = landmarks[33].x * w
    right_eye_x = landmarks[263].x * w
    nose_x = landmarks[1].x * w

    # Simple blink detection: use upper/lower eyelid landmarks
    # FaceMesh approximate landmarks for eye upper/lower
    # left eye: 159 (upper), 145 (lower); right eye: 386 (upper), 374 (lower)
    blink = False
    try:
        le_upper = landmarks[159]
        le_lower = landmarks[145]
        re_upper = landmarks[386]
        re_lower = landmarks[374]
        # convert to pixel distances
        le_vert = abs((le_upper.y - le_lower.y) * h)
        re_vert = abs((re_upper.y - re_lower.y) * h)
        # horizontal widths
        le_width = abs((landmarks[33].x - landmarks[133].x) * w) if len(landmarks) > 133 else 1
        re_width = abs((landmarks[362].x - landmarks[263].x) * w) if len(landmarks) > 362 else 1
        # EAR-like ratio
        le_ear = le_vert / (le_width + 1e-6)
        re_ear = re_vert / (re_width + 1e-6)
        ear = (le_ear + re_ear) / 2.0
        # Empirical threshold — tuned to typical camera sizes; user adjustments may be needed
        if ear < 0.02:
            blink = True
        # draw debug
        cv2.putText(frame, f"EAR:{ear:.3f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
    except Exception:
        blink = False

    # Debug drawings removed: do not draw eye/nose debug dots on camera overlay

    # Prefer iris/eye center if present (some face_mesh configs provide iris landmarks)
    iris_left_idx = 468 if len(landmarks) > 468 else None
    iris_right_idx = 473 if len(landmarks) > 473 else None
    if iris_left_idx and iris_right_idx:
        try:
            # compute left and right iris positions
            iris_left_x = landmarks[iris_left_idx].x * w
            iris_left_y = landmarks[iris_left_idx].y * h
            iris_right_x = landmarks[iris_right_idx].x * w
            iris_right_y = landmarks[iris_right_idx].y * h
            # Draw small green dots for left and right iris centers to show per-eye tracking
            try:
                cv2.circle(frame, (int(iris_left_x), int(iris_left_y)), 3, (0, 255, 0), -1)
            except Exception:
                pass
            try:
                cv2.circle(frame, (int(iris_right_x), int(iris_right_y)), 3, (0, 255, 0), -1)
            except Exception:
                pass

            # compute gaze center (x) from iris landmarks and draw a small label
            gaze_center_x = (iris_left_x + iris_right_x) / 2
            cv2.putText(frame, f"GazeX:{int(gaze_center_x)}", (10,80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            # Decide left/right based on horizontal gaze position
            if gaze_center_x < w*0.45:
                return "LEFT", blink
            if gaze_center_x > w*0.55:
                return "RIGHT", blink
        except Exception:
            pass

    # Fallback using nose relative to eyes
    tol = max(10, w * 0.02)
    if nose_x < left_eye_x - tol:
        return "LEFT", blink
    elif nose_x > right_eye_x + tol:
        return "RIGHT", blink
    return None, blink
