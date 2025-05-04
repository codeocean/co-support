from co_support.prerequisites.core.questions import Questions, QuestionsList


class Answers:
    """
    Represents the user's answers to prerequisite questions.
    """
    def __init__(
        self,
        questions: Questions,
        args,
    ) -> None:
        self.answers = {}
        self.answers[QuestionsList.VERSION.name] = args.version
        self.answers[QuestionsList.ROLE_ARN.name] = args.role
        self.answers[QuestionsList.HOSTING_DOMAIN.name] = args.domain
        self.answers[QuestionsList.ROUTE53_EXISTING.name] = args.zone
        self.answers[QuestionsList.CERT_VALIDATION.name] = args.cert
        self.answers[QuestionsList.PRIVATE_CA.name] = args.private_ca
        self.answers[QuestionsList.EXISTING_VPC.name] = args.vpc
        self.answers[QuestionsList.INTERNET_FACING.name] = args.internet_facing

        self.answers.update(questions.ask(self.answers))

        if args.silent:
            if not args.version:
                raise ValueError("Version must be provided in silent mode.")

    def get_answer(self, question) -> str:
        """
        Retrieves the answer to a specific question.
        """
        answer = self.answers.get(question.name, "")
        if isinstance(answer, str) and answer.lower() in ["y", "n"]:
            answer = answer.lower() == "y"

        return answer
