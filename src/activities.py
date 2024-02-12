import random
import time

from playwright.sync_api import By

from src.browser import Browser


class Activities:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.page = browser.page

    def openDailySetActivity(self, cardId: int):
        self.page.click(
            f'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{cardId}]/div/card-content/mee-rewards-daily-set-item-content/div/a'
        )
        self.browser.utils.switchToNewTab(8)

    def openMorePromotionsActivity(self, cardId: int):
        self.page.click(
            f'//*[@id="more-activities"]/div/mee-card[{cardId}]/div/card-content/mee-rewards-more-activities-card-item/div/a'
        )
        self.browser.utils.switchToNewTab(8)

    def completeSearch(self):
        time.sleep(random.randint(5, 10))
        self.browser.utils.closeCurrentTab()

    def completeSurvey(self):
        self.page.click(f"btoption{random.randint(0, 1)}")
        time.sleep(random.randint(10, 15))
        self.browser.utils.closeCurrentTab()

    def completeQuiz(self):
        if not self.browser.utils.waitUntilQuizLoads():
            self.browser.utils.resetTabs()
            return
        self.page.click('//*[@id="rqStartQuiz"]')
        self.browser.utils.waitUntilVisible(
            '//*[@id="currentQuestionContainer"]/div/div[1]', 5
        )
        time.sleep(3)
        numberOfQuestions = self.page.evaluate(
            "() => _w.rewardsQuizRenderInfo.maxQuestions"
        )
        numberOfOptions = self.page.evaluate(
            "() => _w.rewardsQuizRenderInfo.numberOfOptions"
        )
        for question in range(numberOfQuestions):
            if numberOfOptions == 8:
                answers = []
                for i in range(numberOfOptions):
                    isCorrectOption = self.page.eval_on_selector(
                        f"rqAnswerOption{i}", "(el) => el.getAttribute('iscorrectoption')"
                    )
                    if isCorrectOption and isCorrectOption.lower() == "true":
                        answers.append(f"rqAnswerOption{i}")
                for answer in answers:
                    self.page.click(answer)
                    time.sleep(5)
                    if not self.browser.utils.waitUntilQuestionRefresh():
                        self.browser.utils.resetTabs()
                        return
            elif numberOfOptions in [2, 3, 4]:
                correctOption = self.page.evaluate(
                    "() => _w.rewardsQuizRenderInfo.correctAnswer"
                )
                for i in range(numberOfOptions):
                    if (
                        self.page.eval_on_selector(
                            f"rqAnswerOption{i}",
                            "(el) => el.getAttribute('data-option')",
                        )
                        == correctOption
                    ):
                        self.page.click(f"rqAnswerOption{i}")
                        time.sleep(5)
                        if not self.browser.utils.waitUntilQuestionRefresh():
                            self.browser.utils.resetTabs()
                            return
                        break
            if question + 1 != numberOfQuestions:
                time.sleep(5)
        time.sleep(5)
        self.browser.utils.closeCurrentTab()

    def completeABC(self):
        counter = self.page.inner_text('//*[@id="QuestionPane0"]/div[2]')
        numberOfQuestions = max(int(s) for s in counter.split() if s.isdigit())
        for question in range(numberOfQuestions):
            self.page.click(
                f"questionOptionChoice{question}{random.randint(0, 2)}"
            )
            time.sleep(5)
            self.page.click(f"nextQuestionbtn{question}")
            time.sleep(3)
        time.sleep(5)
        self.browser.utils.closeCurrentTab()

    def completeThisOrThat(self):
        if not self.browser.utils.waitUntilQuizLoads():
            self.browser.utils.resetTabs()
            return
        self.page.click('//*[@id="rqStartQuiz"]')
        self.browser.utils.waitUntilVisible(
            '//*[@id="currentQuestionContainer"]/div/div[1]', 10
        )
        time.sleep(3)
        for _ in range(10):
            correctAnswerCode = self.page.evaluate(
                "() => _w.rewardsQuizRenderInfo.correctAnswer"
            )
            answer1, answer1Code = self.getAnswerAndCode("rqAnswerOption0")
            answer2, answer2Code = self.getAnswerAndCode("rqAnswerOption1")
            if answer1Code == correctAnswerCode:
                answer1.click()
                time.sleep(8)
            elif answer2Code == correctAnswerCode:
                answer2.click()
                time.sleep(8)

        time.sleep(5)
        self.browser.utils.closeCurrentTab()

    def getAnswerAndCode(self, answerId: str) -> tuple:
        answerEncodeKey = self.page.evaluate("() => _G.IG")
        answer = self.page.query_selector(answerId)
        answerTitle = answer.get_attribute("data-option")
        if answerTitle is not None:
            return (
                answer,
                self.browser.utils.getAnswerCode(answerEncodeKey, answerTitle),
            )
        else:
            return (answer, None)
