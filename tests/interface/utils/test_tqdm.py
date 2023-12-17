from spatialyze.utils.tqdm import tqdm


def test_tqdm():
    assert [*tqdm(range(10))] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
