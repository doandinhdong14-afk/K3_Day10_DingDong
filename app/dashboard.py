"""Streamlit dashboard cho Day 10 - Data Pipeline & Data Observability.

Chay:
    streamlit run app/dashboard.py

App chi DOC artifact trong data/ va nap lai ChromaDB collection da build san.
No khong chay lai pipeline, nen moi con so tren man hinh luon khop voi artifact.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from core.config import Settings, load_settings, require_llm_credentials  # noqa: E402
from retrieval.agent import build_agent  # noqa: E402
from retrieval.index import LocalEmbeddingIndex  # noqa: E402
from retrieval.qa import answer_question  # noqa: E402


STATES = ["baseline", "corrupted", "repaired"]

# Categorical slot 1-3 cua palette da validate (all-pairs pass o ca hai mode).
PALETTE_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a"]
PALETTE_DARK = ["#3987e5", "#d95926", "#199e70"]

METRICS = [
    ("retrieval_hit_rate", "Retrieval hit rate", "0-1"),
    ("mean_token_f1", "Mean token F1", "0-1"),
    ("judge_accuracy", "Judge accuracy", "0-1"),
    ("mean_judge_score", "Mean judge score", "1-5"),
]

st.set_page_config(page_title="Day 10 - Data Pipeline & Observability", layout="wide")


# ----------------------------------------------------------------------------
# Nap du lieu (cache de Streamlit khong doc lai file moi lan rerun)
# ----------------------------------------------------------------------------
@st.cache_resource
def get_settings() -> Settings:
    return load_settings(ROOT)


@st.cache_data(show_spinner=False)
def read_json_cached(path_str: str) -> Any:
    path = Path(path_str)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def read_csv_cached(path_str: str) -> pd.DataFrame | None:
    path = Path(path_str)
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def read_text_cached(path_str: str) -> str | None:
    path = Path(path_str)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def paths_for(settings: Settings, state: str) -> dict[str, Path]:
    """Gom duong dan artifact theo tung trang thai dataset."""
    p = settings.paths
    table = {
        "baseline": {
            "clean_csv": p.clean_csv,
            "embeddings": p.embeddings_json,
            "metrics": p.baseline_metrics,
            "answers": p.baseline_answers,
            "quality": p.quality_dir / "baseline_quality.json",
            "freshness": p.freshness_report,
        },
        "corrupted": {
            "clean_csv": p.corrupted_clean_csv,
            "embeddings": p.corrupted_embeddings_json,
            "metrics": p.corrupted_metrics,
            "answers": p.corrupted_answers,
            "quality": p.quality_dir / "corrupted_quality.json",
            "freshness": p.quality_dir / "freshness_report_corrupted.json",
        },
        "repaired": {
            "clean_csv": p.repaired_clean_csv,
            "embeddings": p.repaired_embeddings_json,
            "metrics": p.repaired_metrics,
            "answers": p.repaired_answers,
            "quality": p.quality_dir / "repaired_quality.json",
            "freshness": p.quality_dir / "freshness_report_repaired.json",
        },
    }
    return table[state]


@st.cache_resource(show_spinner="Dang nap ChromaDB collection...")
def get_index(state: str) -> LocalEmbeddingIndex:
    settings = get_settings()
    return LocalEmbeddingIndex.load(settings, paths_for(settings, state)["embeddings"])


@st.cache_resource(show_spinner="Dang khoi tao agent...")
def get_agent(state: str):
    settings = get_settings()
    return build_agent(settings, get_index(state))


def palette() -> list[str]:
    """Chon bo mau theo theme dang hien thi."""
    try:
        if st.context.theme.type == "dark":
            return PALETTE_DARK
    except Exception:
        pass
    return PALETTE_LIGHT


def message_text(content: Any) -> str:
    """Ep content LLM ve chuoi.

    Gemini bat thinking tra ve list content block chu khong phai str; khong gom
    lai thi UI se in ra JSON tho.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
        ]
        if parts:
            return "\n".join(parts)
    return str(content)


def missing(label: str, path: Path) -> None:
    st.warning(
        f"Thieu artifact **{label}**: `{path.name}`\n\n"
        "Hay chay `python script/run_phase1.py` roi `python script/run_corruption_flow.py`."
    )


# ----------------------------------------------------------------------------
settings = get_settings()

st.title("Day 10 — Data Pipeline & Data Observability")
st.caption(
    "Dashboard doc truc tiep tu `data/`. Moi con so deu lay tu artifact, khong go tay."
)

