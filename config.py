"""
Configuration settings for Gesture-Based Adaptive Reading Interface
Contains themes, default settings, and gesture mappings
"""

# Window settings
WINDOW_TITLE = "Adaptive Reader - Gesture Controlled"
WINDOW_SIZE = "1200x800"
MIN_WINDOW_SIZE = (800, 600)

# Font settings
DEFAULT_FONT_FAMILY = "Georgia"
DEFAULT_FONT_SIZE = 18
MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 48
FONT_SIZE_STEP = 2

# Line spacing (1.0 = single, 1.5 = one and half, 2.0 = double)
DEFAULT_LINE_SPACING = 1.5
MIN_LINE_SPACING = 1.0
MAX_LINE_SPACING = 3.0
LINE_SPACING_STEP = 0.25

# Color themes optimized for older adults (high contrast)
THEMES = {
    "light": {
        "name": "Light",
        "bg": "#FFFFFF",
        "fg": "#1A1A1A",
        "accent": "#0066CC",
        "button_bg": "#E8E8E8",
        "button_fg": "#1A1A1A",
        "highlight": "#FFEB3B"
    },
    "dark": {
        "name": "Dark",
        "bg": "#1E1E1E",
        "fg": "#E8E8E8",
        "accent": "#66B3FF",
        "button_bg": "#3C3C3C",
        "button_fg": "#E8E8E8",
        "highlight": "#FFC107"
    },
    "sepia": {
        "name": "Sepia",
        "bg": "#F5E6D3",
        "fg": "#4A3728",
        "accent": "#8B4513",
        "button_bg": "#E6D5C3",
        "button_fg": "#4A3728",
        "highlight": "#FFD700"
    },
    "high_contrast": {
        "name": "High Contrast",
        "bg": "#000000",
        "fg": "#FFFF00",
        "accent": "#00FFFF",
        "button_bg": "#333333",
        "button_fg": "#FFFF00",
        "highlight": "#FF00FF"
    }
}

DEFAULT_THEME = "light"

# Text-to-Speech settings
TTS_DEFAULT_RATE = 150  # Words per minute (slower for older adults)
TTS_MIN_RATE = 80
TTS_MAX_RATE = 250
TTS_RATE_STEP = 10

# Gesture settings
GESTURE_COOLDOWN = 1.0  # Seconds between gesture recognition (prevents accidental triggers)
GESTURE_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for gesture detection

# Gesture mappings (gesture_name: action)
GESTURE_ACTIONS = {
    "thumbs_up": "increase_font",
    "thumbs_down": "decrease_font",
    "open_palm": "toggle_tts",
    "fist": "stop_tts",
    "point_up": "next_page",
    "peace": "previous_page",
    "swipe_left": "next_page",
    "swipe_right": "previous_page"
}

# Sample text for testing
SAMPLE_TEXT = """Welcome to the Adaptive Reading Interface

This application is designed to make reading easier and more comfortable. You can customize the display to suit your preferences.

Features available:
• Adjust the font size using the controls or hand gestures
• Change the color theme for comfortable reading
• Listen to the text using text-to-speech
• Navigate through pages easily

To get started, you can load a text file using the 'Open File' button, or simply start reading this sample text.

Try using hand gestures to control the reader:
• Thumbs up - Make text larger
• Thumbs down - Make text smaller  
• Open palm - Start or pause reading aloud
• Fist - Stop reading
• Point up - Go to next page
• Peace sign - Go to previous page

This interface was designed with accessibility in mind, focusing on ease of use and comfort for extended reading sessions."""