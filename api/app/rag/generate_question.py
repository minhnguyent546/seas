import argparse
import os

from jinja2 import Environment, select_autoescape
from langchain_openai import ChatOpenAI


def generate_question(
    args: argparse.Namespace,
    contexts: str | list[str],
    num_questions: int = 5,
    retries: int = 3,
) -> list[str]:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    if isinstance(contexts, str):
        if not contexts:
            raise ValueError("Contexts must be a non-empty string")
        contexts = [contexts]
    elif not contexts:
        raise ValueError("Contexts must be a non-empty list of strings")

    if not os.path.isfile(args.template_path):
        raise FileNotFoundError(
            f"Template file {args.template_path} not found"
        )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        api_key=openai_api_key,  # pyright: ignore[reportArgumentType]
    )

    # load template from args.template_path
    with open(args.template_path, "r", encoding="utf-8") as f:
        template_source = f.read()

    env = Environment(autoescape=select_autoescape(["html", "xml"]))
    template = env.from_string(template_source)
    prompt = template.render(contexts=contexts, num_questions=num_questions)
    retries_remaining = max(retries, 0)
    while retries_remaining >= 0:
        try:
            response = llm.invoke(prompt)

            content = response.content
            assert isinstance(content, str), (
                "Expected response.content to be a string"
            )

            generated_questions = [
                question.strip()
                for question in content.split("\n")
                if question.strip()
            ]
            return generated_questions
        except Exception as err:
            retries_remaining -= 1
            if retries_remaining >= 0:
                continue
            else:
                raise Exception(
                    f"Failed to generate questions after {retries} retries: {err}"
                ) from err
    return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate questions from contexts using LLM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--template_path",
        type=str,
        required=True,
        help="Path to the template (.j2) file",
    )

    args = parser.parse_args()

    test_contexts = [
        "đ) Thí sinh tham gia đội tuyển quốc gia thi đấu tại các giải quốc tế chính thức được Bộ Văn hoá, Thể thao và Du lịch xác nhận đã hoàn thành nhiệm vụ, bao gồm: Giải vô địch thế giới, Cúp thế giới, Thế vận hội Olympic, Đại hội Thể thao châu Á (ASIAD), Giải vô địch châu Á, Cúp châu Á, Giải vô địch Đông Nam Á, Đại hội Thể thao Đông Nam Á (SEA Games), Cúp Đông Nam Á; thời gian đoạt giải không quá 4 năm tính tới thời điểm xét tuyển thẳng;",
        "## Hồ sơ đăng ký phương thức 1\n\nÍt nhất một trong các bản photocopy: Chứng nhận được Bộ GDĐT cử tham gia các kỳ thi quốc tế; Giấy chứng nhận đoạt giải kỳ thi chọn học sinh giỏi quốc gia hoặc quốc tế; Giấy chứng nhận đoạt giải cuộc thi Khoa học kỹ thuật quốc gia hoặc quốc tế; Giấy chứng nhận đoạt giải quốc tế về thể dục thể thao, năng khiếu nghệ thuật; Giấy chứng nhận đoạt giải kỳ thi tay nghề khu vực ASEAN và thi tay nghề quốc tế và giấy chứng nhận các đối tượng tuyển thẳng, ưu tiên xét tuyển khác.\n- Thời gian nộp hồ sơ: từ nay đến **trước 17 giờ 00 ngày 30/6/2025**.\n- Nộp hồ sơ trực tiếp tại Phòng Đào tạo Trường ĐHCT hoặc gửi bưu điện đến địa chỉ: Phòng Đào tạo, Trường Đại học Cần Thơ",
    ]
    questions = generate_question(
        contexts=test_contexts, num_questions=3, retries=3, args=args
    )
    with open("questions.txt", "w") as f:
        f.write("\n".join(questions))


if __name__ == "__main__":
    main()
