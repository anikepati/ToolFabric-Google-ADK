import subprocess
from ..base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class MCPBasedTool(BaseTool):
    def start(self):
        cmd = self.config.get("command", [])
        self.process = None
        if cmd:
            try:
                logger.info(f"[MCPBasedTool:{self.name}] Starting process: {' '.join(cmd)}")
                self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                raise RuntimeError(f"Failed to start process for {self.name}: {e}")
        super().start()
        logger.info(f"[MCPBasedTool:{self.name}] Ready")

    def stop(self):
        super().stop()
        if getattr(self, "process", None) and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        logger.info(f"[MCPBasedTool:{self.name}] Stopped")

    def to_tool(self):
        def tool(action, payload=None):
            payload = payload or {}
            try:
                for client in self.mcp_clients:
                    client.send({"action": action, "payload": payload})
                return f"[{self.name}] {action} executed"
            except Exception as e:
                logger.error(f"[MCPBasedTool:{self.name}] Tool execution error: {e}")
                return f"[{self.name}] Error executing {action}: {e}"
        return tool

    def _health_check_internal(self):
        # Stub: Check if process is alive
        if self.process and self.process.poll() is not None:
            raise RuntimeError("Process died")
