from abc import ABC, abstractmethod
from app.utils.logger import logger


class NodeExecutionError(Exception):
    """Raised when a node fails during execution."""
    pass


class BaseNode(ABC):
    """Abstract base class for all pipeline nodes."""

    @abstractmethod
    def _run(self, inputs: dict) -> dict:
        """Subclasses implement this with actual logic."""
        ...

    def execute(self, inputs: dict) -> dict:
        """Execute the node, wrapping errors as NodeExecutionError."""
        try:
            return self._run(inputs)
        except NodeExecutionError:
            raise
        except Exception as e:
            logger.error(
                f"Node {self.__class__.__name__} failed: {e}",
                exc_info=True,
            )
            raise NodeExecutionError(
                f"{self.__class__.__name__} failed: {e}"
            ) from e
