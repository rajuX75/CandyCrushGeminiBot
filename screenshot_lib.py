import time
import yaml
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sys
import traceback
from PIL import ImageGrab
import tkinter as tk
from typing import Dict, Tuple, Optional
import threading
from concurrent.futures import ThreadPoolExecutor

class ScreenshotConfig:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize screenshot configuration from YAML file."""
        self.config_path = config_path
        self.interval_ms: int = 1000
        self.save_dir: str = "screenshots"
        self.region: Optional[Tuple[int, int, int, int]] = None
        self.file_prefix: str = "screenshot"
        self.retention_minutes: int = 1
        self.selection_mode: str = "manual"
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from YAML file with error handling."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            self.interval_ms = config.get('interval_ms', 1000)
            self.save_dir = config.get('save_dir', 'screenshots')
            self.region = tuple(config.get('region', []))
            self.file_prefix = config.get('file_prefix', 'screenshot')
            self.retention_minutes = config.get('retention_minutes', 1)
            self.selection_mode = config.get('selection_mode', 'manual')
            
        except FileNotFoundError:
            logging.warning(f"Config file not found at {self.config_path}. Using default values.")
            self._create_default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error loading config: {e}")
            raise

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            'interval_ms': 1000,
            'save_dir': 'screenshots',
            'region': [],
            'file_prefix': 'screenshot',
            'retention_minutes': 1,
            'selection_mode': 'manual'
        }
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logging.info(f"Created default config file at {self.config_path}")
        except Exception as e:
            logging.error(f"Error creating default config: {e}")
            raise

class RegionSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-fullscreen', True)
        self.root.configure(background='grey')
        
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.region = None

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.root.bind('<Escape>', lambda e: self.root.quit())

    def on_click(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, outline='red'
        )

    def on_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        self.region = (x1, y1, x2, y2)
        self.root.quit()

    def get_region(self):
        self.root.mainloop()
        self.root.destroy()
        return self.region

class ScreenshotTool:
    def __init__(self, config: ScreenshotConfig):
        """Initialize the screenshot tool with configuration."""
        self.config = config
        self.setup_logging()
        self.setup_directory()
        self.running = False

    def setup_logging(self) -> None:
        """Configure logging with file and console output."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('screenshot_tool.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def setup_directory(self) -> None:
        """Create screenshot directory if it doesn't exist."""
        try:
            Path(self.config.save_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating directory: {e}")
            raise

    def select_region(self) -> None:
        """Allow user to select a region for screenshots."""
        if not self.config.region:
            try:
                print("\nSelect the area for screenshots...")
                print("1. Click and drag to select the area")
                print("2. Release to confirm selection")
                print("3. Press Escape to cancel\n")
                
                selector = RegionSelector()
                self.config.region = selector.get_region()
                if self.config.region:
                    logging.info(f"Selected region: {self.config.region}")
                else:
                    logging.error("No region selected")
                    raise ValueError("No region selected")
            except Exception as e:
                logging.error(f"Error selecting region: {e}")
                raise

    def take_screenshot(self) -> None:
        """Take a screenshot of the selected region."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.file_prefix}_{timestamp}.png"
            filepath = Path(self.config.save_dir) / filename

            screenshot = ImageGrab.grab(bbox=self.config.region)
            screenshot.save(filepath)
            logging.info(f"Screenshot saved: {filepath}")
            
        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")
            logging.debug(traceback.format_exc())

    def start(self) -> None:
        """Start taking screenshots at configured interval."""
        try:
            self.running = True
            self.select_region()
            
            print("\nScreenshot capture started!")
            print("Press Ctrl+C to stop...\n")
            
            while self.running:
                self.take_screenshot()
                time.sleep(self.config.interval_ms / 1000)
                
        except KeyboardInterrupt:
            self.running = False
            logging.info("Screenshot capture stopped by user")
            print("\nScreenshot capture stopped!")
        except Exception as e:
            logging.error(f"Fatal error in screenshot capture: {e}")
            logging.debug(traceback.format_exc())
            raise

class ImageCleaner:
    def __init__(self, config: ScreenshotConfig):
        self.config = config
        self.running = False
        self.cleanup_thread = None

    def start(self):
        """Start the cleanup thread."""
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

    def stop(self):
        """Stop the cleanup thread."""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()

    def _cleanup_loop(self):
        """Continuously clean up old screenshots."""
        while self.running:
            try:
                self.cleanup_old_images()
            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")
            time.sleep(10)  # Check every 10 seconds

    def cleanup_old_images(self):
        """Delete images older than retention_minutes."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=self.config.retention_minutes)
            screenshot_dir = Path(self.config.save_dir)

            for image_path in screenshot_dir.glob(f"{self.config.file_prefix}_*.png"):
                try:
                    timestamp_str = image_path.stem.split('_', 1)[1]
                    image_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if image_time < cutoff_time:
                        image_path.unlink()
                        logging.info(f"Deleted old screenshot: {image_path}")
                except (ValueError, OSError) as e:
                    logging.error(f"Error processing file {image_path}: {e}")

        except Exception as e:
            logging.error(f"Error cleaning up old images: {e}")
            raise

class ScreenshotManager:
    def __init__(self, config: ScreenshotConfig):
        self.config = config
        self.screenshot_tool = ScreenshotTool(config)
        self.image_cleaner = ImageCleaner(config)
        self.running = False

    def start(self):
        """Start both screenshot capture and cleanup processes."""
        try:
            print("Starting Screenshot Manager...")
            # Start the image cleaner
            self.image_cleaner.start()
            logging.info("Image cleaner started")
            
            # Start screenshot capture
            self.screenshot_tool.start()
            
        except Exception as e:
            logging.error(f"Error in screenshot manager: {e}")
            raise
        finally:
            # Ensure cleanup stops when screenshots stop
            self.image_cleaner.stop()
            logging.info("Image cleaner stopped")