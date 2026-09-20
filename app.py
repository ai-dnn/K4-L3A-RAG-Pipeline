"""Vietnamese labor-law chatbot. Run with: streamlit run app.py."""

from urllib.parse import urlparse

import streamlit as st

from src.task10_generation import generate_with_citation


st.set_page_config(page_title="Sổ tay lao động", page_icon="⚖️", layout="centered")
st.markdown("""
<style>
    .stMainBlockContainer { max-width: 860px; padding-top: 3rem; }
    [data-testid="stHeading"] h1,
    [data-testid="stHeading"] h2,
    [data-testid="stHeading"] h3 { letter-spacing: -.035em; }
    [data-testid="stHeading"] h1 { font-family: Georgia, 'Times New Roman', serif; font-weight: 500; }
    [data-testid="stSidebar"] { border-right: 1px solid #dce4ee; }
    [data-testid="stChatMessage"] { border-radius: 12px; padding: 1.2rem; }
    [data-testid="stChatInput"] { border: 1px solid #9aacc4; }
    [data-testid="stCaptionContainer"] p { color: #53647a; }
    @media (max-width: 640px) {
        .stMainBlockContainer { padding-top: 1.5rem; }
        [data-testid="stChatMessage"] { padding: .75rem; }
    }
</style>
""", unsafe_allow_html=True)

SUGGESTIONS = [
    ("Nghỉ phép", "Người lao động được nghỉ hằng năm bao nhiêu ngày?"),
    ("Thử việc", "Thời gian thử việc tối đa là bao lâu?"),
    ("Làm thêm giờ", "Tiền lương làm thêm giờ được tính như thế nào?"),
]


def render_message(message: dict) -> None:
    with st.chat_message(message["role"], avatar="⚖️" if message["role"] == "assistant" else None):
        st.markdown(message["content"])
        sources = message.get("sources", [])
        if sources:
            st.caption("Đối chiếu các số [1], [2] trong câu trả lời với trích đoạn bên dưới.")
        for index, source in enumerate(sources, 1):
            metadata = source.get("metadata", {})
            title = metadata.get("title") or metadata.get("source") or "Tài liệu"
            with st.expander(f"[{index}] {title}"):
                st.markdown(source["content"])
                if metadata.get("source"):
                    st.caption(f"Tài liệu: {metadata['source']}")
                url = metadata.get("url")
                if isinstance(url, str) and urlparse(url).scheme in {"http", "https"} and urlparse(url).netloc:
                    st.link_button("Mở nguồn gốc", url)


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚖️ Sổ tay lao động")
    st.caption("Tra cứu pháp luật lao động Việt Nam")
    if st.button("Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.subheader("Hỏi và đối chiếu")
    st.write("Đặt câu hỏi cụ thể về nghỉ phép, hợp đồng, tiền lương hoặc thời giờ làm việc.")
    st.write("Mở nguồn dưới mỗi câu trả lời để đọc trích đoạn được sử dụng.")
    st.caption("Mỗi câu hỏi được tra cứu độc lập. Hãy nhắc lại thông tin cần thiết khi hỏi tiếp.")
    with st.expander("Tùy chọn tra cứu"):
        top_k = st.slider("Số trích đoạn tham khảo", 3, 10, 5)

st.title("Hiểu rõ quyền lợi của bạn tại nơi làm việc.")
st.caption("Hỏi bằng tiếng Việt. Câu trả lời dựa trên tài liệu và đi kèm nguồn để bạn kiểm tra.")

suggestion = None
if not st.session_state.messages:
    st.write("")
    st.subheader("Bạn muốn tìm hiểu điều gì?")
    for column, (label, question) in zip(st.columns(3), SUGGESTIONS):
        with column:
            if st.button(label, help=question, use_container_width=True):
                suggestion = question
    st.caption("Chọn một chủ đề hoặc nhập câu hỏi của bạn bên dưới.")

for message in st.session_state.messages:
    render_message(message)

query = st.chat_input("Ví dụ: Tôi làm việc 8 tháng thì được nghỉ phép bao nhiêu ngày?", max_chars=4000)
query = (query or suggestion or "").strip()
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    render_message(st.session_state.messages[-1])
    with st.spinner("Đang tra cứu tài liệu và soạn câu trả lời…"):
        try:
            result = generate_with_citation(query, top_k=top_k)
            message = {"role": "assistant", "content": result["answer"], "sources": result["sources"]}
        except Exception:
            message = {"role": "assistant", "content": "Không thể hoàn tất tra cứu. Vui lòng thử lại.", "sources": []}
    st.session_state.messages.append(message)
    st.rerun()
