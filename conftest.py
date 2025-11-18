import json
import os
from typing import Any

import pytest
from airflow.configuration import conf
from airflow.models import DagBag
from pytest_mock import MockFixture

curr_dir = os.path.dirname(os.path.realpath(__file__))

secrets_backend_conf = dict(
    connections_file_path=os.path.join(curr_dir, "tests/resources/connections.json"),
    variables_file_path=os.path.join(curr_dir, "tests/resources/variables.json"),
)

@pytest.fixture(name="secrets_backend_conf")
def get_secrets_backend_conf() -> dict[str, str]:
    return secrets_backend_conf


@pytest.fixture
def dagbag(mocker: MockFixture) -> DagBag:
    if not conf.has_section("secrets"):
        conf.add_section("secrets")
    conf.set("secrets", "backend", "airflow.secrets.local_filesystem.LocalFilesystemBackend")
    conf.set("secrets", "backend_kwargs", json.dumps(secrets_backend_conf))

    return DagBag(dag_folder=curr_dir, include_examples=False)
