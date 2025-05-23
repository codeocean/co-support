from typing import Dict, List


class Question:
    def __init__(self, text, property, args, type="str", comment=None):
        self.text = f"\033[1m{text}\033[0m"
        self.comment = f"\033[3m\033[90m{comment}\033[0m\n" if comment else ""
        self.property = property
        self.response = None
        self.type = type
        self.args = args

    def ask(self, silent=False):
        """
        Prompt the user for this question and return their response.
        """
        if vars(self.args).get(self.property):
            self.response = vars(self.args).get(self.property)
            return

        if silent:
            return

        response = ""
        if self.type == "str":
            while not response.strip():
                response = input(f"{self.text}\n{self.comment}> ")
        elif self.type == "bool":
            while not response.lower() in ["y", "n"]:
                response = input(f"{self.text}\n{self.comment}[y/n]> ")

            response = response.lower() == "y"
        else:
            print("Unknown command.")
            raise ValueError("Invalid type. Supported types: str, bool.")

        self.response = response

    def answer(self) -> Dict[str, str]:
        """
        Return the answer to this question.
        """
        return {self.property: self.response}


class YesNoQuestion(Question):
    def __init__(
        self,
        text,
        args,
        comment=None,
        property=None,
        type="bool",
        yes_question_list: List[Question] = [],
        no_question_list: List[Question] = [],
    ):
        self.yes_question_list = yes_question_list
        self.no_question_list = no_question_list
        super().__init__(text, property, args, type, comment)

    def ask(self, silent=False):
        """
        Prompt the user for this question and return their response.
        """
        super().ask(silent)

        silent_yes_questions = self.response is False
        for question in self.yes_question_list:
            question.ask(silent_yes_questions or silent)
        for question in self.no_question_list:
            question.ask(not silent_yes_questions or silent)

    def answer(self) -> Dict[str, str]:
        """
        Return answers from the subsequent questions.
        """
        answers = {}
        if self.property:
            answers[self.property] = self.response

        for question in self.yes_question_list + self.no_question_list:
            answers.update(question.answer())

        return answers


class Questions:
    def __init__(self, questions: List[Question], args):
        self.questions = questions
        self.silent = args.silent

    def ask(self):
        for question in self.questions:
            question.ask(self.silent)

    def answers(self) -> Dict[str, str]:
        answers = {}
        for question in self.questions:
            answers.update(question.answer())

        return answers
