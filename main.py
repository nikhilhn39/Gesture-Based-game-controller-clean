import os
import cv2
import threading
import pygame
from hand_control import get_hand_gesture
from eye_control import get_eye_direction
from car_game import game_loop, WIDTH, HEIGHT  # import the cleaned game loop and screen size

# Reduce TensorFlow/TF-Lite verbosity
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

pygame.init()

# Global variables and synchronization
current_hand_action = None
current_eye_action = None
current_blink = False
running = True
action_lock = threading.Lock()


def _open_camera_tried_indices(indices=(0, 1, 2, 3, 4)):
    """Try multiple camera indices and return a cv2.VideoCapture if successful, else None."""
    for idx in indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"Camera opened at index {idx}")
            return cap
        cap.release()
    return None


def camera_control():
    """Thread to handle webcam input and detect gestures."""
    global current_hand_action, current_eye_action, current_blink, running
    cap = _open_camera_tried_indices()
    if cap is None:
        print("ERROR: Could not open any camera. Camera feed will be disabled.")
        running = False
        return

    while running:
        ret, frame = cap.read()
        if not ret:
            print("Camera read failed; stopping camera thread.")
            break

        # Mirror frame so gestures map intuitively
        frame = cv2.flip(frame, 1)

        # Get gestures
        hand_action = get_hand_gesture(frame)
        eye_direction, blink = get_eye_direction(frame)

        # Save both under lock so game can combine them
        with action_lock:
            current_hand_action = hand_action
            current_eye_action = eye_direction
            current_blink = blink

        # Display camera feed with action (show both) and blink status
        display = frame.copy()
        overlay = f"Hand:{hand_action} Eye:{eye_direction} Blink:{blink}"
        cv2.putText(display, overlay, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        try:
            cv2.imshow("Camera Feed", display)
        except Exception as e:
            print(f"Error displaying camera: {e}")
        
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()


def get_current_action():
    """Return a (hand_action, eye_action) tuple in a thread-safe way."""
    with action_lock:
        return (current_hand_action, current_eye_action)


def get_current_blink():
    """Return current blink boolean in a thread-safe way."""
    with action_lock:
        return current_blink


def _show_retry_menu(final_score):
    """Display a simple Pygame retry menu. Returns True to retry, False to quit."""
    # Create overlay
    font_large = pygame.font.Font(None, 72)
    font_med = pygame.font.Font(None, 36)

    retry = None
    blink_was_true = False
    while retry is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # simple approximate button areas
                if WIDTH // 2 - 120 < mx < WIDTH // 2 - 20 and HEIGHT // 2 + 40 < my < HEIGHT // 2 + 90:
                    return True
                if WIDTH // 2 + 20 < mx < WIDTH // 2 + 120 and HEIGHT // 2 + 40 < my < HEIGHT // 2 + 90:
                    return False
        # Accept blink as a retry trigger
        try:
            blink_now = get_current_blink()
            if blink_now and not blink_was_true:
                return True
            blink_was_true = bool(blink_now)
        except Exception:
            pass

        # draw overlay
        screen = pygame.display.get_surface()
        if screen is None:
            screen = pygame.display.set_mode((500, 700))
        screen.fill((0, 0, 0))
        go_text = font_large.render("GAME OVER", True, (255, 0, 0))
        score_text = font_med.render(f"Score: {final_score}", True, (255, 255, 255))
        retry_text = font_med.render("Press R or blink to Retry", True, (200, 200, 200))
        quit_text = font_med.render("Press Q/ESC or click Quit", True, (200, 200, 200))

        screen.blit(go_text, (250 - go_text.get_width() // 2, 200))
        screen.blit(score_text, (250 - score_text.get_width() // 2, 280))
        # draw buttons
        pygame.draw.rect(screen, (0, 180, 0), (250 - 120, 360, 100, 50))
        pygame.draw.rect(screen, (180, 0, 0), (250 + 20, 360, 100, 50))
        screen.blit(font_med.render("Retry", True, (255,255,255)), (250 - 120 + 20, 370))
        screen.blit(font_med.render("Quit", True, (255,255,255)), (250 + 20 + 25, 370))
        screen.blit(retry_text, (250 - retry_text.get_width() // 2, 430))
        screen.blit(quit_text, (250 - quit_text.get_width() // 2, 470))

        pygame.display.update()
        pygame.time.delay(100)


if __name__ == "__main__":
    # Start camera thread (runs cv2 windows). Run Pygame/game loop in the main thread.
    cam_thread = threading.Thread(target=camera_control, daemon=True)
    try:
        cam_thread.start()

        # Main loop: run game, then show retry menu when it ends
        while True:
            collision, final_score = game_loop(get_current_action)
            # If game_loop returned due to window close (no collision) then exit
            if not collision:
                break
            # Show retry menu; if user wants to retry, the loop will run game_loop again
            do_retry = _show_retry_menu(final_score)
            if not do_retry:
                break

    except Exception as e:
        print("Unhandled exception in main:", e)
    finally:
        # Ensure camera thread stops
        running = False
        cam_thread.join(timeout=2)
        pygame.quit()
