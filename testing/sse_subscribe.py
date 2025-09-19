import json
import multiprocessing
import os
import signal
import threading
import time
from collections import defaultdict
from datetime import datetime
from queue import Empty

import requests
from config import (API_KEY, BACKEND_CLIENT_ID, BACKEND_URL, COURSE_SLUG,
                    STUDENT_CREDENTIALS_FILE, TASK_FILE_ID)
from keycloak_utils import get_user_token


class SSEStudentProcess:
    def __init__(self, student_info, backend_url, course_slug, backend_client_id, message_queue):
        self.student_info = student_info
        self.backend_url = backend_url
        self.course_slug = course_slug
        self.backend_client_id = backend_client_id
        self.message_queue = message_queue
        self.username = student_info["username"]
        self.password = student_info["password"]
        self.running = True
        self.token = None
        self.emitter_id = None
        self.start_time = time.time()
        self.min_runtime = 300  # 5 minutes in seconds
        
    def get_token(self):
        """Get authentication token for the student"""
        try:
            self.token = get_user_token(self.username, self.password, self.backend_client_id)
            return True
        except Exception as e:
            self.message_queue.put(("error", self.username, f"Failed to get token: {e}"))
            return False
            
    def send_heartbeat(self):
        """Send heartbeat every 30 seconds"""
        while self.running:
            # try:
            #     if self.token and self.emitter_id:
            #         headers = {"Authorization": f"Bearer {self.token}"}
            #         heartbeat_url = f"{self.backend_url}/courses/{self.course_slug}/heartbeat/{self.emitter_id}"
            #         response = requests.post(heartbeat_url, headers=headers, timeout=10)
            #         
            #         if response.status_code == 200:
            #             self.message_queue.put(("heartbeat_success", self.username, ""))
            #         else:
            #             self.message_queue.put(("heartbeat_error", self.username, f"Status: {response.status_code}"))
            #     elif self.token and not self.emitter_id:
            #         self.message_queue.put(("heartbeat_error", self.username, "No emitter ID available"))
            #             
            # except Exception as e:
            #     self.message_queue.put(("heartbeat_error", self.username, str(e)))
        # for i in range(10):
            time.sleep(30)
    
    def subscribe_to_sse(self):
        """Subscribe to SSE and handle incoming events"""
        if not self.get_token():
            return
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            sse_url = f"{self.backend_url}/courses/{self.course_slug}/subscribe"
            
            self.message_queue.put(("process_started", self.username, "SSE subscription started"))
            
            # Subscribe to SSE stream
            response = requests.get(sse_url, headers=headers, stream=True, timeout=(300, 600))
            response.raise_for_status()
            
            # Extract emitter ID from response headers if available
            if 'X-Emitter-Id' in response.headers:
                self.emitter_id = response.headers['X-Emitter-Id']
                self.message_queue.put(("emitter_id", self.username, f"Emitter ID: {self.emitter_id}"))
            
            # Start heartbeat thread after getting emitter ID
            heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
            heartbeat_thread.start()
            
            for line in response.iter_lines(decode_unicode=True):
                if not self.running:
                    break
                    
                if line:
                    line = line.strip()
                    if line.startswith("event:"):
                        event_name = line[6:].strip()
                        self.message_queue.put(("sse_event", self.username, event_name))
                    elif line.startswith("data:"):
                        data = line[5:].strip()
                        # Check if this is the emitter ID in the data
                        if not self.emitter_id and data.startswith('{"emitter_id":'):
                            try:
                                emitter_data = json.loads(data)
                                if "emitter_id" in emitter_data:
                                    self.emitter_id = emitter_data["emitter_id"]
                                    self.message_queue.put(("emitter_id", self.username, f"Emitter ID: {self.emitter_id}"))
                            except json.JSONDecodeError:
                                pass
                        
        except requests.exceptions.RequestException as e:
            self.message_queue.put(("sse_error", self.username, f"SSE connection error: {e}"))
        except Exception as e:
            self.message_queue.put(("error", self.username, f"Unexpected error: {e}"))
        finally:
            self.running = False
            self.message_queue.put(("process_ended", self.username, "SSE subscription ended"))

    def run(self):
        """Main process execution"""
        self.subscribe_to_sse()


def student_process_worker(student_info, backend_url, course_slug, backend_client_id, message_queue):
    """Worker function for student subprocess"""
    process = SSEStudentProcess(student_info, backend_url, course_slug, backend_client_id, message_queue)
    
    def signal_handler(signum, frame):
        process.running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    process.run()


