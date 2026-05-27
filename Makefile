
.PHONY: unittest e2e integration poller taskiq crawler emb

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
	uv run python -m web_crawler.service.crawler_app

emb:
	uv run infinity_emb v2 --model-id BAAI/bge-m3 --device mps