tabs = st.tabs(
    [
        "Tong quan",
        "Du lieu",
        "Chat luong",
        "Danh gia",
        "So sanh 3 trang thai",
        "RAG Chat",
        "Bao cao",
    ]
)


# ============================================================ TAB 1: Tong quan
with tabs[0]:
    metrics_baseline = read_json_cached(str(settings.paths.baseline_metrics))

    st.subheader("Ket qua baseline")
    if metrics_baseline:
        cols = st.columns(5)
        cols[0].metric("Samples", metrics_baseline.get("samples", "-"))
        for col, (key, label, _) in zip(cols[1:], METRICS, strict=False):
            value = metrics_baseline.get(key)
            col.metric(label, f"{value:.3f}" if isinstance(value, (int, float)) else "-")
    else:
        missing("baseline metrics", settings.paths.baseline_metrics)

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Nguon du lieu")
        clean_df = read_csv_cached(str(settings.paths.clean_csv))
        raw_records = read_json_cached(str(settings.paths.raw_records_json))
        source_rows = [
            ("Source API", settings.source_api),
            ("Query", settings.source_query),
            ("Filter", settings.source_filter),
            ("Max results", settings.max_results),
            ("Raw records", len(raw_records) if raw_records else "-"),
            ("Clean rows", len(clean_df) if clean_df is not None else "-"),
            ("Embedding model", settings.embedding_model),
            ("Top-k", settings.top_k),
            ("LLM provider", settings.llm_provider),
            ("LLM model", settings.model_name),
        ]
        st.dataframe(
            pd.DataFrame(
                [(k, str(v)) for k, v in source_rows], columns=["Truong", "Gia tri"]
            ),
            hide_index=True,
            width="stretch",
        )

    with right:
        st.subheader("Trang thai artifact")
        rows = [
            ("raw response", settings.paths.raw_api_response),
            ("raw records", settings.paths.raw_records_json),
            ("clean csv", settings.paths.clean_csv),
            ("embeddings manifest", settings.paths.embeddings_json),
            ("test set", settings.paths.eval_testset),
            ("baseline metrics", settings.paths.baseline_metrics),
            ("corrupted metrics", settings.paths.corrupted_metrics),
            ("repaired metrics", settings.paths.repaired_metrics),
            ("corruption log", settings.paths.corruption_log),
            ("quality baseline", settings.paths.quality_dir / "baseline_quality.json"),
            ("freshness", settings.paths.freshness_report),
            ("phase 1 report", settings.paths.baseline_report),
            ("corruption report", settings.paths.comparison_report),
        ]
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Artifact": label,
                        "Trang thai": "OK" if path.exists() else "THIEU",
                        "Duong dan": path.relative_to(ROOT).as_posix(),
                    }
                    for label, path in rows
                ]
            ),
            hide_index=True,
            width="stretch",
        )


# ============================================================= TAB 2: Du lieu
with tabs[1]:
    state = st.radio("Dataset", STATES, horizontal=True, key="data_state")
    csv_path = paths_for(settings, state)["clean_csv"]
    df = read_csv_cached(str(csv_path))

    if df is None:
        missing(f"clean dataset ({state})", csv_path)
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("So dong", len(df))
        c2.metric("So cot", len(df.columns))
        if "summary_chars" in df:
            c3.metric("Summary rong", int((df["summary_chars"].fillna(0) < 50).sum()))
        if "age_days" in df:
            c4.metric(
                f"Qua {settings.freshness_threshold_days} ngay",
                int((df["age_days"] > settings.freshness_threshold_days).sum()),
            )

        keyword = st.text_input("Loc theo tu khoa (title / summary / authors)", key="data_kw")
        view = df
        if keyword:
            mask = pd.Series(False, index=df.index)
            for column in ("title", "summary", "authors_joined"):
                if column in df:
                    mask |= df[column].astype(str).str.contains(keyword, case=False, na=False)
            view = df[mask]
            st.caption(f"{len(view)}/{len(df)} dong khop tu khoa.")

        display_cols = [
            c
            for c in ("paper_id", "title", "published", "age_days", "authors_joined", "summary_chars")
            if c in view.columns
        ]
        st.dataframe(view[display_cols], hide_index=True, width="stretch", height=320)

        st.subheader("Chi tiet bai bao")
        if len(view):
            titles = view["title"].astype(str).tolist()
            picked = st.selectbox("Chon bai", titles, key="data_pick")
            row = view[view["title"].astype(str) == picked].iloc[0]
            st.markdown(f"**{row.get('title', '')}**")
            meta_cols = st.columns(3)
            meta_cols[0].markdown(f"`paper_id` {row.get('paper_id', '')}")
            meta_cols[1].markdown(f"`published` {row.get('published', '')}")
            meta_cols[2].markdown(f"`age_days` {row.get('age_days', '')}")
            st.markdown(f"**Tac gia:** {row.get('authors_joined', '')}")
            st.markdown(f"**Categories:** {row.get('categories_joined', '')}")
            st.markdown(f"**Summary:** {row.get('summary', '')}")
            links = []
            if isinstance(row.get("abs_url"), str) and row["abs_url"]:
                links.append(f"[Trang bai bao]({row['abs_url']})")
            if isinstance(row.get("pdf_url"), str) and row["pdf_url"]:
                links.append(f"[PDF]({row['pdf_url']})")
            if links:
                st.markdown(" · ".join(links))
            with st.expander("text_for_embedding (doan thuc su duoc embed)"):
                st.text(row.get("text_for_embedding", ""))


