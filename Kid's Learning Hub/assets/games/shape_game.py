import os
import sys
import threading
import random
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QPen, QBrush, QPainterPath
import math
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
SOUNDS_FOLDER = os.path.join(ROOT_DIR, "assets", "sounds")

# Shape data with names and drawing functions
SHAPES = [
    "circle", 
    "square", 
    "triangle", 
    "star", 
    "heart", 
    "rectangle", 
    "pentagon", 
    "hexagon", 
    "octagon", 
    "diamond"
]

# We'll use a single color for all shapes
DEFAULT_COLOR = (64, 158, 255)  # A nice blue color

# Custom widget for drawing shapes only
class ShapeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shape = "circle"     # Default shape
        self.setMinimumSize(300, 300)
        self.setMaximumSize(300, 300)
        
        # Set white background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(255, 255, 255))
        self.setPalette(palette)
        
        # Add border
        self.setStyleSheet("border: 2px solid #7f8c8d; border-radius: 10px;")
    
    def set_shape(self, shape):
        self.shape = shape
        self.update()  # Request a repaint
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        r, g, b = DEFAULT_COLOR
        
        # Draw shape
        painter.setPen(QPen(QColor(max(0, r - 50), max(0, g - 50), max(0, b - 50)), 3))
        painter.setBrush(QBrush(QColor(r, g, b)))
        
        # Draw based on shape type
        if self.shape == "circle":
            diameter = min(width, height) - 40
            painter.drawEllipse((width - diameter) // 2, (height - diameter) // 2, diameter, diameter)
        
        elif self.shape == "square":
            side = min(width, height) - 40
            painter.drawRect((width - side) // 2, (height - side) // 2, side, side)
        
        elif self.shape == "rectangle":
            width_rect = min(width, height) - 40
            height_rect = width_rect * 0.6  # Make it rectangular, not square
            painter.drawRect(
                (width - width_rect) // 2,
                (height - height_rect) // 2,
                width_rect,
                height_rect
            )
        
        elif self.shape == "triangle":
            side = min(width, height) - 40
            x1 = (width - side) // 2
            y1 = (height + side) // 2  # Bottom left
            x2 = width // 2  # Top middle
            y2 = (height - side) // 2
            x3 = (width + side) // 2  # Bottom right
            y3 = (height + side) // 2
            points = [
                QPoint(x1, y1),
                QPoint(x2, y2),
                QPoint(x3, y3)
            ]
            painter.drawPolygon(*points)
        
        elif self.shape == "star":
            radius = min(width, height) // 2 - 20
            center_x = width // 2
            center_y = height // 2
            
            # Create a 5-pointed star
            points = []
            for i in range(10):
                angle = (i * 36) * 3.14159 / 180
                # Alternate between outer and inner radius
                point_radius = radius if i % 2 == 0 else radius // 2
                x = center_x + int(point_radius * math.sin(angle))
                y = center_y - int(point_radius * math.cos(angle))
                points.append(QPoint(x, y))
            
            painter.drawPolygon(*points)
            
        elif self.shape == "heart":
            # Draw a simple heart
            width_rect = min(width, height) - 40
            height_rect = width_rect  # Make it square
            x = (self.width() - width_rect) // 2
            y = (self.height() - height_rect) // 2
            
            # Create a path for the heart shape
            path = QPainterPath()
            path.moveTo(x + width_rect // 2, y + height_rect * 0.75)
            path.cubicTo(
                x + width_rect * 0.25, y + height_rect * 0.4,
                x, y + height_rect * 0.5,
                x + width_rect // 2, y
            )
            path.cubicTo(
                x + width_rect, y + height_rect * 0.5,
                x + width_rect * 0.75, y + height_rect * 0.4,
                x + width_rect // 2, y + height_rect * 0.75
            )
            painter.drawPath(path)
        
        elif self.shape == "pentagon":
            # Draw a pentagon
            radius = min(width, height) // 2 - 20
            center_x = width // 2
            center_y = height // 2
            
            # Create a 5-sided polygon
            points = []
            for i in range(5):
                angle = (i * 72 - 90) * 3.14159 / 180  # Start from the top
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                points.append(QPoint(x, y))
            
            painter.drawPolygon(*points)
            
        elif self.shape == "hexagon":
            # Draw a hexagon
            radius = min(width, height) // 2 - 20
            center_x = width // 2
            center_y = height // 2
            
            # Create a 6-sided polygon
            points = []
            for i in range(6):
                angle = (i * 60) * 3.14159 / 180
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                points.append(QPoint(x, y))
            
            painter.drawPolygon(*points)
            
        elif self.shape == "octagon":
            # Draw an octagon
            radius = min(width, height) // 2 - 20
            center_x = width // 2
            center_y = height // 2
            
            # Create an 8-sided polygon
            points = []
            for i in range(8):
                angle = (i * 45) * 3.14159 / 180
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                points.append(QPoint(x, y))
            
            painter.drawPolygon(*points)
            
        elif self.shape == "diamond":
            # Draw a diamond (rhombus)
            width_diamond = min(width, height) - 40
            height_diamond = width_diamond  # Equal sides
            
            center_x = width // 2
            center_y = height // 2
            
            points = [
                QPoint(center_x, center_y - height_diamond // 2),  # Top
                QPoint(center_x + width_diamond // 2, center_y),    # Right
                QPoint(center_x, center_y + height_diamond // 2),   # Bottom
                QPoint(center_x - width_diamond // 2, center_y)     # Left
            ]
            
            painter.drawPolygon(*points)

# Communication between threads
class VoiceSignals(QObject):
    result_ready = pyqtSignal(str)
    listening_done = pyqtSignal()

class ShapeGame(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.mixer.init()
        self.score = 0
        self.current_shape = ""
        self.shape_list = SHAPES
        self.signals = VoiceSignals()
        self.initUI()
        
        # Connect signals
        self.signals.result_ready.connect(self.process_voice_result)
        self.signals.listening_done.connect(self.listening_finished)
        
        # Load the first shape
        self.load_random_shape()
        self.update_feature_unlocks()
    
    def initUI(self):
        # Set window properties
        self.setWindowTitle('Shape Game')
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
            QFrame#colorFrame {
                border: 2px solid #7f8c8d;
                border-radius: 10px;
                background-color: white;
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
        title_label = QLabel("Shape Game ▽", self)
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
        
        # Add shape widget
        self.shape_widget = ShapeWidget(self)
        main_layout.addWidget(self.shape_widget, 0, Qt.AlignCenter)
        
        # Status label
        self.status_label = QLabel("What shape is this?", self)
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
        
        # New Shape button
        self.next_button = QPushButton("Next Shape 🔀", self)
        self.next_button.clicked.connect(self.load_random_shape)
        self.next_button.setMinimumHeight(50)
        main_layout.addWidget(self.next_button)
        
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
            
    def load_random_shape(self):
        """Load a random shape"""
        # Choose random shape
        self.current_shape = random.choice(self.shape_list)
        
        # Update the widget
        self.shape_widget.set_shape(self.current_shape)
        
        # Update labels
        question = "What shape is this?"
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
        
        normalized_answer = answer.lower().strip()
        
        # Detect negations to avoid false positives
        negations = ["not", "no", "n't", "never", "none"]
        contains_negation = any(neg in normalized_answer for neg in negations)
        contains_correct_word = self.current_shape in normalized_answer
        
        if contains_correct_word and not contains_negation:
            # Correct answer
            self.score += 5
            self.status_label.setText(f"Correct! It's a {self.current_shape}. ✅")
            self.status_label.setStyleSheet("color: green;")
            
            if self.score < 10:
                threading.Thread(target=lambda: speak(f"Correct! It's a {self.current_shape}"), daemon=True).start()
            
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
                self.status_label.setText(f"Oops! It's a {self.current_shape}. ❌")
                self.status_label.setStyleSheet("color: red;")
                threading.Thread(target=lambda: speak(f"Oops! It's a {self.current_shape}"), daemon=True).start()
                self.hint_label.setText("")
            elif 10 <= self.score < 20:
                self.status_label.setText(f"Oops! It's wrong. ❌")
                self.status_label.setStyleSheet("color: red;")
                self.hint_label.setText(f"Hint: Starts with '{self.current_shape[0]}'")
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
