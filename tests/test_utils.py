from sat_city.utils import bbox_to_geom
import pytest

GEOM_FIXTURE_0 = {'type': 'Polygon', 'coordinates': [[[-10, 10], [-10, 0], [10, 0], [10, 10], [-10, 10]]]}
GEOM_FIXTURE_1 = {'type': 'Polygon', 'coordinates': [[[-20, 10], [-20, 0], [10, 0], [10, 10], [-20, 10]]]}
TEST_BBOX_0 = [-10, 0, 10, 10]
TEST_BBOX_1 = [-20, 0, 10, 10]


@pytest.mark.parametrize("test_input,expected", [(TEST_BBOX_0, GEOM_FIXTURE_0), (TEST_BBOX_1, GEOM_FIXTURE_1)])
def test_bbox_to_geom(test_input, expected) -> None:
    test_geom_0 = bbox_to_geom(test_input)
    assert test_geom_0 == expected