# ========================================================== TAB 3: Chat luong
with tabs[2]:
    state = st.radio("Dataset", STATES, horizontal=True, key="quality_state")
    qpaths = paths_for(settings, state)
    quality = read_json_cached(str(qpaths["quality"]))
    freshness = read_json_cached(str(qpaths["freshness"]))

    if not quality:
        missing(f"quality report ({state})", qpaths["quality"])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tong check", quality.get("total_checks", "-"))
        c2.metric("Pass", quality.get("passed_checks", "-"))
        c3.metric("Fail", quality.get("failed_checks", "-"))
        c4.metric("Ket luan", "DAT" if quality.get("success") else "KHONG DAT")

        checks = quality.get("checks", [])
        if checks:
            check_df = pd.DataFrame(
                [
                    {
                        "Ket qua": "PASS" if c.get("passed") else "FAIL",
                        "Check": c.get("name", ""),
                        "Chieu": c.get("dimension", ""),
                        "Ky vong": c.get("expectation", ""),
                        "Quan sat": c.get("observed", ""),
                        "Dong loi": c.get("failed_rows", 0),
                    }
                    for c in checks
                ]
            )
            st.dataframe(
                check_df.style.apply(
                    lambda col: [
                        "background-color: rgba(227,73,72,0.18)" if v == "FAIL" else ""
                        for v in col
                    ],
                    subset=["Ket qua"],
                ),
                hide_index=True,
                width="stretch",
            )

    st.divider()
    st.subheader("Do tuoi du lieu")
    if not freshness:
        missing(f"freshness report ({state})", qpaths["freshness"])
    else:
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Moi nhat", freshness.get("latest_published", "-"))
        f2.metric("Cu nhat", freshness.get("oldest_published", "-"))
        f3.metric(
            "Dong qua han",
            f"{freshness.get('stale_rows', '-')}/{freshness.get('total_rows', '-')}",
        )
        f4.metric("Trang thai", "FRESH" if freshness.get("is_fresh") else "STALE")

        df_state = read_csv_cached(str(qpaths["clean_csv"]))
        if df_state is not None and "age_days" in df_state:
            hist = (
                alt.Chart(df_state[["age_days"]])
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=palette()[0])
                .encode(
                    x=alt.X("age_days:Q", bin=alt.Bin(maxbins=20), title="Tuoi bai bao (ngay)"),
                    y=alt.Y("count():Q", title="So bai"),
                    tooltip=[alt.Tooltip("count():Q", title="So bai")],
                )
                .properties(height=220)
            )
            rule = (
                alt.Chart(pd.DataFrame({"x": [settings.freshness_threshold_days]}))
                .mark_rule(color="#e34948", strokeDash=[6, 4], size=2)
                .encode(x="x:Q")
            )
            st.altair_chart(hist + rule, width="stretch")
            st.caption(
                f"Duong do = nguong freshness {settings.freshness_threshold_days} ngay."
            )


