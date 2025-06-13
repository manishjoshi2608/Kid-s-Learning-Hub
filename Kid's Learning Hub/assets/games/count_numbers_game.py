import os
import sys
import threading
import random
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QFont, QPixmap
# We need to adjust import to go up one level in the folder structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from voice_utils import speak, listen
import pygame

# Initialize pygame mixer and set lower volume
pygame.mixer.init()
pygame.mixer.set_num_channels(8)  # Ensure enough channels for sound effects
DEFAULT_VOLUME = 0.6  # 60% volume for sounds

# Constants - Updated paths to point back to the root structure
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGES_FOLDER = os.path.join(ROOT_DIR, "assets", "images")
FEEDBACK_SOUNDS_FOLDER = os.path.join(ROOT_DIR, "assets", "sounds")

# Get all available image files
def get_all_images():
    images = []
    # Check all files in the images directory
    for file in os.listdir(IMAGES_FOLDER):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            images.append(file)
    return images

# Communication between threads
class VoiceSignals(QObject):
    result_ready = pyqtSignal(str)
    listening_done = pyqtSignal()

class CountNumbersGame(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.mixer.init()
        self.score = 0
        
        # Get all available images
        self.all_images = get_all_images()
        
        # Game state
        self.current_count = 0
        self.current_image = ""
        self.image_widgets = []
        
        # Set up UI and signals
        self.signals = VoiceSignals()
        self.initUI()
        
        # Connect signals
        self.signals.result_ready.connect(self.process_voice_result)
        self.signals.listening_done.connect(self.listening_finished)
        
        # Load the first counting challenge
        self.load_new_challenge()
        self.update_feature_unlocks()
    
    def initUI(self):
        # Set window properties
        self.setWindowTitle('Count the Numbers Game')
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
            QFrame#imageFrame {
                border: 2px solid #7f8c8d;
                border-radius: 15px;
                background-color: white;
                padding: 10px;
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
        title_label = QLabel("Count the Numbers 🔢", self)
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
        
        # Add image frame
        image_frame = QFrame(self)
        image_frame.setObjectName("imageFrame")
        image_frame.setMinimumHeight(300)
        image_frame.setMaximumHeight(400)
        
        # Create grid layout for images
        self.image_grid_layout = QGridLayout(image_frame)
        self.image_grid_layout.setSpacing(10)
        self.image_grid_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(image_frame)
        
        # Status label
        self.status_label = QLabel("How many items do you see?", self)
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
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Answer button
        self.answer_button = QPushButton("Answer 🎤", self)
        self.answer_button.clicked.connect(self.check_answer)
        self.answer_button.setMinimumHeight(50)
        button_layout.addWidget(self.answer_button)
        
        # New challenge button
        self.next_button = QPushButton("New Challenge 🔀", self)
        self.next_button.clicked.connect(self.load_new_challenge)
        self.next_button.setMinimumHeight(50)
        button_layout.addWidget(self.next_button)
        
        main_layout.addLayout(button_layout)
        
        # Add spacer at the bottom
        main_layout.addStretch()
    
    def update_feature_unlocks(self):
        """Update the feature label based on the current score"""
        if self.score < 10:
            self.feature_label.setText("💡 Simple Counting (1-5) (Score < 10)")
        elif 10 <= self.score < 20:
            self.feature_label.setText("📊 Medium Counting (1-10) (Score 10 - 19)")
        else:
            self.feature_label.setText("🧮 Advanced Counting (1-15) (Score 20+)")
    
    def clear_image_grid(self):
        """Clear all images from the grid"""
        # Remove all existing image widgets
        for widget in self.image_widgets:
            self.image_grid_layout.removeWidget(widget)
            widget.deleteLater()
        self.image_widgets = []
    
    def load_new_challenge(self):
        """Load a new counting challenge"""
        # Clear current images
        self.clear_image_grid()
        
        # Determine the range based on score
        if self.score < 10:
            max_count = 5  # Simple counting (1-5)
        elif 10 <= self.score < 20:
            max_count = 10  # Medium counting (1-10)
        else:
            max_count = 15  # Advanced counting (1-15)
            
        # Choose a random count from 1 to max_count
        self.current_count = random.randint(1, max_count)
        
        # Choose a random image for this challenge
        if self.all_images:
            self.current_image = random.choice(self.all_images)
            image_path = os.path.join(IMAGES_FOLDER, self.current_image)
            
            # Calculate grid dimensions based on count
            if self.current_count <= 5:
                cols = min(self.current_count, 3)
            elif self.current_count <= 10:
                cols = min(self.current_count, 4)
            else:
                cols = 5
                
            rows = (self.current_count + cols - 1) // cols  # Ceiling division
            
            # Add the images to the grid
            count = 0
            for row in range(rows):
                for col in range(cols):
                    if count < self.current_count:
                        # Create image label
                        image_label = QLabel()
                        pixmap = QPixmap(image_path)
                        
                        # Scale the image based on count (smaller when more items)
                        if self.current_count <= 5:
                            size = 120
                        elif self.current_count <= 10:
                            size = 100
                        else:
                            size = 80
                            
                        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setAlignment(Qt.AlignCenter)
                        self.image_grid_layout.addWidget(image_label, row, col)
                        self.image_widgets.append(image_label)
                        count += 1
        
        # Update labels
        question = f"How many {os.path.splitext(self.current_image)[0]}s do you see?"
        self.status_label.setText(question)
        self.status_label.setStyleSheet("color: black;")
        self.hint_label.setText("")
        
        # Reset user speech label
        self.user_speech_label.setText("")
        self.user_speech_label.setVisible(False)
        
        # Voice hints only for basic levels
        if self.score < 10:
            threading.Thread(target=lambda: speak(question), daemon=True).start()
    
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
        
        # Process the answer - extract numbers
        correct_answer = False
        
        # Convert word numbers to digits: one -> 1, two -> 2, etc.
        number_words = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15
        }
        
        normalized_answer = answer.lower().strip()
        
        # First check if the answer contains the number as a word
        for word, num in number_words.items():
            if word in normalized_answer and num == self.current_count:
                correct_answer = True
                break
        
        # Also check for digits in the answer
        if not correct_answer:
            if str(self.current_count) in normalized_answer:
                correct_answer = True
        
        if correct_answer:
            # Correct answer
            self.score += 5
            self.status_label.setText(f"Correct! There are {self.current_count} items. ✅")
            self.status_label.setStyleSheet("color: green;")
            
            if self.score < 10:
                threading.Thread(target=lambda: speak(f"Correct! There are {self.current_count} items."), daemon=True).start()
            
            # Play correct sound if file exists
            correct_sound_path = os.path.join(FEEDBACK_SOUNDS_FOLDER, "correct_answer.wav")
            if os.path.exists(correct_sound_path):
                sound = pygame.mixer.Sound(correct_sound_path)
                sound.set_volume(DEFAULT_VOLUME)
                sound.play()
            
            self.hint_label.setText("")
        else:
            # Wrong answer
            self.score = max(0, self.score - 2)
            
            if self.score < 10:
                self.status_label.setText(f"Oops! There are {self.current_count} items. ❌")
                self.status_label.setStyleSheet("color: red;")
                threading.Thread(target=lambda: speak(f"Oops! There are {self.current_count} items."), daemon=True).start()
                self.hint_label.setText("")
            elif 10 <= self.score < 20:
                self.status_label.setText(f"Oops! That's not right. ❌")
                self.status_label.setStyleSheet("color: red;")
                
                # Give a hint based on the correct number
                if self.current_count <= 5:
                    self.hint_label.setText(f"Hint: It's a small number (1-5)")
                elif self.current_count <= 10:
                    self.hint_label.setText(f"Hint: It's between 5 and 10")
                else:
                    self.hint_label.setText(f"Hint: It's more than 10")
            else:
                self.status_label.setText(f"Oops! That's not right. ❌")
                self.status_label.setStyleSheet("color: red;")
                self.hint_label.setText("")
            
            # Play wrong sound if file exists
            wrong_sound_path = os.path.join(FEEDBACK_SOUNDS_FOLDER, "wrong_answer.wav")
            if os.path.exists(wrong_sound_path):
                sound = pygame.mixer.Sound(wrong_sound_path)
                sound.set_volume(DEFAULT_VOLUME)
                sound.play()
        
        # Update score and features
        self.score_label.setText(f"Score: {self.score}")
        self.update_feature_unlocks()
