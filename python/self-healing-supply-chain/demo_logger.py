import json
import logging
import sys
from datetime import datetime

class DemoLogger:
    # Colors defined as class attributes so they can be accessed via logger.GREEN
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, filename="demo_audit.log"):
        self.filename = filename
        # Clear previous log
        with open(self.filename, 'w') as f:
            f.write(f"--- SUPPLY CHAIN DEMO START: {datetime.now()} ---\n")

    def _write_file(self, text):
        with open(self.filename, 'a') as f:
            f.write(text + "\n")

    def step(self, step_name):
        msg = f"\n{'='*60}\nSTEP: {step_name}\n{'='*60}"
        print(f"{self.BOLD}{msg}{self.RESET}")
        self._write_file(msg)

    def agent(self, message):
        """Logs internal Agent reasoning"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{self.CYAN}🤖 [AGENT]   {message}{self.RESET}")
        self._write_file(f"[{timestamp}] [AGENT] {message}")

    def ucp(self, message, payload=None):
        """Logs UCP Protocol interactions (Discovery/Checkout)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{self.MAGENTA}🌐 [UCP/NET] {message}{self.RESET}")
        self._write_file(f"[{timestamp}] [UCP] {message}")
        if payload:
            if hasattr(payload, 'model_dump'):
                payload = payload.model_dump(mode='json', exclude_none=True)
            
            json_str = json.dumps(payload, indent=2)
            print(f"{self.MAGENTA}{json_str}{self.RESET}")
            self._write_file(json_str)

    def ap2(self, message, payload=None):
        """Logs AP2 Governance and Mandates"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{self.YELLOW}🔐 [AP2/GOV] {message}{self.RESET}")
        self._write_file(f"[{timestamp}] [AP2] {message}")
        if payload:
            if hasattr(payload, 'model_dump'):
                payload = payload.model_dump(mode='json', exclude_none=True)
            json_str = json.dumps(payload, indent=2)
            print(f"{self.YELLOW}{json_str}{self.RESET}")
            self._write_file(json_str)

    def supplier(self, message):
        """Logs Supplier-side actions"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{self.GREEN}🏭 [SUPPLIER] {message}{self.RESET}")
        self._write_file(f"[{timestamp}] [SUPPLIER] {message}")

    def error(self, message):
        print(f"{self.RED}❌ [ERROR]    {message}{self.RESET}")
        self._write_file(f"[ERROR] {message}")

logger = DemoLogger()