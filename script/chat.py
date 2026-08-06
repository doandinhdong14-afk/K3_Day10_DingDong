"""CLI chat de test agent tren terminal.

Vi du:
    python script/chat.py                        # chat voi corpus baseline
    python script/chat.py --dataset corrupted    # chat voi corpus da bi lam hong
    python script/chat.py --trace                # bat che do hien tool call
    python script/chat.py --ask "Who authored ...?"   # hoi mot cau roi thoat
"""
from __future__ import annotations

import argparse
from typing import Any

from core.config import Settings, load_settings, require_llm_credentials
from retrieval.agent import build_agent
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


DATASETS = ("baseline", "corrupted", "repaired")

HELP_TEXT = """
Lenh trong chat:
  /help              hien huong dan nay
  /trace             bat/tat che do hien tool call cua agent
  /reset             xoa lich su hoi thoai
  /dataset <ten>     doi corpus: baseline | corrupted | repaired
  /search <query>    tim kiem thuan embedding, KHONG goi LLM (mien phi)
  /qa <cau hoi>      chay duong rule-based trong qa.py, KHONG goi LLM (mien phi)
  /quit              thoat
Go cau hoi binh thuong de chat voi agent.
""".strip()


def _embeddings_path(settings: Settings, dataset: str):
    """Map ten dataset sang file manifest embedding tuong ung."""
    return {
        "baseline": settings.paths.embeddings_json,
        "corrupted": settings.paths.corrupted_embeddings_json,
        "repaired": settings.paths.repaired_embeddings_json,
    }[dataset]


def _load_index(settings: Settings, dataset: str) -> LocalEmbeddingIndex:
    """Nap lai collection da build san. Bao loi ro rang neu chua chay pipeline."""
    path = _embeddings_path(settings, dataset)
    if not path.exists():
        raise SystemExit(
            f"Thieu manifest embedding: {path}\n"
            f"Hay chay truoc: python script/run_phase1.py"
            + ("" if dataset == "baseline" else " roi python script/run_corruption_flow.py")
        )
    return LocalEmbeddingIndex.load(settings, path)


