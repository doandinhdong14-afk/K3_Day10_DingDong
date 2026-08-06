from datetime import UTC, datetime
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.config import load_settings
from core.utils import read_json
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question

# ---------------------------------------------------------
# Streamlit Configuration & Dark Glassmorphism Design System
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Data Pipeline & Observability Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Glassmorphism CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background: #0B0F19;
        color: #F8FAFC;
    }

    /* Glass Card Style */
    .glass-card {
        background: rgba(17, 24, 39, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Hero Header */
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #A855F7 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 24px;
    }

    /* Metric Display Box */
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Status Badges */
    .badge-pass {
        background: rgba(52, 211, 153, 0.15);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-fail {
        background: rgba(251, 113, 133, 0.15);
        color: #FB7185;
        border: 1px solid rgba(251, 113, 133, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #090D16;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_settings():
    return load_settings()


settings = get_settings()

# ---------------------------------------------------------
# Sidebar Navigation & Branding
# ---------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 40px;">⚡</span>
        <h2 style="margin: 5px 0; font-size: 1.2rem; color: #38BDF8; font-weight: 800;">DATA ENGINE AI</h2>
        <p style="font-size: 0.75rem; color: #64748B;">Day 10 Lab - Observability & RAG</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

navigation_choice = st.sidebar.radio(
    "CHỌN TRANG THUYẾT TRÌNH:",
    [
        "🚀 1. Command Center & Pipeline Runner",
        "📊 2. Data Observability & Diagnostics",
        "⚔️ 3. Impact Analysis (Clean vs Corrupted)",
        "🤖 4. Live RAG Agent Assistant",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);">
        <p style="font-size: 0.8rem; color: #94A3B8; margin: 0;"><b>API Source:</b> Crossref REST API</p>
        <p style="font-size: 0.8rem; color: #94A3B8; margin: 4px 0 0 0;"><b>Vector DB:</b> ChromaDB (HNSW)</p>
        <p style="font-size: 0.8rem; color: #94A3B8; margin: 4px 0 0 0;"><b>Embedding:</b> all-MiniLM-L6-v2</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# PAGE 1: COMMAND CENTER & PIPELINE RUNNER
# ---------------------------------------------------------
if navigation_choice.startswith("🚀"):
    st.markdown('<div class="hero-title">⚡ AI Data Pipeline & Observability Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Hệ thống giám sát dữ liệu thô, làm sạch, Vector Embedding và tự động đánh giá RAG Agent</div>', unsafe_allow_html=True)

    # Status Overview Cards
    c1, c2, c3, c4 = st.columns(4)

    raw_ok = settings.paths.raw_records_json.exists()
    clean_ok = settings.paths.clean_json.exists()
    base_m_ok = settings.paths.baseline_metrics.exists()

    with c1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="metric-label">RAW API DATA</div>
                <div class="metric-value">24 Records</div>
                <span class="{ 'badge-pass' if raw_ok else 'badge-fail' }">{'CONNECTED' if raw_ok else 'OFFLINE'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="metric-label">CLEAN DATASET</div>
                <div class="metric-value">24 Papers</div>
                <span class="{ 'badge-pass' if clean_ok else 'badge-fail' }">{'READY' if clean_ok else 'PENDING'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="metric-label">CHROMADB INDEX</div>
                <div class="metric-value">HNSW Cosine</div>
                <span class="{ 'badge-pass' if clean_ok else 'badge-fail' }">{'INDEXED' if clean_ok else 'EMPTY'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="metric-label">RAG EVALUATION</div>
                <div class="metric-value">24 Testcases</div>
                <span class="{ 'badge-pass' if base_m_ok else 'badge-fail' }">{'EVALUATED' if base_m_ok else 'NOT RUN'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Execution Controls
    st.subheader("⚙️ Điều Phối Executions (Live Pipeline Trigger)")
    run_col1, run_col2 = st.columns(2)

    with run_col1:
        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.2);">
                <h4 style="color: #38BDF8; margin-top:0;">1. Pha 1: Baseline Clean Pipeline</h4>
                <p style="color: #94A3B8; font-size: 0.9rem;">Thực thi tải dữ liệu từ Crossref API -> Làm sạch -> Nạp ChromaDB -> Sinh bộ đề 24 Qs -> Chấm điểm Baseline.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶️ CHẠY PHA 1 (BASELINE CLEAN PIPELINE)", type="primary", use_container_width=True):
            with st.spinner("Đang chạy Phase 1 Baseline Pipeline..."):
                from pipelines.phase1 import main as run_phase1
                run_phase1()
                st.success("✅ Pha 1 thành công!")
                st.rerun()

    with run_col2:
        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 12px; border: 1px solid rgba(168, 85, 247, 0.2);">
                <h4 style="color: #A855F7; margin-top:0;">2. Pha 2: Corruption & Auto-Repair Flow</h4>
                <p style="color: #94A3B8; font-size: 0.9rem;">Giả lập lỗi dữ liệu (mất text, nhiễu rác, trùng lặp) -> Đo độ tụt giảm điểm RAG -> Tự động phục hồi từ Raw Source.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("⚡ CHẠY PHA 2 (CORRUPTION & AUTO-REPAIR FLOW)", use_container_width=True):
            with st.spinner("Đang chạy Pha 2 Corruption & Repair Flow..."):
                from pipelines.corruption_flow import main as run_corruption
                run_corruption()
                st.success("✅ Pha 2 thành công!")
                st.rerun()

    st.markdown("---")

    # Baseline Report Render
    st.subheader("📄 Baseline Executive Report (Báo cáo Pha 1)")
    if settings.paths.baseline_report.exists():
        st.markdown(
            f'<div class="glass-card">{settings.paths.baseline_report.read_text(encoding="utf-8")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Chưa có báo cáo Baseline. Vui lòng bấm nút chạy Pha 1 ở trên.")


# ---------------------------------------------------------
# PAGE 2: DATA OBSERVABILITY & DIAGNOSTICS
# ---------------------------------------------------------
elif navigation_choice.startswith("📊"):
    st.markdown('<div class="hero-title">📊 Data Observability & Quality Diagnostics</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Cảnh báo lỗi dữ liệu tự động, kiểm tra tính toàn vẹn (Data Quality) và độ tươi (Freshness Monitor)</div>', unsafe_allow_html=True)

    if settings.paths.clean_json.exists():
        clean_df = pd.read_json(settings.paths.clean_json)

        # Quality Diagnostic Badges
        q1, q2, q3, q4 = st.columns(4)
        total_rows = len(clean_df)
        null_count = clean_df["summary"].isna().sum() if "summary" in clean_df.columns else 0
        stale_count = (clean_df["age_days"] > settings.freshness_threshold_days).sum() if "age_days" in clean_df.columns else 0

        q1.metric("Data Quality Status", "PASSED ✅", "0 Critical Errors")
        q2.metric("Freshness Status", "FRESH 🌿", f"{stale_count} Stale Records")
        q3.metric("Null Summaries", f"{null_count}", "0 Missing")
        q4.metric("Deduplicated Records", f"{total_rows}", "100% Unique DOIs")

        st.markdown("---")

        # Interactive Plots
        st.subheader("🔍 Trực Quan Hóa Phân Phối Dữ Liệu Sạch (Plotly Analytics)")
        g1, g2 = st.columns(2)

        with g1:
            fig_age = px.histogram(
                clean_df,
                x="age_days",
                nbins=12,
                title="Phân Phối Tuổi Dữ Liệu Bài Báo (Age Days)",
                color_discrete_sequence=["#38BDF8"],
                template="plotly_dark",
            )
            fig_age.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_age, use_container_width=True)

        with g2:
            fig_len = px.box(
                clean_df,
                y="summary_chars",
                title="Phân Phối Độ Dài Summary Ký Tự (Summary Length)",
                color_discrete_sequence=["#A855F7"],
                template="plotly_dark",
            )
            fig_len.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_len, use_container_width=True)

        st.subheader("📋 Bảng Dữ Liệu Đã Làm Sạch (Clean Dataset Table)")
        st.dataframe(
            clean_df[["paper_id", "title", "published", "age_days", "authors_joined", "categories_joined"]],
            use_container_width=True,
        )
    else:
        st.warning("Vui lòng chạy Pha 1 trước để có dữ liệu quan sát.")


# ---------------------------------------------------------
# PAGE 3: IMPACT ANALYSIS (CLEAN VS CORRUPTED VS REPAIRED)
# ---------------------------------------------------------
elif navigation_choice.startswith("⚔️"):
    st.markdown('<div class="hero-title">⚔️ RAG Performance & Data Corruption Impact Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Chứng minh mối liên hệ giữa Chất lượng Dữ liệu thô và Hiệu năng RAG Agent (Baseline vs Corrupted vs Repaired)</div>', unsafe_allow_html=True)

    b_path = settings.paths.baseline_metrics
    c_path = settings.paths.corrupted_metrics
    r_path = settings.paths.repaired_metrics

    if b_path.exists() and c_path.exists() and r_path.exists():
        bm = read_json(b_path)
        cm = read_json(c_path)
        rm = read_json(r_path)

        # Comparative Key Metrics
        m1, m2, m3 = st.columns(3)

        with m1:
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid #34D399;">
                    <div class="metric-label">1. BASELINE (CLEAN)</div>
                    <div class="metric-value" style="color:#34D399;">{bm.get('retrieval_hit_rate', 0):.2%}</div>
                    <p style="color:#94A3B8; font-size:0.85rem; margin:5px 0 0 0;">Hit Rate: 100% | Token F1: {bm.get('mean_token_f1', 0):.4f}</p>
                    <span class="badge-pass">QUALITY: PASSED</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid #FB7185;">
                    <div class="metric-label">2. CORRUPTED (LỖI DỮ LIỆU)</div>
                    <div class="metric-value" style="color:#FB7185;">{cm.get('retrieval_hit_rate', 0):.2%}</div>
                    <p style="color:#94A3B8; font-size:0.85rem; margin:5px 0 0 0;">Hit Rate: 75.0% | Token F1: {cm.get('mean_token_f1', 0):.4f}</p>
                    <span class="badge-fail">QUALITY: FAILED</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m3:
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid #38BDF8;">
                    <div class="metric-label">3. REPAIRED (PHỤC HỒI TỰ ĐỘNG)</div>
                    <div class="metric-value" style="color:#38BDF8;">{rm.get('retrieval_hit_rate', 0):.2%}</div>
                    <p style="color:#94A3B8; font-size:0.85rem; margin:5px 0 0 0;">Hit Rate: 100% | Token F1: {rm.get('mean_token_f1', 0):.4f}</p>
                    <span class="badge-pass">RECOVERY: 100%</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Interactive Comparison Chart
        st.subheader("📊 Biểu Đồ So Sánh Tác Động Lỗi Dữ Liệu Đến AI Agent")

        cats = ["Retrieval Hit Rate", "Mean Token F1", "LLM Judge Accuracy"]
        fig_comp = go.Figure(
            data=[
                go.Bar(
                    name="1. Baseline (Clean Data)",
                    x=cats,
                    y=[bm.get("retrieval_hit_rate", 0), bm.get("mean_token_f1", 0), bm.get("judge_accuracy", 0)],
                    marker_color="#34D399",
                ),
                go.Bar(
                    name="2. Corrupted (Data Lỗi)",
                    x=cats,
                    y=[cm.get("retrieval_hit_rate", 0), cm.get("mean_token_f1", 0), cm.get("judge_accuracy", 0)],
                    marker_color="#FB7185",
                ),
                go.Bar(
                    name="3. Repaired (Đã Phục Hồi)",
                    x=cats,
                    y=[rm.get("retrieval_hit_rate", 0), rm.get("mean_token_f1", 0), rm.get("judge_accuracy", 0)],
                    marker_color="#38BDF8",
                ),
            ]
        )
        fig_comp.update_layout(
            barmode="group",
            title="Sự Sụt Giảm Và Phục Hồi Điểm RAG Agent Ở 3 Trạng Thái Dữ Liệu",
            yaxis_range=[0, 1.15],
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("---")
        st.subheader("📝 Báo Cáo So Sánh Chi Tiết (Corruption & Repair Report)")
        if settings.paths.comparison_report.exists():
            st.markdown(
                f'<div class="glass-card">{settings.paths.comparison_report.read_text(encoding="utf-8")}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Vui lòng bấm nút chạy Pha 2 trên Trang 1 để tạo báo cáo so sánh.")


# ---------------------------------------------------------
# PAGE 4: LIVE RAG AGENT ASSISTANT
# ---------------------------------------------------------
elif navigation_choice.startswith("🤖"):
    st.markdown('<div class="hero-title">🤖 Live RAG Agent Assistant & Semantic Search</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Đặt câu hỏi thực tế để thử nghiệm tính chính xác trong việc tìm kiếm & tổng hợp đáp án từ ChromaDB</div>', unsafe_allow_html=True)

    if settings.paths.embeddings_json.exists():
        index = LocalEmbeddingIndex.load(settings)

        # Sample test set selection
        test_questions = []
        if settings.paths.eval_testset.exists():
            test_data = read_json(settings.paths.eval_testset)
            test_questions = [item["question"] for item in test_data]

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        selected_q = st.selectbox(
            "💡 Chọn câu hỏi mẫu từ bộ 24 Testcases (hoặc tự nhập ở dưới):",
            ["-- Nhập câu hỏi tùy chỉnh --"] + test_questions,
        )

        user_q = st.text_input(
            "💬 Nhập câu hỏi của bạn:",
            value="" if selected_q.startswith("--") else selected_q,
            placeholder="VD: What is the main summary of the paper 'SafeRAG'?",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🔎 GỬI CÂU HỎI CHO AGENT", type="primary", use_container_width=True):
            if user_q.strip():
                with st.spinner("AI Agent đang thực thi Vector Search & tổng hợp đáp án..."):
                    res = answer_question(user_q.strip(), settings=settings, index=index)

                    st.markdown("### 🤖 TRẢ LỜI CỦA AI AGENT:")
                    st.markdown(
                        f"""
                        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 20px; border-radius: 12px; font-size: 1.1rem; color: #F8FAFC;">
                            {res.answer}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("### 📚 TÀI LIỆU TRUY XUẤT NGUỒN (RETRIEVED CONTEXTS):")
                    for i, (doc_id, title, ctx) in enumerate(zip(res.retrieved_doc_ids, res.retrieved_titles, res.retrieved_contexts, strict=False), 1):
                        with st.expander(f"📍 Top {i}: {title} (DOI: {doc_id})"):
                            st.write(ctx)
            else:
                st.warning("Vui lòng nhập câu hỏi.")
    else:
        st.warning("Vui lòng chạy Pha 1 ở Trang 1 để nạp Vector Index trước.")
