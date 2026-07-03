import cv2
import numpy as np
import time
from queue import Queue
from PyQt5.QtCore import QThread, pyqtSignal

class VideoWriterThread(QThread):
    finished = pyqtSignal(str)  # Emitted with the saved video path
    
    def __init__(self, output_path: str, width: int, height: int, fps: int = 10):
        super().__init__()
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_queue = Queue()
        self.running = False
        
    def add_frame(self, image_bytes: bytes, bytes_per_line: int):
        """Adds a raw BGR frame buffer to the queue."""
        if self.running:
            self.frame_queue.put((image_bytes, bytes_per_line))
        
    def stop(self):
        """Stops the recording run loop and flushes remaining frames."""
        self.running = False
        
    def run(self):
        self.running = True
        
        # Use AVI container with XVID codec (widely compatible on Windows)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (self.width, self.height))
        
        try:
            while self.running or not self.frame_queue.empty():
                if not self.frame_queue.empty():
                    image_bytes, bytes_per_line = self.frame_queue.get()
                    
                    # Convert raw bytes back to numpy array
                    raw_array = np.frombuffer(image_bytes, dtype=np.uint8)
                    
                    # Account for row padding / stride in QImage format
                    if bytes_per_line != self.width * 3:
                        # Extract the exact screen dimensions from the padded stride
                        frame = raw_array.reshape((self.height, bytes_per_line // 3, 3))[:, :self.width, :]
                    else:
                        frame = raw_array.reshape((self.height, self.width, 3))
                        
                    # Write frame to video stream
                    out.write(frame)
                    self.frame_queue.task_done()
                else:
                    # Avoid CPU spinning
                    time.sleep(0.01)
        except Exception as e:
            print(f"Error in VideoWriterThread execution: {str(e)}")
        finally:
            out.release()
            self.finished.emit(self.output_path)
