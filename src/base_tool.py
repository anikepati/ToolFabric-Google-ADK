from abc import ABC, abstractmethod
from .mcp_client import MCPClient
import threading
import time
import logging
from threading import Event

logger = logging.getLogger(__name__)

class BaseTool(ABC):
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.mcp_clients = []
        self._health_threads = []
        self._stop_event = Event()

    def _validate_config(self):
        if "name" not in self.config:
            raise ValueError("Tool config missing 'name'")
        if "mcp_clients" not in self.config:
            self.config["mcp_clients"] = []
        # Add more validation as needed

    @abstractmethod
    def start(self):
        self._validate_config()
        self._attach_mcp_clients()
        self._start_health_checks()

    def stop(self):
        self._stop_event.set()
        for client in self.mcp_clients:
            client.disconnect()
        for t in self._health_threads:
            if t and t.is_alive():
                t.join(timeout=2)
        logger.info(f"[BaseTool:{self.name}] Stopped")

    @abstractmethod
    def to_tool(self):
        pass

    def _attach_mcp_clients(self):
        for cfg in self.config.get("mcp_clients", []):
            if not cfg.get("enabled", True):
                continue
            client = MCPClient(
                name=cfg["name"],
                host=cfg["host"],
                port=cfg["port"],
                protocol=cfg.get("protocol", "stdio"),
                token=cfg.get("auth_token")
            )
            client.connect()
            self.mcp_clients.append(client)

    def _start_health_checks(self):
        health_cfg = self.config.get("health_check", {})
        interval = health_cfg.get("interval", 10)
        check_type = health_cfg.get("type", "ping")

        # Client-level checks
        for client in self.mcp_clients:
            client.start_health_check(interval, check_type)

        # Tool-level health for internal (no clients)
        if not self.mcp_clients and check_type == "internal":
            def internal_health_loop():
                while not self._stop_event.is_set():
                    try:
                        self._health_check_internal()
                    except Exception as e:
                        logger.error(f"[BaseTool:{self.name}] Internal health failed: {e}")
                    self._stop_event.wait(timeout=interval)
            t = threading.Thread(target=internal_health_loop, daemon=True)
            t.start()
            self._health_threads.append(t)

    @abstractmethod
    def _health_check_internal(self):
        pass
