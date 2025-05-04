from typing import Callable, Dict, Optional

SKIP_PREREQ = (True, "")


class Prerequisite:
    """
    Represents a prerequisite check with its associated metadata and logic.
    """

    def __init__(
        self,
        name: str,
        description: str,
        reference: str,
        function: Callable[..., Dict],
        parameters: Optional[Dict] = None,
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.reference: str = reference
        self.function: Callable[..., Dict] = function
        self.parameters: Optional[Dict] = parameters

    def check(self) -> Dict:
        """
        Executes the prerequisite check function.
        """
        return self.function(self.parameters)
