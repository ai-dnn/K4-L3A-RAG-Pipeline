import streamlit as st
from dotenv import load_dotenv


load_dotenv()

from src.task10_generation import generate_with_citation

st.set_page_config(
    page_title="RAG Chatbot Pipeline",
    page_icon="🤖",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("⚙️ Cấu hình Chatbot")
    st.markdown("Hệ thống RAG Pipeline với Hybrid Retrieval (Dense + BM25) và Reciprocal Rank Fusion.")
    top_k = st.slider("Số lượng chunks (top-k)", 1, 10, 5)
    if st.button("🗑️ Xoá lịch sử hội thoại"):
        st.session_state.messages = []
        st.rerun()

st.title("💬 RAG Assistant")
st.caption("Chatbot trả lời câu hỏi dựa trên bộ tài liệu kèm trích dẫn (citation) minh bạch.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            method = message.get("retrieval_source", "hybrid")
            st.caption(f"🔍 Phương thức tìm kiếm: `{method}`")
            with st.expander(f"📚 Nguồn tham khảo ({len(message['sources'])} chunks)"):
                for idx, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata", {})
                    score = src.get("score", 0.0)
                    st.markdown(
                        f"**[{idx}] {meta.get('title', 'Tài liệu')}** "
                        f"(`Score: {score:.4f}` | `Nguồn: {meta.get('source', 'N/A')}`)\n\n"
                        f"> {src.get('content', '')}"
                    )

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và sinh câu trả lời..."):
            result = generate_with_citation(query, top_k=top_k)

        answer = result.get("answer", "")
        sources = result.get("sources", [])
        retrieval_source = result.get("retrieval_source", "hybrid")

        st.markdown(answer)

        if sources:
            st.caption(f"🔍 Phương thức tìm kiếm: `{retrieval_source}`")
            with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                for idx, src in enumerate(sources, 1):
                    meta = src.get("metadata", {})
                    score = src.get("score", 0.0)
                    st.markdown(
                        f"**[{idx}] {meta.get('title', 'Tài liệu')}** "
                        f"(`Score: {score:.4f}` | `Nguồn: {meta.get('source', 'N/A')}`)\n\n"
                        f"> {src.get('content', '')}"
                    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
