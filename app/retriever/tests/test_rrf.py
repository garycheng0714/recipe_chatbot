from app.retriever.fusion.rrf import RRFRanker, RankList


def test_rrf_two_rank_list_then_a_got_top_rank():
    list_1 = ["A", "B", "C"]
    list_2 = ["D", "A", "B"]

    rrf_ranker = RRFRanker()

    fused = rrf_ranker.reciprocal_rank_fusion([RankList(ids=list_1), RankList(ids=list_2)])

    assert fused[0].id == "A"


def test_rrf_two_rank_list_then_a_and_b_have_same_rank():
    list_1 = ["A", "B", "C"]
    list_2 = ["B", "A", "D"]

    rrf_ranker = RRFRanker()

    fused = rrf_ranker.reciprocal_rank_fusion([RankList(ids=list_1), RankList(ids=list_2)])

    scores = {r.id: r.score for r in fused}

    assert scores["A"] == scores["B"]


def test_rrf_two_rank_list_then_all_elements_exist():
    list_1 = ["A", "B", "C"]
    list_2 = ["B", "A", "D"]

    rrf_ranker = RRFRanker()

    fused = rrf_ranker.reciprocal_rank_fusion([RankList(ids=list_1), RankList(ids=list_2)])

    ids = {r.id for r in fused}

    assert ids == {"A", "B", "C", "D"}


def test_rrf_empty_list_then_return_empty_list():
    rrf_ranker = RRFRanker()

    fused = rrf_ranker.reciprocal_rank_fusion([])

    assert fused == []