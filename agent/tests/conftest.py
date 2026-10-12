import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "agent"), str(ROOT / "broker")]
FIXTURE = ROOT / "fixtures" / "github-conn-saturation.json"
DEGRADED = ROOT / "fixtures" / "github-conn-saturation-degraded.json"


def make_broker(fixture: Path = FIXTURE):
    os.environ["BROKER_FIXTURE"] = str(fixture)
    os.environ["ALLOWED_NAMESPACES"] = "shop"
    from kubesleuth_broker.server import build_toolbox, create_server
    return create_server(build_toolbox(), rate=1000, burst=1000)


@pytest.fixture
def broker():
    return make_broker()


@pytest.fixture
def degraded_broker():
    return make_broker(DEGRADED)
