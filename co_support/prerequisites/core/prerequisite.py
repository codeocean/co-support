from typing import Callable, Dict, Optional


class Prerequisite:
    def __init__(
        self,
        name: str,
        description: str,
        reference: str,
        function: Callable[..., Dict],
        parameters: Optional[Dict] = None
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.reference: str = reference
        self.function: Callable[..., Dict] = function
        self.parameters: Optional[Dict] = parameters

    def check(self):
        return self.function(self.parameters)
