import numpy as np


class SoftmaxProbability:
    """
    Softmax probability 是將模型輸出的原始分數（logits）轉換成總和為 1、範圍在 0 到 1 之間的機率分布的一種數學函數機制

    將檢索出來的前 k 個文件的 BM25 原始分數，透過帶有溫度參數（Temperature, T）的 Softmax 轉換成機率分布。這能讓得分最高的文件獲得顯著的信賴度
    """

    @staticmethod
    def bm25_to_confidence(scores: list[float], temperature: float = 3.0) -> list[float]:
        """
        將 BM25 原始分數轉換為 Softmax 信賴度機率
        """

        if not scores:
            return []

        scores = np.array(scores, dtype=float)

        # 減去最大值防止指數爆炸 (Exp Overflow)
        exp_scores = np.exp((scores - np.max(scores)) / temperature)

        # 計算 Softmax 機率
        probabilities = exp_scores / np.sum(exp_scores)
        return probabilities.tolist()


if __name__ == '__main__':
    # 假設 BM25 檢索出前 3 篇文件的原始得分
    bm25_scores = [18.5, 7.3, 7.1, 6.7, 6.5]
    # bm25_scores = [60, 53, 51, 48, 40]

    # 轉換成信賴度
    confidences = SoftmaxProbability.bm25_to_confidence(bm25_scores, temperature=3.0)
    print(confidences)

    for idx, (score, conf) in enumerate(zip(bm25_scores, confidences)):
        print(f"文件 {idx + 1}: BM25 分數 = {score:<5} -> 信賴度 = {conf:.2%}")
