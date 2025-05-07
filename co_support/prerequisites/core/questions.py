from typing import Dict, List


class Question:
    def __init__(self, text, property, args, type="str", comment=None):
        self.text = f"\033[1m{text}\033[0m"
        self.comment = f"\033[3m\033[90m{comment}\033[0m\n" if comment else ""
        self.property = property
        self.response = None
        self.type = type
        self.args = args

    def ask(self) -> str:
        """
        Prompt the user for this question and return their response.
        """
        if vars(self.args).get(self.property):
            self.response = vars(self.args).get(self.property)
            return

        response = ""
        match self.type:
            case "str":
                while not response.strip():
                    response = input(f"{self.text}\n{self.comment}> ")
            case "bool":
                while not response.lower() in ["y", "n"]:
                    response = input(f"{self.text}\n{self.comment}[y/n]> ")
                response = response.lower() == "y"
            case _:
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

    def ask(self) -> str:
        """
        Prompt the user for this question and return their response.
        """

        if vars(self.args).get(self.property):
            self.response = vars(self.args).get(self.property)
            return

        response = ""
        while not response.lower() in ["y", "n"]:
            response = input(f"{self.text}\n{self.comment}[y/n]> ")

        if self.property:
            self.response = response.lower() == "y"

        if response.lower() == "y":
            for question in self.yes_question_list:
                question.ask()
        elif response.lower() == "n":
            for question in self.no_question_list:
                question.ask()
        else:
            raise ValueError("Invalid response. Please answer 'y' or 'n'.")

    def answer(self) -> str:
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
    def __init__(self, list: List[Question], args):
        self.list = list
        self.silent = args.silent

    def ask(self):
        if not self.silent:
            for question in self.list:
                question.ask()

    def answers(self):
        answers = {}
        for question in self.list:
            answers.update(question.answer())

        return answers
