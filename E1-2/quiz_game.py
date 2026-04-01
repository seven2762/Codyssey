from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from quiz import Quiz


class QuizGame:
    def __init__(
        self,
        state_path: str | Path = "state.json",
        input_func: Callable[[str], str] = input,
    ) -> None:
        self.state_path = Path(state_path)
        self.input_func = input_func
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None
        self.load_state()

    def default_quizzes(self) -> list[Quiz]:
        return [
            Quiz(
                "축구 경기에서 한 팀이 동시에 뛸 수 있는 선수 수는 몇 명인가?",
                ["9명", "10명", "11명", "12명"],
                3,
            ),
            Quiz(
                "국제 축구 경기의 정규 시간은 보통 몇 분인가?",
                ["70분", "80분", "90분", "100분"],
                3,
            ),
            Quiz(
                "페널티킥은 일반적으로 골문에서 몇 미터 지점에서 차는가?",
                ["11m", "9m", "12m", "15m"],
                1,
            ),
            Quiz(
                "축구에서 골키퍼가 페널티 에어리어 안에서 손으로 공을 잡을 수 있는 상황은?",
                [
                    "상대 팀 선수가 플레이한 공일 때",
                    "자기 팀 선수가 발로 의도적으로 백패스한 공일 때",
                    "자기 팀 선수가 스로인한 공이 직접 왔을 때",
                    "골키퍼가 이미 손에서 놓은 공을 다른 선수 접촉 없이 다시 손으로 잡을 때",
                ],
                1,
            ),
            Quiz(
                "월드컵에서 우승 국가에게 수여되는 트로피의 이름은?",
                ["챔피언스컵", "FIFA 월드컵 트로피", "골든볼", "슈퍼컵"],
                2,
            ),
            Quiz(
                "다음 중 축구에서 오프사이드가 적용되지 않는 방식은?",
                ["프리킥", "골킥", "코너킥", "스로인"],
                4,
            ),
        ]

    def load_state(self) -> None:
        if not self.state_path.exists():
            self.quizzes = self.default_quizzes()
            self.best_score = None
            self.save_state(silent=True)
            return

        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            quizzes_data = data.get("quizzes", [])
            best_score = data.get("best_score", None)

            self.quizzes = [Quiz.from_dict(item) for item in quizzes_data]
            if not self.quizzes:
                self.quizzes = self.default_quizzes()

            if best_score is None:
                self.best_score = None
            else:
                self.best_score = int(best_score)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            print("데이터 파일을 읽는 중 문제가 발생했습니다. 기본 퀴즈 데이터로 복구합니다.")
            self.quizzes = self.default_quizzes()
            self.best_score = None
            self.save_state(silent=True)

    def save_state(self, silent: bool = False) -> None:
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
        }

        try:
            with self.state_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError:
            if not silent:
                print("데이터 저장 중 오류가 발생했습니다.")

    def safe_input(self, prompt: str) -> str | None:
        try:
            return self.input_func(prompt)
        except EOFError:
            print("\n입력이 종료되었습니다. 가능한 범위에서 저장 후 안전하게 종료합니다.")
            self.save_state(silent=True)
            return None
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다. 가능한 범위에서 저장 후 안전하게 종료합니다.")
            self.save_state(silent=True)
            return None

    def input_number(self, prompt: str, min_value: int, max_value: int) -> int | None:
        while True:
            raw = self.safe_input(prompt)
            if raw is None:
                return None

            value = raw.strip()
            if value == "":
                print("빈 입력은 사용할 수 없습니다. 다시 입력해주세요.")
                continue

            try:
                number = int(value)
            except ValueError:
                print("숫자만 입력해주세요.")
                continue

            if not (min_value <= number <= max_value):
                print(f"{min_value}부터 {max_value} 사이의 숫자를 입력해주세요.")
                continue

            return number

    def show_menu(self) -> None:
        print("\n=== 퀴즈 게임 ===")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록 보기")
        print("4. 최고 점수 확인")
        print("5. 종료")

    def play_quiz(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return

        print(f"\n총 {len(self.quizzes)}문제를 시작합니다.")
        score = 0

        for index, quiz in enumerate(self.quizzes, start=1):
            quiz.display(index)
            answer = self.input_number("정답 번호를 입력하세요 (1~4): ", 1, 4)
            if answer is None:
                return

            if quiz.is_correct(answer):
                print("정답입니다!")
                score += 1
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다.")

        print(f"\n퀴즈 종료! 점수: {score}/{len(self.quizzes)}")
        self.update_best_score(score)
        self.save_state(silent=True)

    def add_quiz(self) -> None:
        print("\n=== 새 퀴즈 추가 ===")

        while True:
            question = self.safe_input("문제를 입력하세요: ")
            if question is None:
                return
            question = question.strip()
            if question == "":
                print("문제는 비어 있을 수 없습니다. 다시 입력해주세요.")
                continue
            break

        choices: list[str] = []
        for i in range(1, 5):
            while True:
                choice = self.safe_input(f"선택지 {i}를 입력하세요: ")
                if choice is None:
                    return
                choice = choice.strip()
                if choice == "":
                    print("선택지는 비어 있을 수 없습니다. 다시 입력해주세요.")
                    continue
                choices.append(choice)
                break

        answer = self.input_number("정답 번호를 입력하세요 (1~4): ", 1, 4)
        if answer is None:
            return

        try:
            new_quiz = Quiz(question, choices, answer)
        except ValueError as error:
            print(f"퀴즈를 추가할 수 없습니다: {error}")
            return

        self.quizzes.append(new_quiz)
        self.save_state()
        print("새 퀴즈가 저장되었습니다.")

    def list_quizzes(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return

        print("\n=== 퀴즈 목록 ===")
        for index, quiz in enumerate(self.quizzes, start=1):
            print(f"{index}. {quiz.question}")
            for choice_index, choice in enumerate(quiz.choices, start=1):
                print(f"   {choice_index}) {choice}")
            print(f"   정답: {quiz.answer}번")

    def update_best_score(self, score: int) -> None:
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            print("최고 점수가 갱신되었습니다!")
        else:
            print(f"현재 최고 점수는 {self.best_score}점입니다.")

    def show_best_score(self) -> None:
        if self.best_score is None:
            print("아직 퀴즈를 푼 기록이 없습니다.")
            return

        print(f"현재 최고 점수는 {self.best_score}점입니다.")

    def run(self) -> None:
        while True:
            self.show_menu()
            choice = self.input_number("메뉴 번호를 입력하세요: ", 1, 5)
            if choice is None:
                print("프로그램을 종료합니다.")
                return

            if choice == 1:
                self.play_quiz()
            elif choice == 2:
                self.add_quiz()
            elif choice == 3:
                self.list_quizzes()
            elif choice == 4:
                self.show_best_score()
            elif choice == 5:
                self.save_state(silent=True)
                print("프로그램을 종료합니다.")
                return
