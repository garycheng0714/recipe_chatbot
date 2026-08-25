# 訪談 RAG — 混合檢索問答系統

針對 Eliud Kipchoge YouTube 訪談逐字稿建置的 Hybrid RAG（Retrieval-Augmented Generation）系統。使用者以中文提問，系統翻譯、檢索、生成後回傳基於原始逐字稿內容的英文答案。

## 架構圖


                   Query
                     │
                     ▼
              Hybrid Retrieval
              /              \
           BM25              Dense (Qdrant)
              \              /
               └──── RRF ───┘
                     │
                     ▼
                  Context
                     │
                     ▼
                    LLM (llama3:8b)
                     │
                     ▼
                  Answer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     Faithfulness          Relevancy
          │
          ▼
      Correctness

## Chunking

1. 透過 API 取得影片逐字稿和資訊，依據作者劃分好的分段做章節切割
2. 透過 Gemini API 將逐字稿 raw data 補上標點符號及語意斷行
3. 透過 Gemini API 從各章節中提取 QA pair (knowledge unit) 並存進 DB、BM25 和 Qdrant
![DB_data_model](rag_db_data_model.png)


## Retrieval

### 動態 RRF 權重設計

* 第一版：用規則判斷(query 是否以 who/how/what 開頭)來切換權重(相等 vs ES 0.4 / Qdrant 0.6)


* 第二版：改用 BM25 softmax 信心分數 — top.1 BM25 softmax score > 0.5 就用 1:1, 否則用 0.4/0.6 偏向向量


### 未採用 Rerank 的原因

* 測過幾個模型後發現，即使正確 chunk 仍留在 top.5 內 Rerank 卻讓 MRR 不升反降。
既然高 Recall 已確保正確 chunk 會在 top.5 內，那也不必多一層 Rerank 增加 latency，讓 LLM 從 top.5 內挑出正確答案即可。

### 迴歸測試
* 用 golden set + pytest regression harness (自己寫 Recall / MRR 函式、顯示 diff report 並 assert)

![image](./report_screenshot.png)


## Generation

### Prompt Injection 防護

用 Pydantic AI 的 InputGuardrail 做關鍵字比對以防 prompt injection。Query 內如包含特定關鍵字則直接 block 不讓 LLM 接手。

### Evaluation

建立 真實性（Faithfulness)、內容相關性（Context Relevance）、回答相關性（Answer Relevance）評估指標

![llm_evaluation](llm_evaluation.png)