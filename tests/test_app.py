from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app.py"
RESULT = {
    "answer": "Trích dẫn minh họa [1].",
    "sources": [{"content": "Nội dung nguồn thử nghiệm.", "metadata": {
        "title": "Tài liệu thử nghiệm", "source": "example.docx", "url": None,
    }}],
    "retrieval_source": "hybrid",
}


def test_chat_preserves_sources_across_reruns_and_clears_history():
    with patch("src.task10_generation.generate_with_citation", return_value=RESULT) as generate:
        app = AppTest.from_file(str(APP)).run()
        assert not app.exception
        app.chat_input[0].set_value("Câu hỏi thử nghiệm").run()
        assert not app.exception
        generate.assert_called_once_with("Câu hỏi thử nghiệm", top_k=5)
        assert len(app.chat_message) == 2
        assert app.session_state.messages[1]["sources"] == RESULT["sources"]
        assert any(item.label == "[1] Tài liệu thử nghiệm" for item in app.expander)
        app.slider[0].set_value(7).run()
        assert len(app.chat_message) == 2
        assert generate.call_count == 1
        next(button for button in app.button if button.label == "Cuộc trò chuyện mới").click().run()
        assert not app.chat_message
        assert app.session_state.messages == []


def test_suggestion_and_failure_leave_chat_usable():
    with patch("src.task10_generation.generate_with_citation", side_effect=RuntimeError("private")) as generate:
        app = AppTest.from_file(str(APP)).run()
        next(button for button in app.button if button.label == "Nghỉ phép").click().run()
        assert not app.exception
        assert generate.call_count == 1
        assert len(app.chat_message) == 2
        assert "private" not in app.session_state.messages[1]["content"]
        assert app.session_state.messages[1]["sources"] == []
        assert app.chat_input
