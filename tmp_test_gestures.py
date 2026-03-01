import numpy as np
import cv2
from hand_control import get_hand_gesture
from eye_control import get_eye_direction

# Create a blank frame (black)
frame = np.zeros((480,640,3), dtype='uint8')
print('Calling get_hand_gesture on blank frame...')
print(get_hand_gesture(frame))
print('Calling get_eye_direction on blank frame...')
print(get_eye_direction(frame))
print('Done')
