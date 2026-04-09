from app.nodes.base_node import BaseNode, NodeExecutionError
from app.utils.logger import logger


class Pipeline:
    def __init__(self, nodes: list[BaseNode]):
        self.nodes = nodes

    def run(self, initial_inputs: dict) -> dict:
        state = initial_inputs.copy()
        for node in self.nodes:
            try:
                state = node.execute(state)
            except NodeExecutionError as e:
                logger.error(f"Pipeline halted at {node.__class__.__name__}: {e}")
                return {"error": str(e), "partial_state": state}
        return state
