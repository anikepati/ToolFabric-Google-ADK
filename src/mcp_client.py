import time
import threading
import json
import logging
from abc import ABC, abstractmethod
from threading import Event, Lock

logger = logging.getLogger(__name__)

class ProtocolHandler(ABC):
    @abstractmethod
    def connect(self, host, port):
        pass

    @abstractmethod
    def send(self, payload):
        pass

    @abstractmethod
    def ping(self):
        pass

class StdioHandler(ProtocolHandler):
    def __init__(self):
        self.proc = None  # Placeholder for actual subprocess

    def connect(self, host, port):
        # Stub: In real impl, launch or connect to stdio process
        logger.info("Stdio connected")
        return True

    def send(self, payload):
        # Stub: Write to stdin
        logger.debug(f"Stdio send: {payload}")
        return {"status": "sent"}

    def ping(self):
        # Stub: Send ping, assume success
        response = self.send({"type": "ping"})
        return response.get("pong", False)  # Simulate check

class SSEHandler(ProtocolHandler):
    def connect(self, host, port):
        # Stub: In real impl, use requests or websockets for SSE
        logger.info(f"SSE connected to {host}:{port}")
        return True

    def send(self, payload):
        # Stub: POST or SSE event
        logger.debug(f"SSE send: {payload}")
        return {"status": "sent"}

    def ping(self):
        # Stub: Send ping via SSE
        response = self.send({"type": "ping"})
        return response.get("pong", False)

class MCPClient:
    def __init__(self, name, host, port, protocol="stdio", token=None):
        self.name = name
        self.host = host
        self.port = port
        self.token = token
        self.protocol = protocol
        self.connected = False
        self.handler = self._get_handler(protocol)
        self._health_thread = None
        self._stop_health = Event()
        self._lock = Lock()

    def _get_handler(self, protocol):
        if protocol == "stdio":
            return StdioHandler()
        elif protocol == "sse":
            return SSEHandler()
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    def connect(self):
        with self._lock:
            try:
                success = self.handler.connect(self.host, self.port)
                self.connected = success
                if success:
                    logger.info(f"[MCPClient:{self.name}] Connected via {self.protocol} to {self.host}:{self.port}")
                else:
                    logger.error(f"[MCPClient:{self.name}] Connect failed")
            except Exception as e:
                logger.error(f"[MCPClient:{self.name}] ERROR connecting: {e}")
                self.connected = False

    def send(self, payload):
        with self._lock:
            if not self.connected:
                logger.warning(f"[MCPClient:{self.name}] WARNING: not connected")
                return None
            try:
                result = self.handler.send(payload)
                logger.debug(f"[MCPClient:{self.name}:{self.protocol}] SEND → {payload}")
                return result
            except Exception as e:
                logger.error(f"[MCPClient:{self.name}] Send error: {e}")
                self.connected = False
                return None

    def disconnect(self):
        with self._lock:
            self.connected = False
            self._stop_health.set()
            if self._health_thread and self._health_thread.is_alive():
                self._health_thread.join(timeout=1)
            logger.info(f"[MCPClient:{self.name}] Disconnected")

    def start_health_check(self, interval=5, check_type="ping"):
        def health_loop():
            while not self._stop_health.is_set():
                try:
                    with self._lock:
                        if not self.connected:
                            logger.warning(f"[MCPClient:{self.name}] Health check failed, reconnecting...")
                            self.connect()
                        elif check_type == "ping":
                            pong = self.handler.ping()
                            if not pong:
                                logger.warning(f"[MCPClient:{self.name}] Ping failed, reconnecting...")
                                self.connected = False
                                self.connect()
                except Exception as e:
                    logger.error(f"[MCPClient:{self.name}] Health error: {e}")
                self._stop_health.wait(timeout=interval)
        self._stop_health.clear()
        self._health_thread = threading.Thread(target=health_loop, daemon=True)
        self._health_thread.start()
