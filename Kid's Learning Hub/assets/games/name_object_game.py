import os
import sys
import threading
import json
import random
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPixmap
# We need to adjust import to go up one level in the folder structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from voice_utils import speak, listen
import pygame

# Initialize pygame mixer and set lower volume
pygame.mixer.init()
pygame.mixer.set_num_channels(8)  # Ensure enough channels for sound effects
DEFAULT_VOLUME = 0.3  # 30% volume

# Constants - Updated paths to point back to the root structure
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OBJECTS_FOLDER = os.path.join(ROOT_DIR, "assets", "images")
SOUNDS_FOLDER = os.path.join(ROOT_DIR, "assets", "sounds")

# Object data
OBJECTS = {
    "apple.png": "apple",
    "ball.png": "ball",
    "cat.png": "cat",
    "cow.png": "cow",
    "dog.png": "dog",
    "elephant.png": "elephant",
    "fan.png": "fan",
    "grass.png": "grass",
    "horse.jpg": "horse",
    "igloo.jpg": "igloo",
    "jar.png": "jar",
    "kangaroo.jpg": "kangaroo",
    "lemon.jpg": "lemon",
    "lion.png": "lion",
    "mango.jpg": "mango",
    "nest.jpg": "nest",
    "owl.jpg": "owl",
    "panda.jpg": "panda",
    "quill.png": "quill",
    "rainbow.jpg": "rainbow",
    "stars.jpg": "stars",
    "torch.png": "torch",
    "umbrella.jpg": "umbrella",
    "volcano.jpg": "volcano",
    "waterfall.jpg": "waterfall", 
    "xylophone.png": "xylophone",
    "yak.jpg": "yak",
    "zebra.jpg": "zebra"
}

# Communication between threads
class VoiceSignals(QObject):
    result_ready = pyqtSignal(str)
    listening_done = pyqtSignal()