# ============================================================ TAB 4: Danh gia
with tabs[3]:
    state = st.radio("Dataset", STATES, horizontal=True, key="eval_state")
    epaths = paths_for(settings, state)
    metrics = read_json_cached(str(epaths["metrics"]))
    answers = read_json_cached(str(epaths["answers"]))

    if not metrics:
        missing(f"metrics ({state})", epaths["metrics"])
    else:
        cols = st.columns(5)
        cols[0].metric("Samples", metrics.get("samples", "-"))
        for col, (key, label, _) in zip(cols[1:], METRICS, strict=False):
            value = metrics.get(key)
            col.metric(label, f"{value:.3f}" if isinstance(value, (int, float)) else "-")

    if not answers:
        missing(f"answers ({state})", epaths["answers"])
    else:
        st.subheader(f"Chi tiet {len(answers)} cau hoi")
        only_wrong = st.checkbox("Chi hien cau bi judge cham la SAI", key="eval_wrong")
        rows = [
            {
                "id": a["id"],
                "Loai": a["question_type"],
                "Cau hoi": a["question"],
                "Dap an chuan": a["ground_truth"],
                "Agent tra loi": a["answer"],
                "Hit": "OK" if a["retrieval_hit"] else "MISS",
                "token_f1": round(a["token_f1"], 3),
                "Judge": a["judge"]["score"],
                "Dung?": "DUNG" if a["judge"]["correct"] else "SAI",
            }
            for a in answers
            if not only_wrong or not a["judge"]["correct"]
        ]
        if rows:
            answer_df = pd.DataFrame(rows)
            st.dataframe(
                answer_df.style.apply(
                    lambda col: [
                        "background-color: rgba(227,73,72,0.18)" if v in ("SAI", "MISS") else ""
                        for v in col
                    ],
                    subset=["Dung?", "Hit"],
                ),
                hide_index=True,
                width="stretch",
                height=380,
            )
        else:
            st.success("Khong co cau nao bi cham sai.")

        with st.expander("Xem context da truy xuat cho tung cau"):
            picked = st.selectbox("Chon cau hoi", [a["id"] for a in answers], key="eval_ctx")
            item = next(a for a in answers if a["id"] == picked)
            st.markdown(f"**Cau hoi:** {item['question']}")
            st.markdown(f"**Ground truth doc ids:** `{item['ground_truth_doc_ids']}`")
            st.markdown(f"**Retrieved doc ids:** `{item['retrieved_doc_ids']}`")
            st.markdown(f"**Judge reasoning:** {item['judge']['reasoning']}")
            for i, ctx in enumerate(item["retrieved_contexts"], start=1):
                st.text_area(f"context {i}", ctx, height=110, key=f"ctx_{picked}_{i}")


