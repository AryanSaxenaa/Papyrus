from app.text.similarity import author_sets_equal, coerce_author_list, cosine_similarity


def test_cosine_similarity_identical_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_coerce_author_list_openalex_dicts() -> None:
    authors = [{"display_name": "Ada Lovelace"}, {"author": {"display_name": "Alan Turing"}}]
    assert coerce_author_list(authors) == ["Ada Lovelace", "Alan Turing"]


def test_author_sets_equal_with_apify_author_shapes() -> None:
    cited = ["A. Lovelace"]
    resolved = [{"display_name": "Ada Lovelace"}]
    assert author_sets_equal(cited, resolved) is False
