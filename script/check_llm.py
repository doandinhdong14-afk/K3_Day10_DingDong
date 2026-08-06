"""Kiem tra nhanh LLM provider trong .env truoc khi chay pipeline.

Chay:  python script/check_llm.py

Script kiem tra 3 kha nang ma pipeline thuc su can:
  1. Goi chat binh thuong            -> dung o buoc demo agent
  2. Structured output (Pydantic)    -> dung o LLM judge trong evaluation/metrics.py
  3. Tool calling                    -> dung o retrieval/agent.py

Neu buoc 2 that bai thi evaluation van chay duoc nhung se roi ve giam khao du phong
(heuristic), diem judge_* se khong con y nghia.
"""

from __future__ import annotations

import sys
import time

from pydantic import BaseModel, Field

from core.config import load_settings, normalized_provider, require_llm_credentials
from retrieval.llm import build_llm


class _Verdict(BaseModel):
    score: int = Field(ge=1, le=5)
    correct: bool
    reasoning: str


def _report(step: str, ok: bool, detail: str, elapsed: float) -> None:
    status = "OK  " if ok else "LOI "
    print(f"  [{status}] {step:<22} {elapsed:5.1f}s  {detail}")


def main() -> int:
    settings = load_settings()
    provider = normalized_provider(settings)

    print("=" * 66)
    print("KIEM TRA LLM PROVIDER")
    print("=" * 66)
    print(f"  LLM_PROVIDER = {settings.llm_provider}  (chuan hoa: {provider})")
    print(f"  LLM_MODEL    = {settings.model_name}")
    if provider == "groq":
        print(f"  GROQ_BASE_URL = {settings.groq_base_url}")
    print()

    try:
        require_llm_credentials(settings)
        print("  [OK  ] credentials           co du API key cho provider nay")
    except RuntimeError as exc:
        print(f"  [LOI ] credentials           {exc}")
        print("\n  -> Mo file .env va dien API key cho provider dang chon.")
        return 1

    failures = 0

    start = time.time()
    try:
        llm = build_llm(settings=settings, temperature=0.0)
        response = llm.invoke("Reply with exactly one word: OK")
        text = getattr(response, "content", response)
        _report("chat binh thuong", True, f"tra loi = {str(text)[:40]!r}", time.time() - start)
    except Exception as exc:
        failures += 1
        _report("chat binh thuong", False, f"{type(exc).__name__}: {exc}"[:110], time.time() - start)
        print("\n  -> Provider khong goi duoc. Kiem tra API key, ten model va ket noi mang.")
        return 1

    start = time.time()
    try:
        verdict = build_llm(settings=settings, temperature=0.0).with_structured_output(_Verdict).invoke(
            "Question: 2+2? Reference answer: 4. Model answer: 4. "
            "Return score 1-5, correct, and a short reasoning."
        )
        _report("structured output", True, f"score={verdict.score} correct={verdict.correct}", time.time() - start)
    except Exception as exc:
        failures += 1
        _report("structured output", False, f"{type(exc).__name__}: {exc}"[:110], time.time() - start)

    start = time.time()
    try:
        from langchain.tools import tool

        @tool
        def get_paper_count() -> str:
            """Return how many papers are in the local corpus."""
            return "24"

        bound = build_llm(settings=settings, temperature=0.0).bind_tools([get_paper_count])
        result = bound.invoke("How many papers are in the local corpus? Use the tool.")
        calls = getattr(result, "tool_calls", []) or []
        ok = bool(calls)
        detail = f"tool_calls = {[c.get('name') for c in calls]}" if ok else "model khong goi tool"
        if not ok:
            failures += 1
        _report("tool calling", ok, detail, time.time() - start)
    except Exception as exc:
        failures += 1
        _report("tool calling", False, f"{type(exc).__name__}: {exc}"[:110], time.time() - start)

    print()
    if failures == 0:
        print("  KET LUAN: provider san sang, chay duoc ca hai pipeline.")
        return 0

    print(f"  KET LUAN: {failures} kha nang that bai.")
    print("  - structured output hong -> judge_accuracy/mean_judge_score se dung giam khao du phong.")
    print("  - tool calling hong      -> buoc demo agent o cuoi phase 1 se bi bo qua.")
    print("  - Doi sang model khac trong .env (vi du openai/gpt-oss-120b) roi chay lai script nay.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
