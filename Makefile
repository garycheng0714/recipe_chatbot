
.PHONY: unittest e2e integration poller taskiq crawler emb service diff fastapi pg_backup

# 預設目標：顯示說明
help:
	@echo "可用指令："
	@echo "  make unittest     - 執行單元測試"
	@echo "  make e2e          - 執行 e2e 測試"
	@echo "  make integration  - 執行整合測試"
	@echo "  make poller	   - 啟動 outbox poller"
	@echo "  make taskiq       - 啟動 taskiq"
	@echo "  make crawler      - 啟動 crawler"
	@echo "  make emb          - 啟動 embedding server"
	@echo "  make service      - 啟動相關 service"
	@echo "  make diff         - 查看 es 和 qdrant 的差異"
	@echo "  make fastapi      - 啟動 Fastapi"
	@echo "  make pg_backup    - 備份 Postgresql"

unittest:
	pytest --ignore=tests/integration/ --ignore=tests/e2e/

e2e:
	pytest tests/e2e/

integration:
	pytest tests/integration/

poller:
	uv run python -m tasks.outbox_poller

taskiq:
	uv run taskiq worker tasks.tasks:redis_broker --workers 2 --max-async-tasks 1

crawler:
	uv run python -m web_crawler.main

emb:
	uv run infinity_emb v2 --model-id BAAI/bge-m3 --device mps

service:
	honcho start

diff:
	uv run python qdrant_es_diff.py

fastapi:
	uvicorn app.main:app --reload

pg_backup:
	@# $$ 是為了防止 make 將其誤認為 Makefile 內建的變數
	@# date：呼叫系統時間, +%Y%m%d_%H%M%S：將日期時間格式化為 年月日_時分秒
	pg_dump -h localhost -U postgres -d recipe_orm_db -Fc -f ~/Desktop/db_backup/recipe_db_backup_$$(date +%Y%m%d_%H%M%S).dump