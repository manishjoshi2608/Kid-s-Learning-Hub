import os
import sys
import threading
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
DEFAULT_VOLUME = 0.6  # 60% volume for animal sounds to be clearer

# Constants - Updated paths to point back to the root structure
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANIMAL_SOUNDS_FOLDER = os.path.join(ROOT_DIR, "assets", "sounds", "animals")
FEEDBACK_SOUNDS_FOLDER = os.path.join(ROOT_DIR, "assets", "sounds")

# Animal data - mapping sound files to animal names
ANIMALS = {
    "cat.wav": "cat",
    "cow.wav": "cow",
    "dog.wav": "dog",
    "elephant.wav": "elephant", 
    "horse.wav": "horse",
    "sheep.wav": "sheep",
    "tiger.wav": "tiger"
}

# Communication between threads
class VoiceSignals(QObject):
    result_ready = pyqtSignal(str)
    listening_done = pyqtSignal()

class AnimalSoundGame(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.mixer.init()
        self.score = 0
        self.current_index = 0
        
        # Create the animal list and shuffle it initially
        self.animal_list = list(ANIMALS.items())
        random.shuffle(self.animal_list)
        
        self.signals = VoiceSignals()
        self.initUI()
        self.current = {"sound_file": "", "correct_answer": ""}
        
        # Connect signals
        self.signals.result_ready.connect(self.process_voice_result)
        self.signals.listening_done.connect(self.listening_finished)
        
        # Load the first animal sound
        self.load_random_animal()
        self.update_feature_unlocks()
    
    def initUI(self):
        # Set window properties
        self.setWindowTitle('Animal Sound Game')
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
            QPushButton#playBtn {
                background-color: #2ecc71;
                font-size: 22px;
                min-width: 200px;
                min-height: 100px;
                border-radius: 15px;
            }
            QPushButton#playBtn:hover {
                background-color: #27ae60;
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
            QLabel#animalIcon {
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
        title_label = QLabel("Animal Sound Game 🐾", self)
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
        
        # Add animal icon (question mark initially)
        self.animal_icon = QLabel(self)
        self.animal_icon.setObjectName("animalIcon")
        self.animal_icon.setAlignment(Qt.AlignCenter)
        self.animal_icon.setMinimumSize(200, 200)
        self.animal_icon.setMaximumSize(200, 200)
        self.animal_icon.setText("❓")
        self.animal_icon.setFont(QFont("Arial", 100))
        main_layout.addWidget(self.animal_icon, 0, Qt.AlignCenter)
        
        # Play sound button
        self.play_button = QPushButton("Play Sound 🔊", self)
        self.play_button.setObjectName("playBtn")
        self.play_button.clicked.connect(self.play_current_sound)
        main_layout.addWidget(self.play_button, 0, Qt.AlignCenter)
        
        # Status label
        self.status_label = QLabel("Which animal made that sound?", self)
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
        
        # New Sound button
        self.next_button = QPushButton("Next Animal 🔀", self)
        self.next_button.clicked.connect(self.load_random_animal)
        self.next_button.setMinimumHeight(50)
        button_layout.addWidget(self.next_button)
        
        main_layout.addLayout(button_layout)
        
        # Add spacer at the bottom
        main_layout.addStretch()
    
    def update_feature_unlocks(self):
        """Update the feature label based on the current score"""
        if self.score < 10:
            self.feature_label.setText("💡 Voice Hint Enabled (Score < 10)")
        elif 10 <= self.score < 20:
            self.feature_label.setText("📝 Text Hint Enabled (Score 10 - 19)")
        else:
            self.feature_label.setText("🚫 No Hints - Pro Mode (Score 20+)")
    
    def load_random_animal(self):
        """Load a random animal sound"""
        # Choose a random animal
        self.current_index = random.randrange(0, len(self.animal_list))
        sound_file, animal_name = self.animal_list[self.current_index]
        
        self.current["sound_file"] = sound_file
        self.current["correct_answer"] = animal_name
        
        # Reset the animal icon to question mark
        self.animal_icon.setText("❓")
        self.animal_icon.setPixmap(QPixmap())  # Clear any previous image
        
        # Update labels
        question = "Which animal made that sound?"
        self.status_label.setText(question)
        self.status_label.setStyleSheet("color: black;")
        self.hint_label.setText("")
        
        # Reset user speech label
        self.user_speech_label.setText("")
        self.user_speech_label.setVisible(False)
        
        # Voice hints only for basic levels
        if self.score < 10:
            threading.Thread(target=lambda: speak(question), daemon=True).start()
        
        # Automatically play the sound
        self.play_current_sound()
    
    def play_current_sound(self):
        """Play the current animal sound"""
        if self.current["sound_file"]:
            sound_path = os.path.join(ANIMAL_SOUNDS_FOLDER, self.current["sound_file"])
            if os.path.exists(sound_path):
                # Disable the play button temporarily to prevent multiple plays
                self.play_button.setEnabled(False)
                
                sound = pygame.mixer.Sound(sound_path)
                sound.set_volume(DEFAULT_VOLUME)
                sound.play()
                
                # Re-enable the button after a short delay
                threading.Timer(1.5, lambda: self.play_button.setEnabled(True)).start()
    
    def show_animal_image(self, show_correct=True):
        """Show the animal image after answering"""
        if show_correct:
            animal = self.current["correct_answer"]
            # Try to find an image for this animal
            possible_extensions = ['.png', '.jpg', '.jpeg']
            for ext in possible_extensions:
                image_path = os.path.join(ROOT_DIR, "assets", "images", f"{animal}{ext}")
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    scaled_pixmap = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.animal_icon.setPixmap(scaled_pixmap)
                    self.animal_icon.setText("")  # Clear the text
                    return
            
            # If no image is found, just show the animal name
            self.animal_icon.setText(animal.title())
            self.animal_icon.setFont(QFont("Arial", 24, QFont.Bold))
    
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
            
            # Show the animal image
            self.show_animal_image(True)
            
            if self.score < 10:
                threading.Thread(target=lambda: speak(f"Correct! It's a {self.current['correct_answer']}"), daemon=True).start()
            
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
                self.status_label.setText(f"Oops! It's a {self.current['correct_answer']}. ❌")
                self.status_label.setStyleSheet("color: red;")
                threading.Thread(target=lambda: speak(f"Oops! It's a {self.current['correct_answer']}"), daemon=True).start()
                # Show the correct animal
                self.show_animal_image(True)
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
            wrong_sound_path = os.path.join(FEEDBACK_SOUNDS_FOLDER, "wrong_answer.wav")
            if os.path.exists(wrong_sound_path):
                sound = pygame.mixer.Sound(wrong_sound_path)
                sound.set_volume(DEFAULT_VOLUME)
                sound.play()
        
        # Update score and features
        self.score_label.setText(f"Score: {self.score}")
        self.update_feature_unlocks()
