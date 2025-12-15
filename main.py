"""
Gesture-Based Adaptive Reading Interface for Older Adults
Main entry point for the application

Author: [Your Name]
Course: [Your Course]
Date: [Date]

Description:
    This application provides an accessible reading interface designed
    for older adults, featuring gesture-based controls, customizable
    display settings, and text-to-speech functionality.
"""

import tkinter as tk
from gui import AdaptiveReaderGUI


def main():
    """Initialize and run the application"""
    # Create the main window
    root = tk.Tk()
    
    # Set window icon (optional - add an .ico file if you have one)
    # root.iconbitmap('assets/icon.ico')
    
    # Initialize the GUI
    app = AdaptiveReaderGUI(root)
    
    # Configure window close behavior
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    
    # Start the application
    print("=" * 50)
    print("Adaptive Reader - Gesture Controlled")
    print("=" * 50)
    print("Application started successfully!")
    print("\nKeyboard shortcuts:")
    print("  Ctrl + '+' or '='  : Increase font size")
    print("  Ctrl + '-'         : Decrease font size")
    print("  Left Arrow         : Previous page")
    print("  Right Arrow        : Next page")
    print("  Ctrl + O           : Open file")
    print("=" * 50)
    
    root.mainloop()


def on_closing(root):
    """Handle application closing"""
    print("\nClosing application...")
    root.destroy()


if __name__ == "__main__":
    main()