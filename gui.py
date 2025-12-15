"""
GUI Module for Gesture-Based Adaptive Reading Interface
Handles the main window, text display, and control panels
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import cv2
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import config
from tts_engine import TTSEngine
from gesture_controller import GestureController


class AdaptiveReaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_SIZE)
        self.root.minsize(*config.MIN_WINDOW_SIZE)
        
        # Current settings
        self.current_font_size = config.DEFAULT_FONT_SIZE
        self.current_theme = config.DEFAULT_THEME
        self.current_line_spacing = config.DEFAULT_LINE_SPACING
        self.current_file_path = None
        
        # Text content management
        self.full_text = config.SAMPLE_TEXT
        self.current_page = 0
        self.pages = []
        self.chars_per_page = 2000
        
        # Initialize TTS engine
        self.tts = TTSEngine(
            root=self.root,
            on_complete_callback=self._on_tts_complete
        )
        
        # Initialize Gesture controller
        self.gesture_controller = GestureController(
            on_gesture_callback=self._on_gesture_detected
        )
        self.gesture_thread = None
        self.gesture_window = None
        self.gesture_label = None
        
        # Build the interface
        self._setup_ui()
        self._apply_theme(self.current_theme)
        self._paginate_text()
        self._display_current_page()
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Create all UI components"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control bar (pack first at top)
        self._create_top_controls()
        
        # TTS controls (pack second at top)
        self._create_tts_controls()
        
        # Bottom control bar (pack at bottom BEFORE text area)
        self._create_bottom_controls()
        
        # Settings panel (pack at bottom BEFORE text area)
        self._create_settings_panel()
        
        # Text display area (pack last, will fill remaining space)
        self._create_text_area()
    
    def _create_top_controls(self):
        """Create the top control bar with file and theme options"""
        top_frame = tk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File controls (left side)
        file_frame = tk.Frame(top_frame)
        file_frame.pack(side=tk.LEFT)
        
        self.open_btn = tk.Button(
            file_frame, text="📂 Open File", font=("Arial", 12),
            command=self.open_file, padx=15, pady=8
        )
        self.open_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.file_label = tk.Label(
            file_frame, text="No file loaded - showing sample text",
            font=("Arial", 10)
        )
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Theme controls (right side)
        theme_frame = tk.Frame(top_frame)
        theme_frame.pack(side=tk.RIGHT)
        
        tk.Label(theme_frame, text="Theme:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.theme_buttons = {}
        for theme_key, theme_data in config.THEMES.items():
            btn = tk.Button(
                theme_frame, text=theme_data["name"], font=("Arial", 10),
                command=lambda t=theme_key: self._apply_theme(t),
                padx=10, pady=5
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.theme_buttons[theme_key] = btn
    
    def _create_tts_controls(self):
        """Create TTS control bar with play/pause/stop and speed"""
        tts_frame = tk.Frame(self.main_frame)
        tts_frame.pack(fill=tk.X, pady=5)
        
        # Left side - playback controls
        controls_frame = tk.Frame(tts_frame)
        controls_frame.pack(side=tk.LEFT)
        
        tk.Label(controls_frame, text="🔊 Read Aloud:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.play_btn = tk.Button(
            controls_frame, text="▶ Play", font=("Arial", 11),
            command=self.tts_play, padx=12, pady=5
        )
        self.play_btn.pack(side=tk.LEFT, padx=3)
        
        self.pause_btn = tk.Button(
            controls_frame, text="⏸ Pause", font=("Arial", 11),
            command=self.tts_pause, padx=12, pady=5, state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = tk.Button(
            controls_frame, text="⏹ Stop", font=("Arial", 11),
            command=self.tts_stop, padx=12, pady=5, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
        # TTS status label
        self.tts_status = tk.Label(
            controls_frame, text="Ready", font=("Arial", 10)
        )
        self.tts_status.pack(side=tk.LEFT, padx=15)
        
        # Right side - speed control
        speed_frame = tk.Frame(tts_frame)
        speed_frame.pack(side=tk.RIGHT)
        
        tk.Label(speed_frame, text="Speed:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=config.TTS_DEFAULT_RATE)
        self.speed_scale = tk.Scale(
            speed_frame, from_=config.TTS_MIN_RATE, to=config.TTS_MAX_RATE,
            orient=tk.HORIZONTAL, variable=self.speed_var,
            command=self._on_speed_change, length=150,
            showvalue=False
        )
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = tk.Label(
            speed_frame, text=f"{config.TTS_DEFAULT_RATE} wpm", font=("Arial", 10)
        )
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        # Voice selection
        tk.Label(speed_frame, text="Voice:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(15, 5))
        
        voices = self.tts.get_available_voices()
        voice_names = [name[:20] for i, name in voices]
        
        self.voice_var = tk.StringVar(value=voice_names[0] if voice_names else "Default")
        self.voice_dropdown = ttk.Combobox(
            speed_frame, textvariable=self.voice_var,
            values=voice_names, state="readonly", width=15
        )
        self.voice_dropdown.pack(side=tk.LEFT, padx=5)
        self.voice_dropdown.bind("<<ComboboxSelected>>", self._on_voice_change)
    
    def _create_text_area(self):
        """Create the main text display area"""
        text_frame = tk.Frame(self.main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        self.text_display = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=(config.DEFAULT_FONT_FAMILY, self.current_font_size),
            padx=30,
            pady=20,
            yscrollcommand=scrollbar.set,
            cursor="arrow",
            state=tk.DISABLED
        )
        self.text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_display.yview)
    
    def _create_bottom_controls(self):
        """Create bottom bar with navigation and font controls"""
        bottom_frame = tk.Frame(self.main_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Navigation (left)
        nav_frame = tk.Frame(bottom_frame)
        nav_frame.pack(side=tk.LEFT)
        
        self.prev_btn = tk.Button(
            nav_frame, text="◀ Previous", font=("Arial", 12),
            command=self.previous_page, padx=15, pady=8
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.page_label = tk.Label(
            nav_frame, text="Page 1 of 1", font=("Arial", 12)
        )
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        self.next_btn = tk.Button(
            nav_frame, text="Next ▶", font=("Arial", 12),
            command=self.next_page, padx=15, pady=8
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Font size controls (right)
        font_frame = tk.Frame(bottom_frame)
        font_frame.pack(side=tk.RIGHT)
        
        self.decrease_font_btn = tk.Button(
            font_frame, text="A-", font=("Arial", 14, "bold"),
            command=self.decrease_font, padx=12, pady=5
        )
        self.decrease_font_btn.pack(side=tk.LEFT, padx=5)
        
        self.font_size_label = tk.Label(
            font_frame, text=f"Size: {self.current_font_size}",
            font=("Arial", 12)
        )
        self.font_size_label.pack(side=tk.LEFT, padx=10)
        
        self.increase_font_btn = tk.Button(
            font_frame, text="A+", font=("Arial", 14, "bold"),
            command=self.increase_font, padx=12, pady=5
        )
        self.increase_font_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_settings_panel(self):
        """Create settings panel"""
        settings_frame = tk.Frame(self.main_frame)
        settings_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Line spacing control
        spacing_frame = tk.Frame(settings_frame)
        spacing_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(spacing_frame, text="Line Spacing:", font=("Arial", 11)).pack(side=tk.LEFT)
        
        self.spacing_down_btn = tk.Button(
            spacing_frame, text="-", font=("Arial", 12),
            command=self.decrease_spacing, padx=8
        )
        self.spacing_down_btn.pack(side=tk.LEFT, padx=5)
        
        self.spacing_label = tk.Label(
            spacing_frame, text=f"{self.current_line_spacing:.2f}",
            font=("Arial", 11)
        )
        self.spacing_label.pack(side=tk.LEFT, padx=5)
        
        self.spacing_up_btn = tk.Button(
            spacing_frame, text="+", font=("Arial", 12),
            command=self.increase_spacing, padx=8
        )
        self.spacing_up_btn.pack(side=tk.LEFT, padx=5)
        
        # Gesture status indicator
        self.gesture_frame = tk.Frame(settings_frame)
        self.gesture_frame.pack(side=tk.RIGHT, padx=20)
        
        self.gesture_status = tk.Label(
            self.gesture_frame,
            text="🎥 Gesture Control: OFF",
            font=("Arial", 11)
        )
        self.gesture_status.pack(side=tk.LEFT, padx=10)
        
        self.gesture_toggle_btn = tk.Button(
            self.gesture_frame, text="Enable Gestures",
            font=("Arial", 10), command=self.toggle_gestures,
            padx=10, pady=5
        )
        self.gesture_toggle_btn.pack(side=tk.LEFT)
        
        self.gestures_enabled = False
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts for accessibility"""
        self.root.bind("<Control-plus>", lambda e: self.increase_font())
        self.root.bind("<Control-equal>", lambda e: self.increase_font())
        self.root.bind("<Control-minus>", lambda e: self.decrease_font())
        self.root.bind("<Left>", lambda e: self.previous_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<space>", lambda e: self.tts_toggle())
        self.root.bind("<Escape>", lambda e: self.tts_stop())
    
    def _apply_theme(self, theme_key):
        """Apply a color theme to all components"""
        theme = config.THEMES[theme_key]
        self.current_theme = theme_key
        
        self.root.configure(bg=theme["bg"])
        self.main_frame.configure(bg=theme["bg"])
        
        self.text_display.configure(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["fg"],
            selectbackground=theme["highlight"]
        )
        
        for widget in self.main_frame.winfo_children():
            self._apply_theme_to_widget(widget, theme)
        
        for key, btn in self.theme_buttons.items():
            if key == theme_key:
                btn.configure(bg=theme["accent"], fg=theme["bg"])
            else:
                btn.configure(bg=theme["button_bg"], fg=theme["button_fg"])
    
    def _apply_theme_to_widget(self, widget, theme):
        """Recursively apply theme to a widget and its children"""
        widget_type = widget.winfo_class()
        
        try:
            if widget_type == "Frame":
                widget.configure(bg=theme["bg"])
            elif widget_type == "Label":
                widget.configure(bg=theme["bg"], fg=theme["fg"])
            elif widget_type == "Button":
                if widget not in self.theme_buttons.values():
                    widget.configure(bg=theme["button_bg"], fg=theme["button_fg"])
            elif widget_type == "Scale":
                widget.configure(bg=theme["bg"], fg=theme["fg"],
                               troughcolor=theme["button_bg"],
                               highlightbackground=theme["bg"])
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self._apply_theme_to_widget(child, theme)
    
    def _paginate_text(self):
        """Split text into pages"""
        self.pages = []
        text = self.full_text.strip()
        
        if not text:
            self.pages = ["No content to display."]
            return
        
        paragraphs = text.split('\n\n')
        current_page = ""
        
        for para in paragraphs:
            if len(current_page) + len(para) < self.chars_per_page:
                current_page += para + "\n\n"
            else:
                if current_page:
                    self.pages.append(current_page.strip())
                current_page = para + "\n\n"
        
        if current_page.strip():
            self.pages.append(current_page.strip())
        
        if not self.pages:
            self.pages = [text]
        
        self.current_page = 0
    
    def _display_current_page(self):
        """Display the current page in the text widget"""
        self.text_display.configure(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        
        if self.pages:
            self.text_display.insert(tk.END, self.pages[self.current_page])
        
        self.text_display.configure(state=tk.DISABLED)
        self._update_page_label()
        self._update_line_spacing()
    
    def _update_page_label(self):
        """Update the page indicator"""
        total = len(self.pages) if self.pages else 1
        self.page_label.configure(text=f"Page {self.current_page + 1} of {total}")
    
    def _update_line_spacing(self):
        """Update line spacing in text widget"""
        self.text_display.configure(spacing3=self.current_line_spacing * 10)
    
    # === TTS Methods ===
    
    def _on_tts_complete(self):
        """Callback when TTS finishes speaking"""
        self.root.after(0, self._on_tts_finished)
    
    def _on_tts_finished(self):
        """Handle TTS completion (runs on main thread)"""
        self._update_tts_buttons("stopped")
        self.tts_status.configure(text="Finished")
    
    def _update_tts_buttons(self, state):
        """Update TTS button states"""
        if state == "playing":
            self.play_btn.configure(state=tk.DISABLED)
            self.pause_btn.configure(state=tk.NORMAL, text="⏸ Pause")
            self.stop_btn.configure(state=tk.NORMAL)
            self.tts_status.configure(text="Playing...")
        elif state == "paused":
            self.play_btn.configure(state=tk.DISABLED)
            self.pause_btn.configure(state=tk.NORMAL, text="▶ Resume")
            self.stop_btn.configure(state=tk.NORMAL)
            self.tts_status.configure(text="Paused")
        else:  # stopped
            self.play_btn.configure(state=tk.NORMAL)
            self.pause_btn.configure(state=tk.DISABLED, text="⏸ Pause")
            self.stop_btn.configure(state=tk.DISABLED)
            self.tts_status.configure(text="Ready")
    
    def _on_speed_change(self, value):
        """Handle speed slider change"""
        rate = int(float(value))
        self.tts.set_rate(rate)
        self.speed_label.configure(text=f"{rate} wpm")
    
    def _on_voice_change(self, event):
        """Handle voice selection change"""
        idx = self.voice_dropdown.current()
        self.tts.set_voice(idx)
    
    def tts_play(self):
        """Start TTS playback"""
        if self.pages:
            text = self.pages[self.current_page]
            self.tts.speak(text)
            self._update_tts_buttons("playing")
    
    def tts_pause(self):
        """Pause or resume TTS playback"""
        state = self.tts.get_state()
        if state == "playing":
            self.tts.pause()
            self._update_tts_buttons("paused")
        elif state == "paused":
            self.tts.resume()
            self._update_tts_buttons("playing")
    
    def tts_stop(self):
        """Stop TTS playback"""
        self.tts.stop()
        self._update_tts_buttons("stopped")
    
    def tts_toggle(self):
        """Toggle TTS play/pause"""
        state = self.tts.get_state()
        if state == "stopped":
            self.tts_play()
        elif state == "playing":
            self.tts_pause()
        elif state == "paused":
            self.tts_pause()
    
    # === Public Methods ===
    
    def increase_font(self):
        """Increase font size"""
        if self.current_font_size < config.MAX_FONT_SIZE:
            self.current_font_size += config.FONT_SIZE_STEP
            self.text_display.configure(
                font=(config.DEFAULT_FONT_FAMILY, self.current_font_size)
            )
            self.font_size_label.configure(text=f"Size: {self.current_font_size}")
    
    def decrease_font(self):
        """Decrease font size"""
        if self.current_font_size > config.MIN_FONT_SIZE:
            self.current_font_size -= config.FONT_SIZE_STEP
            self.text_display.configure(
                font=(config.DEFAULT_FONT_FAMILY, self.current_font_size)
            )
            self.font_size_label.configure(text=f"Size: {self.current_font_size}")
    
    def increase_spacing(self):
        """Increase line spacing"""
        if self.current_line_spacing < config.MAX_LINE_SPACING:
            self.current_line_spacing += config.LINE_SPACING_STEP
            self._update_line_spacing()
            self.spacing_label.configure(text=f"{self.current_line_spacing:.2f}")
    
    def decrease_spacing(self):
        """Decrease line spacing"""
        if self.current_line_spacing > config.MIN_LINE_SPACING:
            self.current_line_spacing -= config.LINE_SPACING_STEP
            self._update_line_spacing()
            self.spacing_label.configure(text=f"{self.current_line_spacing:.2f}")
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < len(self.pages) - 1:
            self.tts_stop()
            self.current_page += 1
            self._display_current_page()
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.tts_stop()
            self.current_page -= 1
            self._display_current_page()
    
    def open_file(self):
        """Open a text or PDF file"""
        filetypes = [
            ("All supported files", "*.txt *.pdf"),
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        
        if filepath:
            try:
                # Check file extension
                if filepath.lower().endswith('.pdf'):
                    self._load_pdf(filepath)
                else:
                    self._load_text_file(filepath)
                
                self.current_file_path = filepath
                filename = filepath.split('/')[-1].split('\\')[-1]
                self.file_label.configure(text=f"Loaded: {filename}")
                self.tts_stop()
                self._paginate_text()
                self._display_current_page()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
    
    def _load_text_file(self, filepath):
        """Load a plain text file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.full_text = f.read()
    
    def _load_pdf(self, filepath):
        """Load and extract text from a PDF file"""
        try:
            # Open PDF
            pdf_document = fitz.open(filepath)
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
            
            pdf_document.close()
            
            # Combine all pages
            self.full_text = '\n\n'.join(text_parts)
            
            if not self.full_text.strip():
                raise Exception("PDF appears to be empty or contains only images")
            
        except Exception as e:
            raise Exception(f"Failed to read PDF: {e}")
    
    def toggle_gestures(self):
        """Toggle gesture control on/off"""
        self.gestures_enabled = not self.gestures_enabled
        
        if self.gestures_enabled:
            self.gesture_status.configure(text="🎥 Gesture Control: ON")
            self.gesture_toggle_btn.configure(text="Disable Gestures")
            self._start_gesture_control()
        else:
            self.gesture_status.configure(text="🎥 Gesture Control: OFF")
            self.gesture_toggle_btn.configure(text="Enable Gestures")
            self._stop_gesture_control()
        
        return self.gestures_enabled
    
    def _start_gesture_control(self):
        """Start the gesture control system"""
        if not self.gesture_controller.start_camera():
            messagebox.showerror("Error", "Could not open camera!")
            self.gestures_enabled = False
            self.gesture_status.configure(text="🎥 Gesture Control: OFF")
            self.gesture_toggle_btn.configure(text="Enable Gestures")
            return
        
        # Create gesture camera window
        self.gesture_window = tk.Toplevel(self.root)
        self.gesture_window.title("Gesture Camera")
        self.gesture_window.geometry("400x330")
        self.gesture_window.resizable(False, False)
        self.gesture_window.protocol("WM_DELETE_WINDOW", self._on_gesture_window_close)
        
        # Position window to the right of main window
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        self.gesture_window.geometry(f"+{main_x + 850}+{main_y}")
        
        # Camera feed label
        self.gesture_label = tk.Label(self.gesture_window)
        self.gesture_label.pack(padx=5, pady=5)
        
        # Gesture info label
        self.gesture_info = tk.Label(
            self.gesture_window, 
            text="Show gestures to control the reader",
            font=("Arial", 10)
        )
        self.gesture_info.pack(pady=5)
        
        # Start processing frames
        self._process_gesture_frame()
    
    def _stop_gesture_control(self):
        """Stop the gesture control system"""
        self.gesture_controller.stop_camera()
        
        if self.gesture_window:
            self.gesture_window.destroy()
            self.gesture_window = None
            self.gesture_label = None
    
    def _on_gesture_window_close(self):
        """Handle gesture window close button"""
        self.gestures_enabled = False
        self.gesture_status.configure(text="🎥 Gesture Control: OFF")
        self.gesture_toggle_btn.configure(text="Enable Gestures")
        self._stop_gesture_control()
    
    def _process_gesture_frame(self):
        """Process a frame from the gesture controller"""
        if not self.gestures_enabled or not self.gesture_window:
            return
        
        frame, gesture = self.gesture_controller.process_frame()
        
        if frame is not None:
            # Resize frame for display
            frame = cv2.resize(frame, (390, 280))
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            img = Image.fromarray(frame_rgb)
            
            # Convert to Tkinter PhotoImage
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.gesture_label.imgtk = imgtk
            self.gesture_label.configure(image=imgtk)
        
        # Schedule next frame
        if self.gestures_enabled and self.gesture_window:
            self.root.after(30, self._process_gesture_frame)
    
    def _on_gesture_detected(self, gesture, action):
        """Handle detected gesture from controller"""
        # Schedule action on main thread
        self.root.after(0, lambda: self._execute_gesture_action(gesture, action))
    
    def _execute_gesture_action(self, gesture, action):
        """Execute the action for a detected gesture"""
        if not self.gestures_enabled:
            return
        
        # Update gesture info display
        if self.gesture_info:
            self.gesture_info.configure(text=f"✓ {gesture} → {action}")
        
        # Map actions to methods
        actions = {
            "increase_font": self.increase_font,
            "decrease_font": self.decrease_font,
            "next_page": self.next_page,
            "previous_page": self.previous_page,
            "toggle_tts": self.tts_toggle,
            "stop_tts": self.tts_stop
        }
        
        if action in actions:
            actions[action]()
            print(f"[Gesture] {gesture} → {action}")
    
    def _on_closing(self):
        """Handle window close"""
        self._stop_gesture_control()
        self.gesture_controller.cleanup()
        self.tts.cleanup()
        self.root.destroy()