class NameObjectGame(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.mixer.init()
        self.score = 0
        self.current_index = 0
        
        # Create the object list and shuffle it initially
        self.object_list = list(OBJECTS.items())
        random.shuffle(self.object_list)
        
        self.signals = VoiceSignals()
        self.initUI()
        self.current = {"image_file": "", "correct_answer": ""}
        
        # Connect signals
        self.signals.result_ready.connect(self.process_voice_result)
        self.signals.listening_done.connect(self.listening_finished)
        
        # Load the first object
        self.load_object_by_index(self.current_index)
        self.update_feature_unlocks()
    
    def initUI(self):
        # Set window properties
        self.setWindowTitle('Name the Object Game')
        self.showMaximized()
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f8ff;
            }
            QLabel#titleLabel {
                color: #2e86de;
                font-size: 28px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton {
                background-color: #54a0ff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 16px;
                margin: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0984e3;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QPushButton#exitBtn {
                background-color: #e74c3c;
                color: white;
                max-width: 100px;
                margin-top: 20px;
            }
            QPushButton#exitBtn:hover {
                background-color: #c0392b;
            }
            QLabel#statusLabel {
                font-size: 20px;
                font-weight: bold;
            }
            QLabel#scoreLabel {
                font-size: 18px;
                color: #2c3e50;
            }
            QLabel#featureLabel {
                font-size: 16px;
                color: #3498db;
            }
            QLabel#hintLabel {
                font-size: 16px;
                color: #8e44ad;
                font-style: italic;
            }
            QLabel#userSpeechLabel {
                font-size: 18px;
                color: #16a085;
                border: 1px solid #16a085;
                border-radius: 5px;
                padding: 8px;
                background-color: #e8f8f5;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Add title
        title_label = QLabel("Name the Object 📱", self)
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Add exit button at top-right
        exit_btn_layout = QHBoxLayout()
        exit_btn_layout.addStretch()
        exit_button = QPushButton("Exit", self)
        exit_button.setObjectName("exitBtn")
        exit_button.clicked.connect(self.close)
        exit_btn_layout.addWidget(exit_button)
        main_layout.addLayout(exit_btn_layout)
        
        # Add image label
        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumSize(400, 300)
        main_layout.addWidget(self.img_label)
        
        # Status label
        self.status_label = QLabel("What is this?", self)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # User speech label - shows what the user said
        self.user_speech_label = QLabel("", self)
        self.user_speech_label.setObjectName("userSpeechLabel")
        self.user_speech_label.setAlignment(Qt.AlignCenter)
        self.user_speech_label.setWordWrap(True)
        self.user_speech_label.setMinimumHeight(50)
        self.user_speech_label.setVisible(False)  # Initially hidden
        main_layout.addWidget(self.user_speech_label)
        
        # Score label
        self.score_label = QLabel(f"Score: {self.score}", self)
        self.score_label.setObjectName("scoreLabel")
        self.score_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.score_label)
        
        # Feature label
        self.feature_label = QLabel("", self)
        self.feature_label.setObjectName("featureLabel")
        self.feature_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.feature_label)
        
        # Hint label
        self.hint_label = QLabel("", self)
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.hint_label)
        
        # Answer button
        self.answer_button = QPushButton("Answer 🎤", self)
        self.answer_button.clicked.connect(self.check_answer)
        self.answer_button.setMinimumHeight(50)
        main_layout.addWidget(self.answer_button)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)
        
        prev_button = QPushButton("← Previous", self)
        prev_button.clicked.connect(self.prev_object)
        nav_layout.addWidget(prev_button)
        
        next_button = QPushButton("Next 🔀", self)
        next_button.clicked.connect(self.random_object)
        nav_layout.addWidget(next_button)
        
        main_layout.addLayout(nav_layout)
        
        # Add spacer at the bottom
        main_layout.addStretch()
    
    def random_object(self):
        """Load a random object"""
        # Choose a random index different from the current one (if possible)
        if len(self.object_list) > 1:
            new_index = self.current_index
            while new_index == self.current_index:
                new_index = random.randrange(0, len(self.object_list))
            self.current_index = new_index
        else:
            self.current_index = 0
        self.load_object_by_index(self.current_index)
    
    def update_feature_unlocks(self):
        """Update the feature label based on the current score"""
        if self.score < 10:
            self.feature_label.setText("💡 Voice Hint Enabled (Score < 10)")
        elif 10 <= self.score < 20:
            self.feature_label.setText("📝 Text Hint Enabled (Score 10 - 19)")
        else:
            self.feature_label.setText("🚫 No Hints - Pro Mode (Score 20+)")
    
    def load_object_by_index(self, index):
        """Load an object image by its index in the list"""
        if 0 <= index < len(self.object_list):
            image_file, correct_answer = self.object_list[index]
            self.current["image_file"] = image_file
            self.current["correct_answer"] = correct_answer
            
            # Load image
            image_path = os.path.join(OBJECTS_FOLDER, image_file)
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(pixmap)
            
            # Update labels
            self.status_label.setText("What is this?")
            self.status_label.setStyleSheet("color: black;")
            self.hint_label.setText("")
            
            # Reset user speech label
            self.user_speech_label.setText("")
            self.user_speech_label.setVisible(False)
            
            # Play "What is this?" voice hint if score < 10
            if self.score < 10:
                threading.Thread(target=lambda: speak("What is this?"), daemon=True).start()
    
    def check_answer(self):
        """Start the voice recognition process"""
        self.answer_button.setEnabled(False)
        self.status_label.setText("Listening...")
        self.status_label.setStyleSheet("color: blue;")
        self.hint_label.setText("")
        
        # Start listening in a separate thread to avoid blocking the UI
        threading.Thread(target=self._listen_thread, daemon=True).start()
    
    def _listen_thread(self):
        """Thread function for voice recognition"""
        answer = listen()
        self.signals.result_ready.emit(answer)
        self.signals.listening_done.emit()
    
    def listening_finished(self):
        """Called when listening is done"""
        self.answer_button.setEnabled(True)
    
    def process_voice_result(self, answer):
        """Process the voice recognition result"""
        print(f"You said: {answer}")
        
        # Display what the user said
        if answer and answer.strip():
            self.user_speech_label.setText(f"You said: \"{answer}\"")
            self.user_speech_label.setVisible(True)
        else:
            self.user_speech_label.setVisible(False)
        
        if not answer or not answer.strip():
            self.status_label.setText("Didn't catch that. Try again!")
            self.status_label.setStyleSheet("color: orange;")
            return
        
        normalized_answer = answer.lower().strip()
        
        # Detect negations to avoid false positives
        negations = ["not", "no", "n't", "never", "none"]
        contains_negation = any(neg in normalized_answer for neg in negations)
        contains_correct_word = self.current["correct_answer"] in normalized_answer
        
        if contains_correct_word and not contains_negation:
            # Correct answer
            self.score += 5
            self.status_label.setText(f"Correct! It's a {self.current['correct_answer']}. ✅")
            self.status_label.setStyleSheet("color: green;")
            
            if self.score < 10:
                threading.Thread(target=lambda: speak(f"Correct! It's a {self.current['correct_answer']}"), daemon=True).start()
            
            # Play correct sound if file exists
            correct_sound_path = os.path.join(SOUNDS_FOLDER, "correct_answer.wav")
            if os.path.exists(correct_sound_path):
                sound = pygame.mixer.Sound(correct_sound_path)
                sound.set_volume(DEFAULT_VOLUME)
                sound.play()
            
            self.hint_label.setText("")
        else:
            # Wrong answer
            self.score = max(0, self.score - 2)
            
            if self.score < 10:
                self.status_label.setText(f"Oops! It's a {self.current['correct_answer']}. ❌")
                self.status_label.setStyleSheet("color: red;")
                threading.Thread(target=lambda: speak(f"Oops! It's a {self.current['correct_answer']}"), daemon=True).start()
                self.hint_label.setText("")
            elif 10 <= self.score < 20:
                self.status_label.setText(f"Oops! It's wrong. ❌")
                self.status_label.setStyleSheet("color: red;")
                self.hint_label.setText(f"Hint: Starts with '{self.current['correct_answer'][0]}'")
            else:
                self.status_label.setText(f"Oops! It's wrong. ❌")
                self.status_label.setStyleSheet("color: red;")
                self.hint_label.setText("")
            
            # Play wrong sound if file exists
            wrong_sound_path = os.path.join(SOUNDS_FOLDER, "wrong_answer.wav")
            if os.path.exists(wrong_sound_path):
                sound = pygame.mixer.Sound(wrong_sound_path)
                sound.set_volume(DEFAULT_VOLUME)
                sound.play()
        
        # Update score and features
        self.score_label.setText(f"Score: {self.score}")
        self.update_feature_unlocks()
    
    def next_object(self):
        """Redirect to random_object for backward compatibility"""
        self.random_object()
    
    def prev_object(self):
        """Load the previous object"""
        self.current_index = (self.current_index - 1) % len(self.object_list)
        self.load_object_by_index(self.current_index)
