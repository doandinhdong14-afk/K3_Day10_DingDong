# Phase 1 Baseline Data Pipeline & Observability Report

## 1. Source Summary
- **Source API**: Crossref REST API
- **Query**: `agentic retrieval augmented generation large language model`
- **Filter**: `from-pub-date:2026-02-07,has-abstract:true`
- **Raw Records Fetched**: 24
- **Cleaned Records**: 24

## 2. RAG Baseline Evaluation Metrics
- **Total Test Samples**: 24
- **Retrieval Hit Rate**: 1.0000
- **Mean Token F1**: 0.4389
- **LLM Judge Accuracy**: 0.3750
- **Mean LLM Judge Score**: 2.42 / 5.0

## 3. Data Quality Observability
- **Quality Checks Status**: `PASSED`
- **Total Rows Analyzed**: 24
- **Missing Paper IDs**: 0
- **Duplicate Paper IDs**: 0
- **Missing Titles**: 0
- **Missing/Empty Summaries**: 0
- **Short Summaries (< 20 chars)**: 0

## 4. Freshness Monitoring Report
- **Freshness Status**: `FRESH`
- **Latest Publication Date**: 2026-08-05
- **Oldest Publication Date**: 2026-02-13
- **Stale Rows (> 180 days)**: 0
- **Fresh Ratio**: 100.0%
