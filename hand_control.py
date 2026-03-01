import mediapipe as mp
import cv2

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
# Keep a persistent Hands object instead of creating it every frame
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)


def _count_fingers(landmarks):
    """Return number of fingers that appear to be up (0-5).

    landmarks: list of normalized landmark objects
    """
    # Tip ids for thumb, index, middle, ring, pinky
    tip_ids = [4, 8, 12, 16, 20]
    count = 0

    # Thumb: compare x to previous landmark -- handedness/flip can affect sign, but
    # this simple check works on typical webcam frames (and main.py flips the frame).
    try:
        if landmarks[4].x < landmarks[3].x:
            count += 1
    except Exception:
        pass

    # Other fingers: tip y lower than pip y indicates finger is up (smaller y = higher on image)
    for tip in [8, 12, 16, 20]:
        try:
            if landmarks[tip].y < landmarks[tip - 2].y:
                count += 1
        except Exception:
            continue

    return count


def get_hand_gesture(frame):
    """Analyze a BGR frame and return one of: 'LEFT','RIGHT','ACCELERATE','BRAKE', or None."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            count = _count_fingers(landmarks)
            h, w = frame.shape[:2]
            # Draw finger count
            cv2.putText(frame, f"Fingers:{count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

            # If open palm (4 or 5) -> ACCELERATE, fist (0) -> BRAKE
            if count >= 4:
                return "ACCELERATE"
            if count == 0:
                return "BRAKE"

            # Use index finger tip vs wrist to determine left/right (more stable)
            try:
                index_x = landmarks[8].x * w
                wrist_x = landmarks[0].x * w
                dx = index_x - wrist_x
                cv2.putText(frame, f"IdxX:{int(index_x)} WrX:{int(wrist_x)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                # threshold relative to width
                thresh = w * 0.12
                if dx < -thresh:
                    return "LEFT"
                elif dx > thresh:
                    return "RIGHT"
            except Exception:
                pass
    return None
