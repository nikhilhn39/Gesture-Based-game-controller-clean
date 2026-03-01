🚗 Gesture-Based Car Racing Game Controller

A Python-based car racing game controlled using hand and eye gestures instead of a keyboard.
This project combines Computer Vision + Pygame to create a touchless gaming experience.

📌 Project Overview

This system uses:
🎮 Pygame for the racing game interface
👋 Hand gesture detection for steering control
👁 Eye control module for additional interaction
📷 OpenCV + MediaPipe for real-time gesture tracking
The player can control the car using hand movements detected via webcam.

🛠 Technologies Used
Python 3.10+
OpenCV
MediaPipe
Pygame
NumPy

Project Structure
CarRacingGestureProject/
│
├── main.py              # Main game controller
├── car_game.py          # Racing game logic
├── hand_control.py      # Hand gesture detection
├── eye_control.py       # Eye tracking module
├── tmp_test_gestures.py # Testing gesture detection
├── assets/              # Game images & sounds
├── venv/                # Virtual environment
└── README.md

Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/nikhilhn39/Gesture-Based-game-controller.git
cd Gesture-Based-game-controller

2️⃣ Create Virtual Environment (Recommended)
python -m venv venv
venv\Scripts\activate   # Windows

Install Dependencies
pip install -r requirements.txt
If no requirements file, install manually
pip install opencv-python mediapipe pygame numpy

Run the Game
python main.py