# ============================================================= TAB 5: So sanh
with tabs[4]:
    st.subheader("Baseline vs Corrupted vs Repaired")
    all_metrics = {s: read_json_cached(str(paths_for(settings, s)["metrics"])) for s in STATES}

    if not all(all_metrics.values()):
        st.warning(
            "Thieu metrics cua mot hoac nhieu trang thai. Chay `script/run_phase1.py` "
            "roi `script/run_corruption_flow.py` truoc."
        )
    else:
        long_rows = [
            {"Trang thai": s, "metric": label, "value": float(all_metrics[s][key])}
            for key, label, _ in METRICS
            for s in STATES
            if isinstance(all_metrics[s].get(key), (int, float))
        ]
        long_df = pd.DataFrame(long_rows)

        # Small multiples: moi metric mot truc rieng, tranh gop thang 0-1 va 1-5
        # len cung mot truc (dual-axis la loi kinh dien cua bieu do so sanh).
        base = alt.Chart(long_df).encode(
            x=alt.X("Trang thai:N", sort=STATES, title=None, axis=alt.Axis(labels=False, ticks=False)),
            y=alt.Y("value:Q", title=None),
            color=alt.Color(
                "Trang thai:N",
                sort=STATES,
                scale=alt.Scale(domain=STATES, range=palette()),
                legend=alt.Legend(title=None, orient="top", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("Trang thai:N", title="Trang thai"),
                alt.Tooltip("value:Q", title="Gia tri", format=".4f"),
            ],
        )
        bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=34)
        # Nhan so phai deo mau chu, khong duoc an mau series -> ghi de kenh color.
        labels = base.mark_text(dy=-8, fontSize=11).encode(
            text=alt.Text("value:Q", format=".3f"),
            color=alt.value("#52514e"),
        )
        chart = (
            alt.layer(bars, labels)
            .properties(width=150, height=200)
            .facet(column=alt.Column("metric:N", title=None, sort=[m[1] for m in METRICS]))
            .resolve_scale(y="independent")
        )
        st.altair_chart(chart, width="content")
        st.caption(
            "Moi metric co truc y rieng vi `mean_judge_score` thang 1-5, ba metric con lai thang 0-1."
        )

        st.subheader("Bang chenh lech")
        delta_rows = []
        for key, label, scale in METRICS:
            b = float(all_metrics["baseline"][key])
            c = float(all_metrics["corrupted"][key])
            r = float(all_metrics["repaired"][key])
            drop = (c - b) / b * 100 if b else 0.0
            delta_rows.append(
                {
                    "Metric": label,
                    "Thang": scale,
                    "Baseline": round(b, 4),
                    "Corrupted": round(c, 4),
                    "Repaired": round(r, 4),
                    "Corrupt vs baseline": f"{drop:+.1f}%",
                    "Repair hoi phuc": "hoan toan" if abs(r - b) < 1e-9 else f"{(r - c):+.4f}",
                }
            )
        st.dataframe(pd.DataFrame(delta_rows), hide_index=True, width="stretch")

        st.divider()
        st.subheader("Cau hoi nao bi hong sau corruption")
        ans_b = read_json_cached(str(paths_for(settings, "baseline")["answers"]))
        ans_c = read_json_cached(str(paths_for(settings, "corrupted")["answers"]))
        ans_r = read_json_cached(str(paths_for(settings, "repaired")["answers"]))
        if ans_b and ans_c:
            by_c = {a["id"]: a for a in ans_c}
            by_r = {a["id"]: a for a in (ans_r or [])}
            diff_rows = []
            for a in ans_b:
                c = by_c.get(a["id"])
                if not c or (a["judge"]["correct"] == c["judge"]["correct"] and a["retrieval_hit"] == c["retrieval_hit"]):
                    continue
                r = by_r.get(a["id"])
                diff_rows.append(
                    {
                        "id": a["id"],
                        "Loai": a["question_type"],
                        "Cau hoi": a["question"][:90] + "...",
                        "Baseline": a["answer"][:70],
                        "Corrupted": c["answer"][:70],
                        "Repaired": (r or {}).get("answer", "")[:70],
                        "F1 base": round(a["token_f1"], 3),
                        "F1 corrupt": round(c["token_f1"], 3),
                    }
                )
            if diff_rows:
                st.caption(f"{len(diff_rows)}/{len(ans_b)} cau doi ket qua sau khi lam hong du lieu.")
                st.dataframe(pd.DataFrame(diff_rows), hide_index=True, width="stretch")
            else:
                st.info("Khong cau nao doi ket qua — corruption chua cham vao truong ma QA doc.")

        st.divider()
        st.subheader("Cac buoc corruption da thuc hien")
        log = read_json_cached(str(settings.paths.corruption_log))
        if log:
            c1, c2, c3 = st.columns(3)
            c1.metric("Dong nguon", log.get("source_rows", "-"))
            c2.metric("Dong sau corrupt", log.get("result_rows", "-"))
            c3.metric("Tong dong bi anh huong", log.get("total_affected_rows", "-"))
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Buoc": s.get("name", ""),
                            "Mo ta": s.get("description", ""),
                            "Dong anh huong": s.get("affected_rows", 0),
                            "paper_id bi cham": ", ".join(s.get("affected_paper_ids", []))[:80],
                        }
                        for s in log.get("steps", [])
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        else:
            missing("corruption log", settings.paths.corruption_log)


