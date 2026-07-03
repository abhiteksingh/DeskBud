import sys
import os
import winsound
from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon 
from PyQt5.QtGui import QImage


from ui.widget import AetherWidget
from ui.panel import AetherPanel
from utils.sleep_detector import SleepDetector
from voice.listener import AetherVoiceListener
from brain.agent import AetherBrain

# Task executions
from tasks.open_app import launch_app
from tasks.file_finder import find_files, format_file_result, open_file_or_dir
from tasks.draft_text import copy_draft_to_clipboard
from tasks.reminder import set_reminder
from tasks.summarize_file import extract_text_from_file
from memory.history import add_task_log, init_db
from tasks.volume_control import change_volume
from tasks.brightness_control import adjust_brightness
from tasks.clipboard_manager import init_clipboard_db, log_clipboard_change, get_clipboard_history, format_clipboard_history
from tasks.close_window import close_active_window
from tasks.minimize_all import minimize_all_windows
from tasks.lock_screen import lock_workstation
from tasks.take_screenshot import capture_screenshot
from tasks.delete_file import search_file_for_deletion, delete_file_path
from tasks.screen_record import VideoWriterThread
from ui.dialogs import AetherConfirmDialog, AetherRecordingBar, AetherSpeechBubble


# Signal bridge for the sleep detector background thread
class SleepBridge(QObject):
    sleep_changed = pyqtSignal(bool)

