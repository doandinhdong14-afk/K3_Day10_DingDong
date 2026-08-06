# Doi chieu cau tra loi cua agent theo trang thai du lieu

_Generated: 2026-08-06 05:57:02 UTC_

## 1. Tong quan

- Tong so cau hoi: **20** (cung mot evaluation set cho ca ba trang thai).
- So cau bi DOI cau tra loi khi du lieu bi corrupt: **7/20**.
- So cau QUAY VE dung cau tra loi baseline sau khi repair: **7/7**.

## 2. Cac cau co output khac nhau

### q001 - loai `authors`

**Cau hoi:** Who authored the paper 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation'?

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | Dr. Sumalatha P, Manoj Kumar | judge 1/5, F1 0.0000, tim dung bai: khong |
| Repaired (da sua) | Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li | judge 5/5, F1 1.0000, tim dung bai: co |

### q002 - loai `date`

**Cau hoi:** When was the paper 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generation' published?

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | 2026-08-01 | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | 2026-06-02 | judge 1/5, F1 0.0000, tim dung bai: khong |
| Repaired (da sua) | 2026-08-01 | judge 5/5, F1 1.0000, tim dung bai: co |

### q003 - loai `categories`

**Cau hoi:** What categories are assigned to the paper 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generati...

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | SPE Journal, journal article, Society of Petroleum Engineers (SPE) | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | International Scientific Journal of Engineering and Management, journal article, Edtech Publishers (OPC) Private Limited | judge 1/5, F1 0.2727, tim dung bai: khong |
| Repaired (da sua) | SPE Journal, journal article, Society of Petroleum Engineers (SPE) | judge 5/5, F1 1.0000, tim dung bai: co |

### q004 - loai `summary`

**Cau hoi:** Give a one sentence summary of the paper 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework for Oil and Gas Safety Report Generatio...

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | In high-risk industrial settings, leveraging large language models (LLMs) for automated accident analysis and generating safety reports has emerged as an effici... | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | This work focuses on the two crucial bottlenecks in Retrieval-Augmented Generation (RAG): high inference latency and expensive computation cost. | judge 1/5, F1 0.0952, tim dung bai: khong |
| Repaired (da sua) | In high-risk industrial settings, leveraging large language models (LLMs) for automated accident analysis and generating safety reports has emerged as an effici... | judge 5/5, F1 1.0000, tim dung bai: co |

### q008 - loai `summary`

**Cau hoi:** Give a one sentence summary of the paper 'An Agentic AI System for Roof Design Compliance Using Computer Vision, Retrieval-Augmented Generation and Large Langua...

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | Designers, engineers, and building officials face increasing pressure to accelerate and improve the accuracy of design review for buildings and infrastructure. | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | (rong) | judge 1/5, F1 0.0000, tim dung bai: co |
| Repaired (da sua) | Designers, engineers, and building officials face increasing pressure to accelerate and improve the accuracy of design review for buildings and infrastructure. | judge 5/5, F1 1.0000, tim dung bai: co |

### q012 - loai `summary`

**Cau hoi:** Give a one sentence summary of the paper 'Retrieval-Augmented Generation (RAG), Generative AI, and Agentic AI Governance: An Integrated Enterprise Governance Pr...

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | Enterprise adoption of artificial intelligence (AI) systems, including Generative AI (GenAI), Retrieval-Augmented Generation (RAG), and agentic AI, is advancing... | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | LOREM IPSUM DOLOR ###### CORRUPTED PAYLOAD @@@@@@. | judge 1/5, F1 0.0000, tim dung bai: co |
| Repaired (da sua) | Enterprise adoption of artificial intelligence (AI) systems, including Generative AI (GenAI), Retrieval-Augmented Generation (RAG), and agentic AI, is advancing... | judge 5/5, F1 1.0000, tim dung bai: co |

### q018 - loai `date`

**Cau hoi:** When was the paper '0346 Retrieval Augmented Generation Improves Large Language Model Performance in Sleep Medicine' published?

| Trang thai | Cau tra loi cua agent | Ket qua cham |
| --- | --- | --- |
| Baseline (du lieu sach) | 2026-05-01 | judge 5/5, F1 1.0000, tim dung bai: co |
| Corrupted (du lieu hong) | 2023-05-01 | judge 1/5, F1 0.0000, tim dung bai: co |
| Repaired (da sua) | 2026-05-01 | judge 5/5, F1 1.0000, tim dung bai: co |

## 3. Cac cau khong doi output

13/20 cau giu nguyen cau tra loi vi corruption khong cham vao paper tuong ung hoac khong cham vao truong du lieu ma cau hoi do can:

`q005`, `q006`, `q007`, `q009`, `q010`, `q011`, `q013`, `q014`, `q015`, `q016`, `q017`, `q019`, `q020`

## 4. Ket luan

Du lieu hong lam **7/20** cau tra loi sai lech so voi baseline, va repair tu raw snapshot dua **toan bo 7** cau ve dung cau tra loi ban dau. Day la bang chung truc tiep o muc output, doc lap voi cac chi so tong hop.