# ============================================================ TAB 6: RAG Chat
with tabs[5]:
    st.subheader("Hoi truc tiep corpus")

    col1, col2, col3 = st.columns([1.2, 1.4, 1])
    chat_state = col1.selectbox("Corpus", STATES, key="chat_state")
    mode = col2.selectbox(
        "Che do",
        ["Agent (co LLM)", "Rule-based QA (khong LLM)", "Semantic search (khong LLM)"],
        key="chat_mode",
    )
    show_trace = col3.checkbox("Hien tool call", value=True, key="chat_trace")

    try:
        index = get_index(chat_state)
        st.caption(
            f"collection `{index.collection_name}` — {len(index.documents)} documents "
            f"| provider `{settings.llm_provider}` / `{settings.model_name}`"
        )
    except Exception as exc:
        index = None
        st.error(
            f"Khong nap duoc collection cho `{chat_state}` ({type(exc).__name__}).\n\n"
            "Hay chay lai pipeline de tao collection truoc."
        )

    history_key = f"chat_history_{chat_state}"
    display_key = f"chat_display_{chat_state}"
    st.session_state.setdefault(history_key, [])
    st.session_state.setdefault(display_key, [])

    if st.button("Xoa hoi thoai", key="chat_reset"):
        st.session_state[history_key] = []
        st.session_state[display_key] = []
        st.rerun()

    for turn in st.session_state[display_key]:
        with st.chat_message(turn["role"]):
            st.markdown(turn["text"])
            if turn.get("trace"):
                with st.expander("Tool call cua agent"):
                    for line in turn["trace"]:
                        st.code(line, language="text")

    question = st.chat_input("Nhap cau hoi ve corpus...")
    if question and index is not None:
        st.session_state[display_key].append({"role": "user", "text": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            if mode == "Semantic search (khong LLM)":
                results = index.search(question, top_k=settings.top_k)
                lines = [
                    f"{i}. `{r.score:.4f}` — **{r.title}**  \n   `{r.paper_id}`"
                    for i, r in enumerate(results, start=1)
                ]
                text = "\n".join(lines) if lines else "Khong tim thay ket qua."
                st.markdown(text)
                st.session_state[display_key].append({"role": "assistant", "text": text})

            elif mode == "Rule-based QA (khong LLM)":
                result = answer_question(question, settings=settings, index=index)
                text = (
                    f"{result.answer}\n\n"
                    f"*retrieved:* `{', '.join(result.retrieved_doc_ids)}`"
                )
                st.markdown(text)
                st.session_state[display_key].append({"role": "assistant", "text": text})

            else:
                try:
                    require_llm_credentials(settings)
                    agent = get_agent(chat_state)
                    history = st.session_state[history_key] + [
                        {"role": "user", "content": question}
                    ]
                    before = len(history)
                    with st.spinner("Agent dang goi tool..."):
                        result = agent.invoke({"messages": history})
                    messages = result.get("messages", [])
                    st.session_state[history_key] = list(messages)

                    trace: list[str] = []
                    for message in messages[before:]:
                        for call in getattr(message, "tool_calls", None) or []:
                            trace.append(f"TOOL CALL  {call['name']}({call.get('args')})")
                        if type(message).__name__ == "ToolMessage":
                            body = message_text(getattr(message, "content", ""))
                            trace.append(
                                f"TOOL OUT   {getattr(message, 'name', 'tool')}: "
                                f"{len(body)} chars\n{' '.join(body.split())[:400]}..."
                            )

                    text = message_text(getattr(messages[-1], "content", "")) if messages else ""
                    st.markdown(text)
                    if show_trace and trace:
                        with st.expander("Tool call cua agent"):
                            for line in trace:
                                st.code(line, language="text")
                    st.session_state[display_key].append(
                        {"role": "assistant", "text": text, "trace": trace if show_trace else []}
                    )
                except Exception as exc:
                    detail = str(exc)
                    hint = ""
                    if "rate_limit" in detail or "429" in detail or "413" in detail:
                        hint = (
                            "\n\nTool `semantic_search_papers` tra ve nguyen `text_for_embedding` "
                            "cua top_k bai (~9k token) nen de vuot han muc free tier. "
                            "Doi provider/model, hoac cat bot content trong `src/retrieval/agent.py`."
                        )
                    text = f"**Loi khi goi LLM** (`{type(exc).__name__}`): {detail[:400]}{hint}"
                    st.error(text)
                    st.session_state[display_key].append({"role": "assistant", "text": text})


# ============================================================= TAB 7: Bao cao
with tabs[6]:
    report_files = [
        ("Phase 1 — Baseline report", settings.paths.baseline_report),
        ("Phase 2 — Corruption & comparison report", settings.paths.comparison_report),
        ("Group report", ROOT / "report" / "group_report.md"),
        ("Individual report", ROOT / "report" / "individual_report.md"),
    ]
    available = [(label, path) for label, path in report_files if path.exists()]
    if not available:
        st.warning("Chua co bao cao nao. Chay pipeline de sinh `data/reports/`.")
    else:
        picked_label = st.selectbox("Chon bao cao", [label for label, _ in available])
        picked_path = dict(available)[picked_label]
        content = read_text_cached(str(picked_path))
        st.caption(f"Nguon: `{picked_path.relative_to(ROOT).as_posix()}`")
        st.download_button(
            "Tai file .md",
            content or "",
            file_name=picked_path.name,
            mime="text/markdown",
        )
        st.markdown(content or "")