def message_text(content: Any) -> str:
    """Ep content cua LLM ve chuoi.

    Gemini bat thinking tra ve list content block thay vi str, nen phai gom
    cac block type=text lai; neu khong UI/console se in ra JSON tho.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if text:
                    parts.append(str(text))
        if parts:
            return "\n".join(parts)
    return str(content)


def _print_trace(messages: list[Any], start: int) -> None:
    """In cac tool call va ket qua tool phat sinh trong luot vua roi."""
    for message in messages[start:]:
        for call in getattr(message, "tool_calls", None) or []:
            print(f"    [tool call] {call['name']}({call.get('args')})")
        if type(message).__name__ == "ToolMessage":
            text = message_text(getattr(message, "content", ""))
            preview = " ".join(text.split())
            name = getattr(message, "name", "tool")
            print(f"    [tool out ] {name}: {len(text)} chars | {preview[:160]}...")


def _cmd_search(index: LocalEmbeddingIndex, query: str, top_k: int) -> None:
    """Tim kiem thuan embedding de kiem tra retrieval ma khong ton API call."""
    results = index.search(query, top_k=top_k)
    if not results:
        print("  (khong tim thay ket qua)")
        return
    for rank, result in enumerate(results, start=1):
        print(f"  {rank}. score={result.score:.4f} | {result.paper_id}")
        print(f"     {result.title[:100]}")


def _cmd_qa(settings: Settings, index: LocalEmbeddingIndex, question: str) -> None:
    """Chay duong rule-based trong qa.py - dung de doi chieu voi agent."""
    result = answer_question(question, settings=settings, index=index)
    print(f"  answer   : {result.answer}")
    print(f"  doc_ids  : {result.retrieved_doc_ids}")


def _explain_error(exc: Exception) -> str:
    """Doi loi API thanh goi y hanh dong thay vi traceback 40 dong."""
    text = str(exc)
    if "rate_limit" in text or "429" in text or "413" in text:
        return (
            "  Provider tu choi vi qua han muc token/phut.\n"
            "  Tool semantic_search_papers tra ve nguyen text_for_embedding cua top_k bai\n"
            "  (~9k token) nen de vuot han muc cua cac free tier nho.\n"
            "  Cach xu ly: doi provider (vi du LLM_PROVIDER=gemini), doi model co han muc cao hon,\n"
            "  hoac cat bot do dai content trong tool o src/retrieval/agent.py."
        )
    return f"  Chi tiet: {text[:500]}"


def _ask_agent(agent: Any, history: list[Any], question: str, trace: bool) -> list[Any]:
    """Goi agent voi ca lich su hoi thoai va tra ve lich su moi."""
    history = history + [{"role": "user", "content": question}]
    before = len(history)
    result = agent.invoke({"messages": history})
    messages = result.get("messages", [])
    if trace:
        _print_trace(messages, before)
    if not messages:
        print("agent: (khong co phan hoi)")
        return history
    print(f"agent: {message_text(getattr(messages[-1], 'content', ''))}")
    return list(messages)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat voi paper corpus agent tren terminal.")
    parser.add_argument("--dataset", choices=DATASETS, default="baseline", help="corpus dung de tra loi")
    parser.add_argument("--trace", action="store_true", help="hien tool call cua agent")
    parser.add_argument("--top-k", type=int, default=None, help="so ket qua cho lenh /search")
    parser.add_argument("--ask", default=None, help="hoi mot cau roi thoat, khong vao che do chat")
    args = parser.parse_args()

    settings = load_settings()
    require_llm_credentials(settings)

    dataset = args.dataset
    index = _load_index(settings, dataset)
    agent = build_agent(settings, index)
    top_k = args.top_k or settings.top_k
    trace = args.trace
    history: list[Any] = []

    if args.ask:
        try:
            _ask_agent(agent, history, args.ask, trace)
        except Exception as exc:
            print(f"LOI khi goi LLM ({type(exc).__name__}):")
            print(_explain_error(exc))
            raise SystemExit(1) from None
        return

    print("=" * 72)
    print("PAPER CORPUS AGENT - CHAT CLI")
    print("=" * 72)
    print(f"  dataset  : {dataset} ({index.collection_name}, {len(index.documents)} documents)")
    print(f"  provider : {settings.llm_provider} | model: {settings.model_name}")
    print(f"  trace    : {'ON' if trace else 'OFF'}")
    print("  go /help de xem cac lenh, /quit de thoat")
    print("=" * 72)

    while True:
        try:
            line = input("\nban> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nthoat.")
            return
        if not line:
            continue

        if line in {"/quit", "/exit", "/q"}:
            print("thoat.")
            return
        if line == "/help":
            print(HELP_TEXT)
            continue
        if line == "/trace":
            trace = not trace
            print(f"  trace = {'ON' if trace else 'OFF'}")
            continue
        if line == "/reset":
            history = []
            print("  da xoa lich su hoi thoai")
            continue
        if line.startswith("/dataset"):
            name = line.removeprefix("/dataset").strip()
            if name not in DATASETS:
                print(f"  ten khong hop le. Chon mot trong: {', '.join(DATASETS)}")
                continue
            try:
                index = _load_index(settings, name)
            except SystemExit as exc:
                print(f"  {exc}")
                continue
            dataset = name
            agent = build_agent(settings, index)
            history = []
            print(f"  da doi sang {dataset} ({index.collection_name}, {len(index.documents)} documents)")
            continue
        if line.startswith("/search"):
            query = line.removeprefix("/search").strip()
            if query:
                _cmd_search(index, query, top_k)
            continue
        if line.startswith("/qa"):
            question = line.removeprefix("/qa").strip()
            if question:
                _cmd_qa(settings, index, question)
            continue
        if line.startswith("/"):
            print("  lenh khong ro, go /help")
            continue

        try:
            history = _ask_agent(agent, history, line, trace)
        except Exception as exc:  # rate limit / mat mang -> giu phien chat song
            print(f"  LOI khi goi LLM ({type(exc).__name__}):")
            print(_explain_error(exc))


if __name__ == "__main__":
    main()
