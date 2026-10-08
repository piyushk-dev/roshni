def test_delhi_yield_is_between_the_two_datasets(delhi_yield):
    assert round(delhi_yield.annual_optimistic) == 1623
    assert 1400 < delhi_yield.annual < 1550


def test_winter_smog_is_scaled_down(delhi_yield):
    dec = 11
    assert delhi_yield.monthly[dec] < 0.85 * delhi_yield.optimistic[dec]


def test_never_scaled_up(delhi_yield):
    assert all(c <= o for c, o in zip(delhi_yield.monthly, delhi_yield.optimistic))


def test_monsoon_left_alone_when_nasa_is_sunnier(delhi_yield):
    jul = 6
    assert delhi_yield.monthly[jul] == delhi_yield.optimistic[jul]


def test_tilt_faces_south(delhi_yield):
    assert 25 <= delhi_yield.tilt_deg <= 35
    assert abs(delhi_yield.azimuth_deg) < 10
