from typing import Dict


class Answers:
    """
    Represents the user's answers to prerequisite questions.
    """
    def __init__(
        self,
        answers: Dict[str, str],
        args,
    ) -> None:
        self.answers = answers

        if args.silent:
            if not args.version:
                raise ValueError("Version must be provided in silent mode.")

    def retrieve(self, property) -> str:
        """
        Retrieves answer for a specific property.
        """
        return self.answers.get(property, "")
