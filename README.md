# 檢索評估遇到的問題與解決方式

### 1. Golden set 標註問題

* 問題:標註集裡漏了一個相關的 knowledge unit(relevant_ids 沒收全),導致 Hybrid RRF 的結果看起來比實際差
* 解決:找出並修正這個標註缺口

### 2. 動態 RRF 權重設計的演進

* 第一版:用規則判斷(query 是否以 who/how/what 開頭)來切換權重(相等 vs ES 0.4 / Qdrant 0.6)


* 第二版:改用 BM25 softmax 信心分數 —— top-1 BM25 softmax score > 0.5 就用 1:1,否則用 0.4/0.6 偏向向量


* 用 keyword 型查詢 (Münster、python、recovery、recreational runners) 和 semantic 型查詢(9 個 training/mindset 相關問題) 分別建立 golden set,用 Recall@5 和 MRR@5 評估 BM25 / Vectors / Hybrid

### 3. 迴歸測試框架的取捨

* 問題:要不要用 deepeval?

* 決定:先不用 —— deepeval 主要價值在 LLM-as-judge 和 Confident AI dashboard,跟目前純檢索指標的評估階段不合;之後做 answer-level faithfulness 評估時再考慮

* 改用自建 pytest regression harness(自己寫 Recall/MRR 函式、顯示 diff report 並 assert)

[report.html](./youtube/tests/retrieve/report/golden_set_diff.html)


### 4. 真實的檢索缺陷(非標註問題)

* 問題:針對「What key training lets his body sustain high speed for a long time?」這類查詢,向量檢索會把同講者、同主題但離題的答案排到正確答案之上,導致 MRR 掉到 0.33(但 Recall 在各方法間都維持 0.67,顯示問題出在排序而非有沒有撈到)
* 
* 目前狀態:考慮導入 cross-encoder reranker 來處理,決定先累積更多類似案例再決定,避免過早增加複雜度