# CSE-518
Gesture-Based Adaptive Reading

Gesture-Based Adaptive Reading Interface for Older Adults
A Python-based accessible reading application that uses hand gestures for control, designed specifically for older adults with vision and motor impairments.
Features

🖐️ Gesture Control - Control the app using 6 intuitive hand gestures
📖 Text Customization - Font size (12-48pt), 4 high-contrast themes, adjustable line spacing
🔊 Text-to-Speech - Natural Microsoft Edge voices with speed control
📄 File Support - Read .txt and .pdf documents
⌨️ Keyboard Shortcuts - Traditional controls available as backup
🎥 Real-time Feedback - Live camera feed shows gesture recognition

Gesture Controls
GestureAction
👍 Thumbs UpIncrease font size
👎 Thumbs DownDecrease font size
✋ Open PalmPlay/Pause text-to-speech
✊ FistStop text-to-speech
☝️ Point UpNext page
✌️ Peace SignPrevious page


Requirements

Python 3.8 or higher
Webcam (720p or better recommended)
Windows 10+, macOS 10.15+, or Linux
Internet connection (for first-time TTS voice download)

Installation

Clone the repository
git clone <repository-url>
cd gesture_reader

Create virtual environment
python -m venv venv

Activate virtual environment
Windows:
venv\Scripts\activate

Install dependencies
pip install -r requirements.txt


Usage
Start the application
python main.py

Enable gesture control
Click "Enable Gestures" button
Camera window will open showing your hand tracking


Load a document
Click "📂 Open File" to load .txt or .pdf files
Or use the sample text provided


Customize reading experience
Use A+/A- buttons or gestures to adjust font size
Switch themes for different lighting conditions
Adjust line spacing for comfortable reading


Use text-to-speech
Click "▶ Play" or show open palm gesture
Adjust speed slider for preferred reading pace
Select different voices from dropdown

Keyboard Shortcuts
Ctrl + = or Ctrl + + - Increase font size
Ctrl + - - Decrease font size
Left Arrow - Previous page
Right Arrow - Next page
Space - Toggle text-to-speech
Esc - Stop text-to-speech
Ctrl + O - Open file

Project Structure
gesture_reader/
├── main.py                 # Application entry point
├── config.py              # Configuration settings and constants
├── gui.py                 # User interface and main logic
├── tts_engine.py          # Text-to-speech functionality
├── gesture_controller.py  # Gesture recognition system
└── requirements.txt       # Python dependencies

Technologies Used
Python 3.11 - Core application
Tkinter - GUI framework
OpenCV - Camera capture and image processing
MediaPipe - Hand landmark detection
Edge-TTS - Neural text-to-speech (Microsoft voices)
PyGame - Audio playback
PyMuPDF - PDF text extraction
Pillow - Image processing

Troubleshooting
Camera not opening:
Close other applications using the camera (Zoom, Teams, etc.)
Check camera permissions in system settings
Try restarting the application

Gestures not recognized:
Ensure good lighting (avoid backlighting)
Keep hand 30-50cm from camera
Hold gestures steady for ~1 second

Text-to-speech not working:
Check internet connection (needed for first download)
Verify audio output is not muted
Try selecting a different voice

Module not found errors:
Ensure virtual environment is activated
Run pip install -r requirements.txt again

System Performance
Gesture Recognition: 30 FPS, ~92% accuracy
Latency: 330ms (with stabilization)
CPU Usage: 15-25% on Intel Core i5
Memory: ~150MB base + loaded documents

Limitations
Requires good lighting for gesture recognition
Text-based PDFs only (no scanned images)
Single-user gesture tracking
Gesture recognition may be affected by hand size and skin tone

Future Enhancements
Machine learning-based gesture classification
Voice command integration
Bookmark and annotation system
Multi-language support
Mobile/tablet optimization

Author
Parth Kambli
Student ID: 117313635
Course: CSE-518
Stony Brook University
License
This project is created for academic purposes as part of CSE-518 coursework.

Acknowledgments
MediaPipe by Google for hand tracking technology
Microsoft Edge TTS for high-quality neural voices
Senior community center participants for user testing feedback

