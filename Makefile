
.PHONY: unittest e2e integration poller taskiq crawler \
		emb service diff fastapi pg_backup alembic_migration \
		alembic_upgrade urlscanner unittest-yt

# rg "index_batch_chunk": 「快速在整個專案裡搜尋字串」

# 預設目標：顯示說明
help:
	@echo "可用指令："
	@echo "  make unittest     			- 執行單元測試"
	@echo "  make unittest-yt     		- 執行 yt 單元測試"
	@echo "  make e2e          			- 執行 e2e 測試"
	@echo "  make integration  			- 執行整合測試"
	@echo "  make poller	   			- 啟動 outbox poller"
	@echo "  make taskiq       			- 啟動 taskiq"
	@echo "  make crawler      			- 啟動 crawler"
	@echo "  make urlscanner      		- 啟動 url scanner"
	@echo "  make emb          			- 啟動 embedding server"
	@echo "  make service      			- 啟動 Procfile 內的服物"
	@echo "  make diff        			- 查看 es 和 qdrant 的差異"
	@echo "  make fastapi      			- 啟動 Fastapi"
	@echo "  make pg_backup    			- 備份 Postgresql"
	@echo "  make alembic_migration		- 建立 Postgresql Migration commit"
	@echo "  make alembic_upgrade		- 執行 Postgresql Migration"

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

urlscanner:
	uv run python -m web_crawler.urlscanner

emb:
	uv run infinity_emb v2 --model-id BAAI/bge-m3 --device mps --batch-size 8

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

alembic_migration:
	@if [ -z "$(msg)" ]; then \
		echo "錯誤：請使用 msg 變數！例如：make alembic_migration msg='add phone to user'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(msg)"

alembic_upgrade:
	@# alembic current：查看目前資料庫正處於哪一個遷移版本 ID
	@# alembic history：依時間順序列出專案中所有的遷移腳本
	@# 執行所有尚未套用的資料庫遷移，將資料庫結構（Schema）更新至最新的版本
	alembic upgrade head

unittest-yt :
	pytest --ignore=tests/ --ignore=web_crawler/tests/ --html=yt_unittest_report.html