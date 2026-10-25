import numpy as np
import pytest

from rockbands.sensors import SENSORS


def make_scene(sensor, shape=(4, 5), seed=0, dtype=float):
    """Random positive 'reflectance' for every native band of a sensor, keyed by native id."""
    rng = np.random.default_rng(seed)
    return {b.id: rng.uniform(0.05, 0.6, shape).astype(dtype) for b in sensor.bands}


@pytest.fixture(params=list(SENSORS.values()), ids=list(SENSORS))
def sensor(request):
    return request.param
