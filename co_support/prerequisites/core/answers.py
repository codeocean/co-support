from co_support.prerequisites.core.questions import Questions


class Answers:
    """
    Represents the user's answers to prerequisite questions.
    """
    def __init__(
        self,
        questions: Questions,
        args,
    ) -> None:
        questions.ask()
        self.answers = questions.answers()
        for answer in self.answers:
            if not self.answers[answer]:
                self.answers[answer] = vars(args).get(answer)

        if args.silent:
            if not args.version:
                raise ValueError("Version must be provided in silent mode.")

    def retrieve(self, property) -> str:
        """
        Retrieves answer for a specific property.
        """
        return self.answers.get(property, "")