class SSEParentProcess:
    def __init__(self):
        self.processes = {}
        self.event_counts = defaultdict(int)
        self.message_queue = multiprocessing.Queue()
        self.running = True
        
    def setup_signal_handlers(self):
        """Setup signal handlers for clean shutdown"""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}. Shutting down gracefully...")
            self.running = False
            self.shutdown_all_processes()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def create_student_processes(self, student_credentials):
        """Create subprocess for each student"""
        print(f"Creating {len(student_credentials)} student processes...")
        
        for student_info in student_credentials:
            username = student_info["username"]
            
            process = multiprocessing.Process(
                target=student_process_worker,
                args=(student_info, BACKEND_URL, COURSE_SLUG, BACKEND_CLIENT_ID, self.message_queue)
            )
            
            process.start()
            self.processes[username] = {
                "process": process,
                "status": "running",
                "start_time": datetime.now()
            }
            
        print(f"All {len(student_credentials)} processes created and started")
    
    def monitor_processes(self):
        """Monitor subprocess health and handle messages"""
        print("Starting process monitoring...")
        
        while self.running:
            # Check for messages from subprocesses
            try:
                message_type, username, data = self.message_queue.get(timeout=1)
                self.handle_message(message_type, username, data)
            except Empty:
                pass
            except Exception as e:
                print(f"Error reading from message queue: {e}")
            
            # Check process health
            dead_processes = []
            for username, proc_info in self.processes.items():
                process = proc_info["process"]
                if not process.is_alive() and proc_info["status"] == "running":
                    proc_info["status"] = "dead"
                    proc_info["end_time"] = datetime.now()
                    dead_processes.append(username)
                    
            for username in dead_processes:
                print(f"PROCESS DIED: {username} at {datetime.now()}")
                
        print("Process monitoring stopped")
    
    def handle_message(self, message_type, username, data):
        """Handle messages from subprocesses"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if message_type == "sse_event":
            self.event_counts[data] += 1
            print(f"[{timestamp}] SSE EVENT: {username} -> {data} (total: {self.event_counts[data]})")
        elif message_type == "process_started":
            print(f"[{timestamp}] PROCESS STARTED: {username}")
        elif message_type == "process_ended":
            print(f"[{timestamp}] PROCESS ENDED: {username}")
        elif message_type == "emitter_id":
            print(f"[{timestamp}] EMITTER ID: {username} - {data}")
        elif message_type == "heartbeat_success":
            print(f"[{timestamp}] HEARTBEAT OK: {username}")
        elif message_type == "heartbeat_error":
            print(f"[{timestamp}] HEARTBEAT ERROR: {username} - {data}")
        elif message_type == "sse_error":
            print(f"[{timestamp}] SSE ERROR: {username} - {data}")
        elif message_type == "error":
            print(f"[{timestamp}] ERROR: {username} - {data}")
    
    def shutdown_all_processes(self):
        """Terminate all subprocesses"""
        print("Shutting down all processes...")
        
        for username, proc_info in self.processes.items():
            process = proc_info["process"]
            if process.is_alive():
                print(f"Terminating process for {username}")
                process.terminate()
                
        # Give processes time to terminate gracefully
        time.sleep(2)
        
        # Force kill any remaining processes
        for username, proc_info in self.processes.items():
            process = proc_info["process"]
            if process.is_alive():
                print(f"Force killing process for {username}")
                process.kill()
                
        # Wait for all processes to finish
        for username, proc_info in self.processes.items():
            process = proc_info["process"]
            process.join(timeout=60)
            
        print("All processes terminated")
    
    def print_summary(self):
        """Print final summary"""
        print("\n--- FINAL SUMMARY ---")
        print(f"Event counts: {dict(self.event_counts)}")
        
        alive_count = sum(1 for proc_info in self.processes.values() if proc_info["status"] == "running")
        dead_count = len(self.processes) - alive_count
        print(f"Processes: {alive_count} alive, {dead_count} dead")
    
    def run(self):
        """Main parent process execution"""
        self.setup_signal_handlers()
        
        print("--- Starting SSE Parent Process ---")
        
        try:
            if not os.path.exists(STUDENT_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Student credentials file '{STUDENT_CREDENTIALS_FILE}' not found. "
                    "Please run register_students.py first."
                )
                
            with open(STUDENT_CREDENTIALS_FILE, 'r') as f:
                student_credentials = json.load(f)
                
            print(f"Loaded {len(student_credentials)} student credentials")
            
            self.create_student_processes(student_credentials)
            self.monitor_processes()
            
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if not self.running:  # Only shutdown if not already shutting down
                self.shutdown_all_processes()
            self.print_summary()
            print("--- SSE Parent Process Complete ---")


if __name__ == "__main__":
    parent = SSEParentProcess()
    parent.run()
