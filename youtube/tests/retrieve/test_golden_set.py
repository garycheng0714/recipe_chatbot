import pytest

from youtube.tests.retrieve.conftest import FileType

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_crate_golden_set_recall_and_mrr_metrics(data_test_set_reader, create_recall_mrr_metrics, create_metrics_json_data, check_metrics_diff):
    test_sets = data_test_set_reader("youtube/tests/retrieve/assets/golden_set.json")


    df = await create_recall_mrr_metrics(test_sets)

    print(df)

    create_metrics_json_data(df)

    assert check_metrics_diff(), "📉 Metrics Decline"