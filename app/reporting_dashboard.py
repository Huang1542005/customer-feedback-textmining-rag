"""P5 local dashboard. Reads P5 reports only; never runs upstream code."""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Feedback Observatory | P5", page_icon="◉", layout="wide")
st.markdown("""<style>
/* Leave all colors to Streamlit so light/dark themes stay consistent,
   including widgets, metric labels, the sidebar and Vega charts. */
.block-container {padding-top: 5rem; max-width: 1400px;}
h1, h2, h3 {letter-spacing: -.025em;}
[data-testid="stMetric"] {padding: 18px; border: 1px solid color-mix(in srgb, currentColor 20%, transparent); border-radius: 12px;}
</style>""", unsafe_allow_html=True)


def load_report(directory: Path):
    report = directory / "reports.json"
    evaluation = directory / "evaluation.json"
    if not report.is_file():
        return None, None
    payload = json.loads(report.read_text(encoding="utf-8"))
    checks = json.loads(evaluation.read_text(encoding="utf-8")) if evaluation.is_file() else None
    if payload.get("schema_version") != "1.0" or not isinstance(payload.get("reports"), list):
        raise ValueError("Unsupported reports.json schema")
    return payload, checks


def main() -> None:
    with st.sidebar:
        st.caption("CUSTOMER EXPERIENCE / P5")
        st.title("Feedback Observatory")
        st.write("Từ phản hồi đến hướng điều tra có bằng chứng.")
        directory = Path(st.text_input("Thư mục báo cáo", str(ROOT / "reports/p5")))
        st.caption("Dashboard chỉ đọc output đã tạo. Dữ liệu không được gửi đi khi xem báo cáo.")
        st.button("Đọc lại dữ liệu")
    st.caption("INSIGHTS & EVIDENCE")
    st.title("Hiểu vấn đề. Chọn việc cần làm.")
    st.write("Theo dõi mức ưu tiên, xu hướng và bằng chứng của từng nhóm phản hồi.")
    try:
        payload, checks = load_report(directory)
    except (ValueError, OSError) as error:
        st.error(f"Không đọc được báo cáo: {error}")
        return
    if payload is None:
        st.info("Chưa có output P5. Hãy tạo báo cáo từ các file P1–P4 trước.")
        st.code("python scripts/run_reporting.py --input-dir data/processed --output-dir reports/p5")
        return
    reports = payload["reports"]
    period = payload.get("review_period", {})
    if period.get("start"):
        st.caption(f"Kỳ dữ liệu lịch sử: {period['start']} → {period['end']}. Thời điểm tạo báo cáo không phải thời điểm phát sinh phản hồi.")
    provenance = payload.get("provenance", {})
    if provenance.get("raw_row_limit"):
        st.warning(f"Phạm vi: {provenance['raw_row_limit']:,} dòng đầu của CSV; P4 index tối đa {provenance.get('rag_review_limit', 'N/A')} review. Kết quả chưa đại diện cho toàn bộ dataset.")
    elif provenance.get("rag_review_limit"):
        st.info(f"Thống kê P1–P3 dùng toàn bộ CSV. Bằng chứng P4 chỉ truy xuất trong tối đa {provenance['rag_review_limit']:,} review đầu; chưa bao phủ toàn bộ phản hồi.")
    with st.sidebar:
        query = st.text_input("Tìm vấn đề / từ khóa")
        minimum = st.slider("Điểm ưu tiên tối thiểu", 0, 100, 0)
        evidence_only = st.checkbox("Chỉ hiện vấn đề có bằng chứng đã đối chiếu")
        st.download_button("Tải reports.json", json.dumps(payload, ensure_ascii=False, indent=2),
                           "reports.json", "application/json")
        if (directory / "reports.md").is_file():
            st.download_button("Tải báo cáo Markdown", (directory / "reports.md").read_text(encoding="utf-8"),
                               "reports.md", "text/markdown")
    selected = [r for r in reports if (r["priority_score"] or 0) >= minimum
                and query.casefold() in (r["label"] + " " + " ".join(r["top_terms"])).casefold()
                and (not evidence_only or any(c["verified"] for c in r["citations"]))]
    counts = payload["sentiment"]["counts"]
    a, b, c, d = st.columns(4)
    a.metric("Nhóm vấn đề", len(reports))
    b.metric("Review trong output", f"{sum(counts.values()):,}")
    c.metric("Phản hồi tiêu cực", f"{counts['negative']:,}")
    rate = (checks or {}).get("citation_resolution_rate")
    d.metric("Trích dẫn đối chiếu được", "N/A" if rate is None else f"{rate:.0%}")
    st.caption("Đối chiếu được = tìm thấy nguồn và đoạn trích; chưa chứng minh tính đúng của nhận định hoặc nguyên nhân.")
    tabs = st.tabs(["Tổng quan", "Điều tra vấn đề", "Đánh giá & nguồn dữ liệu"])
    with tabs[0]:
        analysis = payload.get("analyst_analysis")
        if analysis:
            st.subheader("Insight và hướng hành động")
            st.caption("Phân tích do trợ lý tổng hợp từ số liệu và nội dung bằng chứng; không gọi Gemini, chưa được thẩm định độc lập.")
            for finding in analysis["executive_findings"]:
                with st.expander(finding["title"], expanded=False):
                    st.write(finding["text"])
                    st.write("**Hành động đề xuất:** " + finding["action"])
                    if finding.get("citation_ids"):
                        st.caption("Nguồn: " + ", ".join(finding["citation_ids"]))
        left, right = st.columns([2, 1])
        with left:
            st.subheader("Ưu tiên xử lý")
            if selected:
                chart = pd.DataFrame([{"Vấn đề": f"#{r['rank']} {r['label']}", "Điểm ưu tiên": r["priority_score"]} for r in selected])
                priority_chart = alt.Chart(chart).mark_bar(color="#168c9a", cornerRadiusEnd=3).encode(
                    x=alt.X("Điểm ưu tiên:Q", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Vấn đề:N", sort=chart["Vấn đề"].tolist(),
                            axis=alt.Axis(labelLimit=230), title=None),
                    tooltip=["Vấn đề:N", alt.Tooltip("Điểm ưu tiên:Q", format=".1f")],
                ).properties(height=max(240, 30 * len(chart)))
                st.altair_chart(priority_chart, width="stretch")
            else:
                st.info("Không có vấn đề phù hợp bộ lọc.")
        with right:
            st.subheader("Phân bố cảm xúc")
            sentiment_labels = {"positive": "Tích cực", "neutral": "Trung lập",
                                "negative": "Tiêu cực", "unknown": "Chưa rõ"}
            sentiment = pd.DataFrame([{"Cảm xúc": sentiment_labels.get(key, key), "Reviews": count}
                                      for key, count in counts.items()])
            sentiment_chart = alt.Chart(sentiment).mark_bar(color="#df9c45", cornerRadiusEnd=3).encode(
                x=alt.X("Reviews:Q", title="Số review"),
                y=alt.Y("Cảm xúc:N", sort=list(sentiment_labels.values()), title=None),
                tooltip=["Cảm xúc:N", alt.Tooltip("Reviews:Q", format=",")],
            ).properties(height=max(240, 30 * len(selected)))
            st.altair_chart(sentiment_chart, width="stretch")
            st.caption("Nhãn có thể được quy đổi từ số sao. Đây không phải điểm đánh giá một mô hình sentiment độc lập.")
        st.dataframe(pd.DataFrame([{"Hạng": r["rank"], "Vấn đề": r["label"], "Ưu tiên": r["priority_score"],
                                    "Số phàn nàn": r["metrics"].get("n_reviews"),
                                    "Tăng trưởng P3": r["metrics"].get("growth_recent_vs_prev")} for r in selected]),
                     hide_index=True, width="stretch")
    with tabs[1]:
        if not selected:
            st.info("Không có vấn đề phù hợp bộ lọc.")
        else:
            index = st.selectbox("Chọn vấn đề", range(len(selected)),
                                 format_func=lambda i: f"#{selected[i]['rank']} — {selected[i]['label']}")
            report = selected[index]
            st.subheader(report["label"])
            authored = report.get("analyst_insight")
            if authored:
                st.subheader(authored["headline"])
                for observation in authored["observations"]:
                    st.write(observation["text"])
                    st.caption("Nguồn: " + ", ".join(observation["citation_ids"]))
                st.write("**Diễn giải:** " + authored["interpretation"])
                st.caption("Chưa thể kết luận: " + authored["uncertainty"])
                for action in authored["actions"]:
                    st.write("• " + action)
                st.divider()
            for fact in report["facts"]:
                st.write(fact["text"])
            for warning in report["warnings"]:
                st.warning(warning)
            if not authored:
                st.info(report["root_cause"])
                for recommendation in report["recommendations"]:
                    st.write(f"• {recommendation}")
            if report.get("llm_claims"):
                st.subheader("Giả thuyết do LLM tạo — cần duyệt")
                for claim in report["llm_claims"]:
                    st.write(claim["text"])
                    st.caption(", ".join(claim["citation_ids"]))
            if report["trends"]:
                trend = pd.DataFrame(report["trends"])
                if {"month", "monthly_share"}.issubset(trend.columns):
                    trend["monthly_share"] = pd.to_numeric(trend["monthly_share"], errors="coerce")
                    st.subheader("Tỷ trọng vấn đề theo tháng")
                    st.line_chart(trend.set_index("month")[["monthly_share"]], color="#087e8b")
                with st.expander("Bảng xu hướng P2"):
                    st.dataframe(trend, hide_index=True)
            st.subheader("Bằng chứng và trích dẫn")
            st.caption("P3 examples là review đại diện; P4 output là kết quả truy xuất. Hai nguồn được ghi riêng.")
            for citation in report["citations"]:
                label = "Đã đối chiếu nguồn" if citation["verified"] else "Chưa xác minh"
                with st.expander(f"{citation['id']} · {label} · {citation['origin']}"):
                    st.text(citation["quote"] or "Không có nội dung nguồn")
                    st.caption(f"Nguồn: {citation['source_file']} | {citation['reason']}")
            if report.get("upstream_narrative"):
                with st.expander("Nhận định từ output cũ — chưa đánh giá tính đúng"):
                    st.text(report["upstream_narrative"])
    with tabs[2]:
        st.subheader("Phạm vi kiểm tra")
        st.write("P5 kiểm tra liên kết artifact và nguồn trích dẫn. Chưa có nhãn relevance để tính Recall@k/MRR, hoặc nhãn chuẩn để đánh giá sentiment và độ đúng của insight.")
        if checks:
            st.json(checks)
            st.download_button("Tải evaluation.json", json.dumps(checks, ensure_ascii=False, indent=2), "evaluation.json", "application/json")
        else:
            st.warning("Chưa có evaluation.json.")
        st.subheader("Phạm vi chạy upstream")
        st.json(payload.get("provenance", {}))
        st.subheader("Manifest đầu vào")
        st.dataframe(pd.DataFrame(payload["input_manifest"]), hide_index=True, width="stretch")
        for warning in payload["warnings"]:
            st.warning(warning)
        st.caption(f"Báo cáo được tạo lúc {payload['generated_at']} (UTC).")


if __name__ == "__main__":
    main()
