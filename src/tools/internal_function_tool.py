import importlib
from ..base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class InternalFunctionTool(BaseTool):
    def start(self):
        try:
            module = importlib.import_module(self.config["module"])
            self.function = getattr(module, self.config["function"])
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load module/function {self.config['module']}.{self.config['function']}: {e}")
        super().start()
        logger.info(f"[InternalFunctionTool:{self.name}] Ready")

    def stop(self):
        super().stop()

    def to_tool(self):
        def tool(*args, **kwargs):
            try:
                result = self.function(*args, **kwargs)
                for client in self.mcp_clients:
                    client.send({"result": result})
                return result
            except Exception as e:
                logger.error(f"[InternalFunctionTool:{self.name}] Execution error: {e}")
                return {"error": str(e)}
        return tool

    def _health_check_internal(self):
        # Stub: Call function with dummy args to test
        try:
            self.function(health=True)  # Assume function handles health flag
        except Exception:
            raise  # Fail health if function breaks
