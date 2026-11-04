"""Customer Feedback Text Mining & RAG Dashboard.

Interactive web application for exploring customer complaints,
diagnosing root causes, and querying the RAG knowledge base.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Setup project root path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

load_dotenv()

from customer_feedback.rag.answer_generation import RAGGenerator  # noqa: E402
from customer_feedback.rag.document_loader import (  # noqa: E402
    Document,
    load_policy_documents,
    load_ranked_issues,
    load_reviews_as_documents,
)
from customer_feedback.rag.embeddings import get_embedder  # noqa: E402
from customer_feedback.rag.retrieval import HybridRetriever, RetrievedContext  # noqa: E402
from customer_feedback.rag.vector_store import ChromaVectorStore  # noqa: E402

# Streamlit Page Config
st.set_page_config(
    page_title="Customer Feedback RAG Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Đang khởi tạo Vector Store và Mô hình Embedding...")
def get_rag_components(provider: str = "local"):
    """Load or build vector store and hybrid retriever once and cache in memory."""
    vectordb_dir = ROOT / "data/vector_store"
    reviews_path = ROOT / "data/processed/reviews_clean.parquet"
    policies_dir = ROOT / "docs/policies"

    embedder = get_embedder(provider=provider)
    vector_store = ChromaVectorStore(persist_dir=vectordb_dir, embedder=embedder)

    corpus_docs = []
    if reviews_path.exists():
        corpus_docs = load_reviews_as_documents(reviews_path, max_docs=500)

    policy_docs = []
    if policies_dir.exists():
        policy_docs = load_policy_documents(policies_dir)

    retriever = HybridRetriever(vector_store=vector_store, corpus_documents=corpus_docs)
    generator = RAGGenerator()

    return vector_store, retriever, generator, corpus_docs, policy_docs


def main() -> None:
    st.title("📊 Customer Feedback Text Mining & RAG System")
    st.caption("Hệ thống phát hiện khiếu nại, phân tích nguyên nhân cốt lõi và đề xuất giải pháp có trích dẫn bằng chứng.")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cấu hình Hệ thống")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        has_key = bool(gemini_key and gemini_key != "your_gemini_api_key_here")

        if has_key:
            st.success("🟢 Gemini API: Đã kết nối")
        else:
            st.warning("🟡 Gemini API: Chưa có key (Đang dùng Offline Heuristics)")

        provider = st.selectbox(
            "Mô hình Embedding",
            options=["local", "gemini"],
            index=0 if os.getenv("EMBEDDING_PROVIDER", "local") == "local" else 1,
            help="Local: SentenceTransformers (offline, nhanh). Gemini: text-embedding-004.",
        )

        st.markdown("---")
        st.subheader("📁 Đường dẫn dữ liệu")
        st.code("data/processed/issues_ranked.json", language="text")
        st.code("data/processed/reviews_clean.parquet", language="text")

    # Load RAG Components
    try:
        vector_store, retriever, generator, corpus_docs, policy_docs = get_rag_components(provider=provider)
    except Exception as e:
        st.error(f"Lỗi khởi tạo RAG components: {e}")
        st.stop()

    tab1, tab2, tab3 = st.tabs([
        "🚨 Sự cố đã xếp hạng (Ranked Issues)",
        "💬 Trợ lý Hỏi Đáp RAG Trực Tiếp",
        "📚 Kho Bằng chứng & Quy chuẩn",
    ])

    # TAB 1: Ranked Issues
    with tab1:
        issues_path = ROOT / "data/processed/issues_ranked.json"
        if not issues_path.exists():
            st.info("Chưa tìm thấy file `issues_ranked.json`. Hãy chạy `python scripts/run_issue_analysis.py` để tạo dữ liệu.")
        else:
            with open(issues_path, "r", encoding="utf-8") as f:
                issues = json.load(f)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tổng số sự cố phát hiện", len(issues))
            with col2:
                top_issue = issues[0] if issues else {}
                st.metric("Sự cố ưu tiên cao nhất", f"Rank #1: {top_issue.get('label', 'N/A')}")
            with col3:
                top_score = top_issue.get("priority_score", 0.0)
                st.metric("Điểm ưu tiên cao nhất", f"{top_score:.1f} / 100")

            st.markdown("---")
            st.subheader("Danh sách chi tiết các sự cố cần xử lý:")

            # Check for precomputed RAG insights
            insights_path = ROOT / "data/processed/rag_insights.json"
            precomputed_map = {}
            if insights_path.exists():
                try:
                    with open(insights_path, "r", encoding="utf-8") as f:
                        for item in json.load(f):
                            precomputed_map[item["issue_id"]] = item
                except Exception:
                    pass

            for issue in issues:
                rank = issue.get("rank", 0)
                label = issue.get("label", "Unknown").upper()
                priority = issue.get("priority_score", 0.0)
                terms = ", ".join(issue.get("top_terms", []))
                metrics = issue.get("metrics", {})

                with st.expander(f"🔴 Rank #{rank}: {label} — Điểm ưu tiên: {priority:.1f}/100", expanded=(rank == 1)):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.write(f"**Số lượng phàn nàn:** {metrics.get('n_reviews', 'N/A')}")
                    c2.write(f"**Tỉ lệ đánh giá 1 sao:** {float(metrics.get('pct_one_star', 0))*100:.1f}%")
                    c3.write(f"**Từ khóa lỗi:** `{terms}`")
                    c4.write(f"**Tăng trưởng:** {metrics.get('growth_recent_vs_prev', 0):.2f}")

                    # Show insight
                    if issue.get("issue_id") in precomputed_map:
                        insight = precomputed_map[issue.get("issue_id")]
                        st.markdown("#### 🔍 Phân tích nguyên nhân cốt lõi (Root Cause)")
                        st.info(insight.get("root_cause", ""))

                        st.markdown("#### ⚡ Khuyến nghị hành động (Recommendations)")
                        for r in insight.get("recommendations", []):
                            st.write(f"- {r}")

                        st.markdown("#### 📑 Bằng chứng trích dẫn (Citations)")
                        for cite in insight.get("citations", []):
                            if cite.get("type") == "review":
                                st.caption(f"📌 **{cite.get('id')}**: *{cite.get('snippet', cite.get('source', ''))}*")
                            else:
                                st.caption(f"📘 **Chính sách [{cite.get('id')}]**: {cite.get('title', cite.get('source', ''))}")
                    else:
                        if st.button(f"🚀 Chạy RAG phân tích Sự cố #{rank}", key=f"btn_{rank}"):
                            with st.spinner("Đang truy xuất ngữ cảnh và gọi LLM..."):
                                ctx = retriever.retrieve_context_for_issue(issue, top_reviews=3, top_policies=2)
                                res = generator.generate_insight(issue, ctx)
                                st.markdown("#### 🔍 Phân tích nguyên nhân")
                                st.info(res.root_cause)
                                st.markdown("#### ⚡ Khuyến nghị")
                                for r in res.recommendations:
                                    st.write(f"- {r}")

    # TAB 2: Interactive RAG Q&A
    with tab2:
        st.subheader("💬 Hỏi đáp trực tiếp về đánh giá khách hàng & chính sách")
        st.write("Bạn có thể đặt bất kỳ câu hỏi nào để RAG tìm kiếm bằng chứng trong kho review và chính sách:")

        example_queries = [
            "Khách hàng phàn nàn nhiều nhất về vấn đề gì?",
            "Tại sao khách phản ánh về vị đắng và ôi thiu?",
            "Chính sách bồi thường khi sản phẩm bị vỡ hoặc rò rỉ là gì?",
            "Quy định về hạn sử dụng tối thiểu khi giao hàng cho khách là bao lâu?",
        ]

        selected_example = st.selectbox("Gợi ý câu hỏi mẫu:", ["-- Chọn câu hỏi mẫu hoặc tự gõ bên dưới --"] + example_queries)

        user_query = st.text_input(
            "Nhập câu hỏi của bạn:",
            value="" if selected_example.startswith("--") else selected_example,
            placeholder="Ví dụ: Khách hàng gặp vấn đề gì với bao bì và hộp giao hàng?",
        )

        if st.button("🔍 Tìm kiếm & Sinh câu trả lời", type="primary") and user_query:
            with st.spinner("Đang thực hiện Hybrid Search (Vector + BM25) và tổng hợp câu trả lời..."):
                # Retrieve reviews
                matched_reviews = retriever.hybrid_search(user_query, collection_name="feedback_reviews", top_k=4)
                # Retrieve policies
                matched_policies = retriever.dense_search(user_query, collection_name="feedback_policies", top_k=2)

                ctx = RetrievedContext(
                    issue_id=0,
                    label=user_query,
                    query_str=user_query,
                    evidence_reviews=matched_reviews,
                    relevant_policies=matched_policies,
                )

                issue_stub = {
                    "issue_id": 0,
                    "rank": 1,
                    "label": user_query,
                    "priority_score": 85.0,
                    "top_terms": user_query.split()[:5],
                    "metrics": {"n_reviews": len(matched_reviews), "pct_one_star": 0.75},
                }

                insight = generator.generate_insight(issue_stub, ctx)

                st.markdown("### 💡 Kết quả phân tích từ RAG")
                st.markdown(insight.root_cause)

                st.markdown("### 📋 Đề xuất hành động")
                for rec in insight.recommendations:
                    st.write(f"- {rec}")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("#### 💬 Bằng chứng Review tìm thấy")
                    if not matched_reviews:
                        st.caption("Không tìm thấy review trực tiếp khớp.")
                    for rev in matched_reviews:
                        r_id = rev.metadata.get("review_id", rev.doc_id)
                        score = rev.metadata.get("score", "N/A")
                        sim = rev.metadata.get("rrf_score", rev.metadata.get("similarity_score", ""))
                        st.markdown(f"- **Review #{r_id}** (Sao: {score}⭐, Relevance: `{sim}`):")
                        st.caption(f"> \"{rev.text}\"")

                with col_b:
                    st.markdown("#### 📘 Điều khoản Chính sách tham chiếu")
                    if not matched_policies:
                        st.caption("Không có tài liệu chính sách liên quan.")
                    for pol in matched_policies:
                        p_id = pol.metadata.get("policy_id", pol.doc_id)
                        title = pol.metadata.get("title", "")
                        st.markdown(f"- **[{p_id}] {title}**:")
                        st.caption(pol.text)

    # TAB 3: Knowledge Base Explorer
    with tab3:
        st.subheader("📚 Khám phá Tài liệu Quy chuẩn Vận hành (Operational Policies)")
        if not policy_docs:
            st.info("Chưa có tài liệu chính sách trong `docs/policies/`.")
        else:
            for pol in policy_docs:
                p_id = pol.metadata.get("policy_id", pol.doc_id)
                p_title = pol.metadata.get("title", "Chính sách")
                sec_title = pol.metadata.get("section_title", "")
                with st.expander(f"📜 [{p_id}] {p_title} — {sec_title}"):
                    st.markdown(pol.text)


if __name__ == "__main__":
    main()
