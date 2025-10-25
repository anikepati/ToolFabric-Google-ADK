import yaml
import logging
from tool_factory import create_tool
from threading import RLock

logger = logging.getLogger(__name__)

class ToolFabric:
    def __init__(self, config_path=None):
        self.tool_instances = {}
        self.tools = {}
        self._lock = RLock()
        self.config_path = config_path
        self.config = {}
        if config_path:
            self.load_from_yaml(config_path)

    def load_from_yaml(self, path):
        with open(path, "r") as f:
            self.config = yaml.safe_load(f)
        logger.info(f"Loaded config from {path}")

    def setup(self):
        with self._lock:
            for cfg in self.config.get("tools", []):
                name = cfg["name"]
                instance = create_tool(cfg)
                instance.start()
                self.tool_instances[name] = instance
                self.tools[name] = instance.to_tool()
                logger.info(f"[ToolFabric] Loaded tool: {name}")
        return self.tools

    def attach_all_to_agent(self, agent):
        with self._lock:
            for name, func in list(self.tools.items()):
                self._attach_single_to_agent(name, func, agent)
        logger.info(f"[ToolFabric] Attached {len(self.tools)} tools to agent")

    def _attach_single_to_agent(self, name, func, agent):
        try:
            if hasattr(agent, 'attach_tool'):
                agent.attach_tool(name, func)
            elif hasattr(agent, 'tools'):
                agent.tools[name] = func
            else:
                logger.warning(f"Agent {agent} lacks attach_tool or tools dict")
        except Exception as e:
            logger.error(f"Failed to attach {name} to agent: {e}")

    def stop_all(self):
        with self._lock:
            for instance in list(self.tool_instances.values()):
                instance.stop()
            self.tool_instances.clear()
            self.tools.clear()
            logger.info("[ToolFabric] All tools stopped")
