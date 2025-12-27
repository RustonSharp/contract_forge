# 定义 BaseTool 抽象基类
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """
    Abstract base class for tools.
    """

    name: str
    description: str

    def __init__(self):
        pass

    @abstractmethod
    def run(self, input_data: dict, context: dict) -> dict:
        """
        Run the tool with the given input.

        Args:
            input_data (dict): The input to the tool.
            context (dict): Additional context for the tool.

        Returns:
            dict: The output of the tool.
        """
        pass