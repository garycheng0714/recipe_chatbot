import ast

from jinja2 import Environment, FileSystemLoader
import pandas as pd


def generate_benchmark_html(
    data_base,
    data_curr,
    template_path="index.html",
    output_filename="rag_metrics_diff.html",
):
    # 1. 解析資料
    def parse_df(data):
        df = pd.DataFrame(data).T
        df.index = pd.MultiIndex.from_tuples(
            [ast.literal_eval(idx) for idx in df.index],
            names=["Query", "Metric"],
        )
        return df

    success = True

    df_b = parse_df(data_base)
    df_c = parse_df(data_curr)
    df_diff = df_c - df_b

    # 2. 轉換資料為字典結構給 Jinja2 渲染
    rows = []
    for (query, metric), row in df_c.iterrows():
        is_avg = "Average" in query
        row_class = "table-row table-row-avg" if is_avg else "table-row"

        metrics_data = []
        for col in ["BM25", "Vectors", "Hybrid"]:
            val_c = row[col]
            diff = df_diff.loc[(query, metric), col]

            if diff < 0:
                badge_class = "badge badge-negative"
                diff_text = f"({diff:+.2f})"
                success = False
            elif diff > 0:
                badge_class = "badge badge-positive"
                diff_text = f"({diff:+.2f})"
            else:
                badge_class = "badge badge-neutral"
                diff_text = ""

            metrics_data.append(
                {
                    "val": f"{val_c:.2f}",
                    "diff_text": diff_text,
                    "badge_class": badge_class,
                }
            )

        rows.append(
            {
                "query": query,
                "metric": metric,
                "row_class": row_class,
                "metrics": metrics_data,
            }
        )

    # 3. 讀取 template.html 並渲染結果
    env = Environment(loader=FileSystemLoader("app/retriever/service/report/"))
    template = env.get_template(template_path)
    rendered_html = template.render(rows=rows)

    # 4. 寫入檔案
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"✅ 報告已生成：{output_filename}")

    return success
