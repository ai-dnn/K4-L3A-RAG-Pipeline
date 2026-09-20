import streamlit as st
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot - Pháp luật Lao động",
    page_icon="⚖️",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("⚖️ RAG Chatbot")
    st.caption("Hỏi đáp về pháp luật lao động Việt Nam")
    top_k = st.slider("Số chunks truy xuất", 3, 10, 5)
    st.divider()
    st.markdown(
        "**Nguồn dữ liệu:**\n"
        "- Bộ luật Lao động 2019 (VBHN 2026)\n"
        "- Nghị định 145/2020/NĐ-CP\n"
        "- Nghị định 12/2022/NĐ-CP\n"
        "- Các bài viết tin tức lao động"
    )
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

st.title("⚖️ Hỏi đáp Pháp luật Lao động")
st.caption("Đặt câu hỏi về Bộ luật Lao động, nghị định hướng dẫn và tin tức lao động. Câu trả lời có trích dẫn nguồn.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander(f"📚 Nguồn tham khảo ({len(message['sources'])} chunks) — {message.get('retrieval_source', '')}"):
                for idx, src in enumerate(message["sources"], 1):
                    score_str = f"{src['score']:.4f}" if isinstance(src.get('score'), (int, float)) else "N/A"
                    st.markdown(
                        f"**[{idx}]** `{src['metadata'].get('title', '')}` "
                        f"| Method: `{src.get('retrieval_method', '')}` "
                        f"| Score: `{score_str}`"
                    )
                    st.caption(src["content"][:300] + ("..." if len(src["content"]) > 300 else ""))

query = st.chat_input("Nhập câu hỏi về pháp luật lao động...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và tổng hợp câu trả lời..."):
            from src.task10_generation import generate_with_citation

            result = generate_with_citation(query, top_k=top_k)
            answer = result["answer"]
            sources = result["sources"]
            retrieval_source = result["retrieval_source"]

        st.markdown(answer)

        if sources:
            with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks) — {retrieval_source}"):
                for idx, src in enumerate(sources, 1):
                    score_str = f"{src['score']:.4f}" if isinstance(src.get('score'), (int, float)) else "N/A"
                    st.markdown(
                        f"**[{idx}]** `{src['metadata'].get('title', '')}` "
                        f"| Method: `{src.get('retrieval_method', '')}` "
                        f"| Score: `{score_str}`"
                    )
                    st.caption(src["content"][:300] + ("..." if len(src["content"]) > 300 else ""))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
