from abc import ABC, abstractmethod
from typing import Dict

SKIP_PREREQ = (True, "")


class Prerequisite(ABC):
    """
    Represents a prerequisite check with its associated metadata and logic.
    """

    def __init__(
        self,
        name: str,
        description: str,
        reference: str,
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.reference: str = reference

    @abstractmethod
    def check(self) -> Dict:
        """
        Executes the prerequisite check function.
        """
        pass
