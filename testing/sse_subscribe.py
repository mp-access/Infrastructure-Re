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


# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m' 
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    ORANGE = '\033[33m'
    RESET = '\033[0m'


# Constants
EVENT_COUNTING_PHASE_DURATION = 10  # seconds to count for an event type
HEARTBEAT_INTERVAL = 15  # seconds to send heartbeat

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
        
    def get_token(self):
        """Get authentication token for the student"""
        try:
            # self.message_queue.put(("debug", self.username, f"Attempting to get token for {self.username}"))
            self.token = get_user_token(self.username, self.password, self.backend_client_id)
            
            # self.message_queue.put(("debug", self.username, f"Successfully got token"))
            return True
        except Exception as e:
            self.message_queue.put(("error", self.username, f"Failed to get token: {e}"))
            return False
          
    def send_heartbeat(self):
        """Send heartbeat"""
        while self.running:
            time.sleep(HEARTBEAT_INTERVAL)
            try:
                if self.token and self.emitter_id:
                    headers = {"Authorization": f"Bearer {self.token}"}
                    heartbeat_url = f"{self.backend_url}/courses/{self.course_slug}/heartbeat/{self.emitter_id}"
                    response = requests.put(heartbeat_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        self.message_queue.put(("heartbeat_success", self.username, ""))
                    else:
                        self.message_queue.put(("heartbeat_error", self.username, f"Status: {response.status_code}"))
                elif self.token and not self.emitter_id:
                    self.message_queue.put(("heartbeat_error", self.username, "No emitter ID available"))
                        
            except Exception as e:
                self.message_queue.put(("heartbeat_error", self.username, str(e)))
            
    def subscribe_to_sse(self):
        """Subscribe to SSE and handle incoming events (no reconnection)"""
        if True:
            if not self.get_token():
                self.message_queue.put(("error", self.username, "Failed to get token, stopping"))
                return
              
            try:
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                }
                
                sse_url = f"{self.backend_url}/courses/{self.course_slug}/subscribe"
                connection_start = time.time()  # Track this connection attempt
                
                # self.message_queue.put(("debug", self.username, f"Connecting to SSE: {sse_url}"))
                self.message_queue.put(("process_started", self.username, "SSE subscription started"))
                
                # Subscribe to SSE stream (no timeout for indefinite connection)
                headers.update({
                    "User-Agent": f"SSE-Client-{self.username}",
                    "X-Client-ID": self.username
                })
                response = requests.get(sse_url, headers=headers, stream=True)
                # self.message_queue.put(("debug", self.username, f"SSE response status: {response.status_code}"))
                # self.message_queue.put(("debug", self.username, f"Response headers: {dict(response.headers)}"))
                response.raise_for_status()
                # self.message_queue.put(("debug", self.username, "SSE connection established successfully"))
                                
                # Start heartbeat thread to keep connection alive
                # heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
                # heartbeat_thread.start()
                
                # Track connection health
                last_activity = time.time()
                
                for line in response.iter_lines(decode_unicode=True):
                    if not self.running:
                        # self.message_queue.put(("debug", self.username, "Process stopped, breaking from SSE loop"))
                        break
                        
                    if line:
                        last_activity = time.time()  # Update activity timestamp
                        line = line.strip()
                        # print(line)
                        self.message_queue.put(("new_event", self.username, line))
                        if line.startswith("event:"):
                            event_name = line[6:].strip()
                            self.message_queue.put(("sse_event", self.username, event_name))
                        elif line.startswith("data:"):
                            data = line[5:].strip()
                            # Check if this is the emitter ID in the data
                            if not self.emitter_id:
                                self.emitter_id = data
                                self.message_queue.put(("emitter_id", self.username, f"Emitter ID: {self.emitter_id}"))
                                
                                # Start heartbeat when received emitter ID
                                heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
                                heartbeat_thread.start()
                                # try:
                                #     emitter_data = data
                                #     if "emitter_id" in emitter_data:
                                #         self.emitter_id = emitter_data["emitter_id"]
                                #         self.message_queue.put(("emitter_id", self.username, f"Emitter ID: {self.emitter_id}"))
                                # except json.JSONDecodeError:
                                #     pass
                    else:
                        # Empty line - check if connection is still alive
                        current_time = time.time()
                        if current_time - last_activity > 60:  # 60 seconds without activity
                            # self.message_queue.put(("debug", self.username, "SSE connection inactive for 60 seconds, but still connected"))
                            last_activity = current_time
                
                # If we reach here, the stream ended normally
                duration = time.time() - connection_start
                # Check if this was a server-initiated close
                response_info = ""
                self.message_queue.put(("debug", self.username, f"Disconnect Response: {response}"))
                # if hasattr(response, 'status_code'):
                #     response_info = f" (HTTP {response.status_code})"
                # if hasattr(response, 'reason'):
                #     response_info += f" - {response.reason}"
                
                self.message_queue.put(("sse_disconnect", self.username, f"SSE stream ended normally after {duration:.1f}s{response_info}, stopping (reconnect disabled)"))
                            
            # except requests.exceptions.RequestException as e:  # Reconnect logic commented out
            #     duration = time.time() - connection_start
            #     self.message_queue.put(("sse_disconnect", self.username, f"SSE connection error after {duration:.1f}s: {e}, will attempt to reconnect"))
            except Exception as e:
                duration = time.time() - connection_start
                self.message_queue.put(("sse_disconnect", self.username, f"Unexpected error after {duration:.1f}s: {e}, will attempt to reconnect"))
                            
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
        self.event_timers = {}
        self.event_counting_phase = {}
        self.completed_events = []
        
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
    
    def _end_event_counting_phase(self, event_type):
        """Called to end the counting phase for an event type"""
        final_count = self.event_counts[event_type]
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.BLUE}[{timestamp}] EVENT COUNTING COMPLETE: {event_type} - Final count: {final_count}{Colors.RESET}")
        
        # Add record to completed events array
        self.completed_events.append((timestamp ,event_type, final_count))
        
        # Delete this event type from history
        if event_type in self.event_counts:
            del self.event_counts[event_type]
        if event_type in self.event_counting_phase:
            del self.event_counting_phase[event_type]
        if event_type in self.event_timers:
            del self.event_timers[event_type]
    
    def handle_message(self, message_type, username, data):
        """Handle messages from subprocesses"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if message_type == "sse_event":
            # print(f"[{timestamp}] SSE EVENT: {data}")
            event_type = data
            
            # Check if this is the first time we see this event type
            if event_type not in self.event_counting_phase:
                # First occurrence - start the 30-second counting phase
                self.event_counting_phase[event_type] = True
                self.event_counts[event_type] = 1
                
                print(f"{Colors.CYAN}[{timestamp}] NEW SSE EVENT DETECTED: {event_type} - Starting {EVENT_COUNTING_PHASE_DURATION}-second counting phase{Colors.RESET}")
                
                # Start timer to end the counting phase after 15 seconds
                timer = threading.Timer(30 if event_type == "emitter-id" else EVENT_COUNTING_PHASE_DURATION, self._end_event_counting_phase, args=[event_type])
                self.event_timers[event_type] = timer
                timer.start()
            else:
                # Event already seen - increment count silently during counting phase
                self.event_counts[event_type] += 1
                
                # Only print if we're not in counting phase anymore
                if not self.event_counting_phase.get(event_type, False):
                    print(f"{Colors.CYAN}[{timestamp}] SSE EVENT: {username} -> {event_type} (total: {self.event_counts[event_type]}){Colors.RESET}")
        elif message_type == "process_started":
            print(f"{Colors.GREEN}[{timestamp}] PROCESS STARTED: {username}{Colors.RESET}")
        elif message_type == "process_ended":
            print(f"{Colors.GREEN}[{timestamp}] PROCESS ENDED: {username}{Colors.RESET}")
        elif message_type == "emitter_id":
            # print(f"{Colors.MAGENTA}[{timestamp}] EMITTER ID: {username} - {data}{Colors.RESET}")
            pass
        elif message_type == "heartbeat_success":
            # print(f"[{timestamp}] HEARTBEAT OK: {username}")
            pass
        elif message_type == "heartbeat_error":
            # print(f"{Colors.RED}[{timestamp}] HEARTBEAT ERROR: {username} - {data}{Colors.RESET}")
            pass
        elif message_type == "sse_disconnect":
            print(f"{Colors.YELLOW}[{timestamp}] SSE DISCONNECT: {username} - {data}{Colors.RESET}")
        elif message_type == "sse_error":
            print(f"{Colors.RED}[{timestamp}] SSE ERROR: {username} - {data}{Colors.RESET}")
        elif message_type == "error":
            print(f"{Colors.RED}[{timestamp}] ERROR: {username} - {data}{Colors.RESET}")
        elif message_type == "debug":
            # Temporarily re-enable debug for connection diagnostics
            if ("SSE response status" in data or "Response headers" in data or 
                "connection" in data.lower() or "Token expires" in data):
                print(f"{Colors.GRAY}[{timestamp}] DEBUG: {username} - {data}{Colors.RESET}")
            # pass
    
    def shutdown_all_processes(self):
        """Terminate all subprocesses and cleanup timers"""
        print("Shutting down all processes...")
        
        # Cancel any active event timers
        for timer in self.event_timers.values():
            if timer.is_alive():
                timer.cancel()
        self.event_timers.clear()
        
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
        print(f"{Colors.GREEN}Completed events:{Colors.RESET}")
        for timestamp, event_type, count in self.completed_events:
            print(f"{Colors.YELLOW}  [{timestamp}] {Colors.BLUE}{event_type}: {count} {Colors.RESET}")
        
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
            self.shutdown_all_processes()
            self.print_summary()
            print("--- SSE Parent Process Complete ---")


if __name__ == "__main__":
    parent = SSEParentProcess()
    parent.run()