# Background Worker to process AI commands without freezing the PyQt GUI
class CommandProcessorWorker(QThread):
    finished = pyqtSignal(dict)  # Emitted with response details

    def __init__(self, brain: AetherBrain, user_input: str):
        super().__init__()
        self.brain = brain
        self.user_input = user_input

    def run(self):
        result = {
            "task_type": "unknown",
            "query": self.user_input,
            "response": "",
            "status": "FAILED"
        }
        
        try:
            # 1. Ask the AI Brain to parse the query
            ai_data = self.brain.process_command(self.user_input)
            
            task = ai_data.get("task", "unknown")
            params = ai_data.get("params", {})
            aether_response = ai_data.get("response", "Greetings! I heard you!")
            
            result["task_type"] = task
            result["response"] = aether_response
            result["status"] = "SUCCESS"
            
            # 2. Execute the parsed task
            if task == "open_app":
                app_name = params.get("app_name", "")
                success, msg = launch_app(app_name)
                result["response"] = f"{aether_response}\n({msg})"
                result["status"] = "SUCCESS" if success else "FAILED"
                
            elif task == "find_file":
                file_query = params.get("file_query", "")
                matches = find_files(file_query)
                formatted_matches = format_file_result(matches)
                result["response"] = f"{aether_response}\n\n{formatted_matches}"
                result["status"] = "SUCCESS" if matches else "FAILED"
                
                # Auto-open if we found exactly one matching file
                if len(matches) == 1:
                    open_file_or_dir(matches[0]["path"])
                           
            elif task == "draft_text":
                draft_content = params.get("draft_content", "")
                if draft_content:
                    success, msg = copy_draft_to_clipboard(draft_content)
                    result["response"] = f"{aether_response}\n\n[Copied Draft]:\n{draft_content}"
                    result["status"] = "SUCCESS" if success else "FAILED"
                else:
                    result["response"] = "I couldn't write the draft content. Please describe it differently."
                    result["status"] = "FAILED"
                    
            elif task == "set_reminder":
                try:
                    minutes = float(params.get("reminder_minutes", 0))
                    message = params.get("reminder_message", "")
                    success, msg = set_reminder(minutes, message)
                    result["response"] = msg
                    result["status"] = "SUCCESS" if success else "FAILED"
                except Exception as e:
                    result["response"] = "I had trouble setting that reminder. Make sure you specify a time!"
                    result["status"] = "FAILED"
                    
            elif task == "summarize_file":
                file_path = params.get("file_path", "")
                success, extracted_text = extract_text_from_file(file_path)
                if success:
                    # Send text to LLM to summarize
                    summary = self.brain.generate_direct_response(
                        prompt=f"Summarize the file at '{file_path}'", 
                        context=extracted_text
                    )
                    result["response"] = f"Here is the summary of '{os.path.basename(file_path)}':\n\n{summary}"
                    result["status"] = "SUCCESS"
                else:
                    result["response"] = f"I couldn't read the file: {extracted_text}"
                    result["status"] = "FAILED"
                    
            elif task == "volume_control":
                action = params.get("action", "")
                success, msg = change_volume(action)
                result["response"] = msg
                result["status"] = "SUCCESS" if success else "FAILED"
                
            elif task == "brightness_control":
                action = params.get("action", "")
                value = params.get("value", None)
                if value is not None:
                    try:
                        value = int(value)
                    except ValueError:
                        value = None
                success, msg = adjust_brightness(action, value)
                result["response"] = msg
                result["status"] = "SUCCESS" if success else "FAILED"
                
            elif task == "clipboard_history":
                limit = params.get("limit", 5)
                try:
                    limit = int(limit)
                except ValueError:
                    limit = 5
                history = get_clipboard_history(limit)
                msg = format_clipboard_history(history)
                result["response"] = msg
                result["status"] = "SUCCESS"
                
            elif task == "close_window":
                success, msg = close_active_window()
                result["response"] = msg
                result["status"] = "SUCCESS" if success else "FAILED"
                
            elif task == "minimize_all":
                success, msg = minimize_all_windows()
                result["response"] = msg
                result["status"] = "SUCCESS" if success else "FAILED"
                
            elif task == "lock_screen":
                success, msg = lock_workstation()
                result["response"] = msg
                result["status"] = "SUCCESS" if success else "FAILED"
                
            elif task == "take_screenshot":
                # We will perform the actual grab on the main GUI thread in on_command_finished
                result["response"] = aether_response
                result["status"] = "SUCCESS"
                
            elif task == "delete_file":
                file_query = params.get("file_query", "")
                if not file_query:
                    result["response"] = "You did not specify a scroll name to delete."
                    result["status"] = "FAILED"
                else:
                    search_res = search_file_for_deletion(file_query)
                    if search_res["status"] == "FOUND":
                        result["status"] = "CONFIRM_DELETE"
                        result["file_path"] = search_res["file_path"]
                        result["file_name"] = search_res["file_name"]
                        result["response"] = f"I found the scroll. Banish confirmation required."
                    elif search_res["status"] == "NOT_FOUND":
                        result["response"] = f"I could not find any file matching '{file_query}' in my folders."
                        result["status"] = "FAILED"
                    else:  # AMBIGUOUS
                        lines = ["I found multiple scrolls. Please be more specific:"]
                        for i, m in enumerate(search_res["matches"][:3], 1):
                            lines.append(f"{i}. {m['name']} in {os.path.dirname(m['path'])}")
                        result["response"] = "\n".join(lines)
                        result["status"] = "FAILED"
                        
            elif task == "screen_record":
                action = params.get("action", "start")
                result["action"] = action
                result["response"] = aether_response
                result["status"] = "SUCCESS"
                

                
            else: # unknown / generic chat
                # The response already contains Aether's friendly response
                pass
                
        except Exception as e:
            result["response"] = f"Whoops, something went wrong processing that command: {str(e)}"
            result["status"] = "FAILED"
            
        # Log to local history database
        try:
            add_task_log(
                task_type=result["task_type"],
                query=result["query"],
                response=result["response"],
                status=result["status"]
            )
        except Exception as db_err:
            print(f"Error logging to history: {db_err}")
            
        self.finished.emit(result)

class AetherCoordinator(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        
        # Initialize Database
        init_db()
        init_clipboard_db()
        
        # Initialize AI Brain
        self.brain = AetherBrain()
        
        # Create UI Components
        self.widget = AetherWidget()
        self.panel = AetherPanel()
        self.speech_bubble = AetherSpeechBubble()
        
        # Connect UI Signals
        self.widget.clicked.connect(self.toggle_panel)
        self.widget.moved.connect(self.align_panel)
        self.panel.submitted.connect(self.process_command)
        self.panel.settings_clicked.connect(self.open_settings)
        
        # Setup Sleep Mode Detector
        self.sleep_bridge = SleepBridge()
        self.sleep_bridge.sleep_changed.connect(self.handle_sleep_changed)
        self.sleep_detector = SleepDetector(self.sleep_bridge.sleep_changed.emit)
        self.sleep_detector.start()
        
        # Setup Voice Listener Thread
        self.voice_listener = AetherVoiceListener()
        self.voice_listener.wake_word_detected.connect(self.on_voice_wake)
        self.voice_listener.command_transcribed.connect(self.process_command)
        self.voice_listener.status_changed.connect(self.on_voice_status_changed)
        self.voice_listener.start()
        
        # Show Mascot Sprite
        self.widget.show()
        self.align_panel()
        
        # Initial greeting timer
        QTimer.singleShot(1000, self.greet)
        
        # Clipboard Poll Timer (checks for changes every 2 seconds)
        self.clip_timer = QTimer(self)
        self.clip_timer.timeout.connect(log_clipboard_change)
        self.clip_timer.start(2000)
        
        # Screen Recording state
        self.recording = False
        self.record_thread = None
        self.record_timer = None
        self.recording_bar = None
        



    def greet(self):
        """Displays a greeting notification when Aether launches."""
        self.show_speech_bubble("Greetings, guardian! I have awakened. Say 'Wake up' or click me!", 5000)

    def toggle_panel(self):
        """Toggles the popup input panel visibility."""
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.align_panel()
            self.panel.show()
            self.panel.raise_()
            self.panel.input_field.setFocus()

    def open_settings(self):
        """Opens the API Keys Settings Dialog."""
        from ui.dialogs import AetherSettingsDialog
        dialog = AetherSettingsDialog(self.panel)
        if dialog.exec_() == AetherSettingsDialog.Accepted:
            # Reload clients in brain with the new keys
            self.brain.reload_clients()
            self.widget.tray_icon.showMessage(
                "Dragon Magic Saved",
                "Your API key runes have been safely inscribed. My magic is restored!",
                QSystemTrayIcon.Information,
                3000
            )
            self.show_speech_bubble("My magic has been restored, guardian! Ask me anything.", 5000)

    def align_panel(self):
        """Re-positions the panel near the widget."""
        self.panel.align_to_widget(self.widget.pos(), self.widget.size())
        if hasattr(self, "speech_bubble") and self.speech_bubble.isVisible():
            self.speech_bubble.align_to_widget(self.widget.pos(), self.widget.size())

    def handle_sleep_changed(self, is_sleeping: bool):
        """Handles fullscreen state shifts. Hides Aether to avoid overlay issues."""
        if is_sleeping:
            print("Fullscreen detected. Aether sleeping...")
            self.widget.change_state("sleep")
            self.panel.hide()
            self.speech_bubble.hide()
        else:
            print("Fullscreen exited. Aether waking up...")
            self.widget.change_state("idle")

    def on_voice_wake(self):
        """Triggered when user says 'Wake Up'."""
        try:
            # Play a premium native notification sound to alert the user
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass
            
        # Wake up sprite & show panel
        self.widget.change_state("active")
        self.panel.set_status("listening")
        self.show_speech_bubble("I am listening, guardian...", 4000)
        
        if not self.panel.isVisible():
            self.align_panel()
            self.panel.show()
            self.panel.raise_()

    def on_voice_status_changed(self, status: str):
        """Updates UI status labels matching voice listener threads."""
        if status == "Listening (active)...":
            self.panel.set_status("listening")
        elif status == "Idle":
            self.panel.set_status("idle")
            self.widget.change_state("idle")
        elif status == "Mic Unavailable":
            self.panel.set_status("idle")
            print("Warning: Microphone is not connected or accessible.")

    def process_command(self, text: str):
        """Executes a command by launching a background execution thread."""
        if not text.strip():
            return
            
        # Visual cues for thinking
        self.panel.set_status("thinking")
        self.widget.change_state("active")
        self.speech_bubble.hide()
        
        if not self.panel.isVisible():
            self.align_panel()
            self.panel.show()
            
        # Spawn worker thread
        self.worker = CommandProcessorWorker(self.brain, text)
        self.worker.finished.connect(self.on_command_finished)
        self.worker.start()

    def on_command_finished(self, result: dict):
        """Callback when AI execution finishes."""
        self.panel.set_status("idle")
        self.widget.change_state("idle")
        
        # 1. Handle confirmation required for file deletion
        if result["status"] == "CONFIRM_DELETE" and result["task_type"] == "delete_file":
            file_path = result.get("file_path", "")
            file_name = result.get("file_name", "")
            
            # Show custom styled confirmation dialog
            dialog = AetherConfirmDialog("Banish Scroll", file_name, file_path, self.panel)
            self.show_speech_bubble("A decision is required, guardian.", 4000)
            if dialog.exec_() == AetherConfirmDialog.Accepted:
                # User confirmed deletion
                success, msg = delete_file_path(file_path)
                add_task_log(
                    task_type="delete_file",
                    query=result["query"],
                    response=msg,
                    status="SUCCESS" if success else "FAILED"
                )
                self.show_speech_bubble(msg, 5000)
                self.widget.tray_icon.showMessage(
                    "Banishment Complete",
                    msg[:100],
                    QSystemTrayIcon.Information,
                    3000
                )
            else:
                # User cancelled deletion
                msg = "Banishment aborted. The scroll remains safe under my wings."
                add_task_log(
                    task_type="delete_file",
                    query=result["query"],
                    response=msg,
                    status="SUCCESS"
                )
                self.show_speech_bubble(msg, 5000)
            self.panel.reload_history()
            return

        # 2. Handle main-thread task execution for taking screenshot
        if result["status"] == "SUCCESS" and result["task_type"] == "take_screenshot":
            success, msg = capture_screenshot()
            add_task_log(
                task_type="take_screenshot",
                query=result["query"],
                response=msg,
                status="SUCCESS" if success else "FAILED"
            )
            self.panel.reload_history()
            self.show_speech_bubble(msg, 5000)
            self.widget.tray_icon.showMessage(
                "Screenshot Captured",
                msg[:100],
                QSystemTrayIcon.Information,
                3000
            )
            return
            
        # 3. Handle screen recording commands
        if result["status"] == "SUCCESS" and result["task_type"] == "screen_record":
            action = result.get("action", "start")
            if action == "start":
                self.start_screen_recording(result["query"])
                self.show_speech_bubble("Recording desktop! Click STOP when finished.", 5000)
            else:
                self.stop_screen_recording()
            return


        # Display the result dialog/response inside the panel
        self.panel.reload_history()
        
        # Show response in speech bubble
        resp = result.get("response", "")
        if resp:
            self.show_speech_bubble(resp, 6000)
        
        # Optionally flash tray balloon message for background reminders or execution confirmation
        if result["status"] == "SUCCESS" and result["task_type"] != "unknown":
            self.widget.tray_icon.showMessage(
                "Task Completed",
                result["response"][:100] + ("..." if len(result["response"]) > 100 else ""),
                QSystemTrayIcon.Information,
                3000
            )

    # --- Screen Recording Helpers ---
    def start_screen_recording(self, query: str):
        if self.recording:
            self.widget.tray_icon.showMessage("Screen Recording", "I am already capturing the screen, guardian!", QSystemTrayIcon.Warning, 3000)
            return
            
        import time
        from pathlib import Path
        dest_dir = Path.home() / "Downloads"
        if not dest_dir.exists():
            dest_dir = Path.home() / "Videos"
        if not dest_dir.exists():
            dest_dir = Path.home()
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.avi"
        output_path = str(dest_dir / filename)
        
        screen = self.app.primaryScreen()
        if not screen:
            self.widget.tray_icon.showMessage("Screen Recording Failed", "No viewport screens found.", QSystemTrayIcon.Critical, 3000)
            return
            
        pixmap = screen.grabWindow(0)
        width = pixmap.width()
        height = pixmap.height()
        
        self.recording_query = query
        self.record_thread = VideoWriterThread(output_path, width, height, fps=10)
        self.record_thread.finished.connect(self.on_recording_finished)
        self.record_thread.start()
        
        self.recording_bar = AetherRecordingBar()
        self.recording_bar.stop_clicked.connect(self.stop_screen_recording)
        self.recording_bar.show()
        
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.capture_record_frame)
        self.record_timer.start(100) # Grab frame every 100ms (10fps)
        
        self.recording = True
        self.panel.set_status("working")
        self.panel.status_text.setText("RECORDING...")
        
    def capture_record_frame(self):
        if not self.recording or not self.record_thread or not self.record_thread.isRunning():
            return
            
        screen = self.app.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0)
            img = pixmap.toImage().convertToFormat(QImage.Format_BGR888)
            ptr = img.bits()
            ptr.setsize(img.byteCount())
            raw_bytes = bytes(ptr)
            self.record_thread.add_frame(raw_bytes, img.bytesPerLine())
            
    def stop_screen_recording(self):
        if not self.recording:
            return
            
        if self.record_timer:
            self.record_timer.stop()
            self.record_timer = None
            
        if self.record_thread:
            self.record_thread.stop()
            
        if self.recording_bar:
            self.recording_bar.hide()
            self.recording_bar = None
            
        self.recording = False
        self.panel.set_status("idle")
        
    def on_recording_finished(self, output_path: str):
        msg = f"Screen capture complete! I have recorded your desktop and saved the scroll to {os.path.basename(output_path)}."
        add_task_log(
            task_type="screen_record",
            query=getattr(self, "recording_query", "screen record"),
            response=msg,
            status="SUCCESS" if output_path else "FAILED"
        )
        self.panel.reload_history()
        self.show_speech_bubble(msg, 6000)
        
        if output_path and os.path.exists(output_path):
            self.widget.tray_icon.showMessage(
                "Recording Saved",
                f"Video saved in Downloads. Click to play!",
                QSystemTrayIcon.Information,
                3000
            )
            # Auto-play using standard media player
            try:
                os.startfile(output_path)
            except Exception:
                pass
                
        self.record_thread = None

    def show_speech_bubble(self, text: str, duration_ms=4500):
        """Displays a speech bubble above Aether's head with the given text."""
        if len(text) > 160:
            text = text[:157] + "..."
        if hasattr(self, "speech_bubble"):
            self.speech_bubble.show_text(text, self.widget.pos(), self.widget.size(), duration_ms)

    def clean_up(self):
        """Cleans up running threads on exit."""
        self.sleep_detector.stop()
        self.voice_listener.stop()
        
        # Stop screen recording if active
        if self.recording:
            self.stop_screen_recording()
            if self.record_thread:
                self.record_thread.wait()
                
        if hasattr(self, "speech_bubble"):
            self.speech_bubble.close()

# System lock socket to enforce single instance
lock_socket = None

def main():
    import socket
    global lock_socket
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', 48329))
    except socket.error:
        print("Another instance of Aether is already running. Exiting...")
        sys.exit(0)

    app = QApplication(sys.argv)
    
    # Avoid closing the app when windows are closed (since widget can hide/show)
    app.setQuitOnLastWindowClosed(False)
    
    coordinator = AetherCoordinator(app)
    
    # Connect application exit signals to clean up background threads
    app.aboutToQuit.connect(coordinator.clean_up)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
