# Copyright Quantinuum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import pytest

from pytket.circuit import Circuit
from pytket.extensions.iqm import IQMBackend


@pytest.fixture(name="authenticated_iqm_backend", scope="session")
def fixture_authenticated_iqm_backend() -> IQMBackend:
    # Authenticated IQMBackend used for the remote tests
    # The credentials are taken from the env variable:
    # - PYTKET_REMOTE_IQM_API_TOKEN

    return IQMBackend(
        device="pyrite:test", api_token=os.getenv("PYTKET_REMOTE_IQM_API_TOKEN")
    )


@pytest.fixture(name="sample_circuit", scope="session")
def fixture_sample_circuit() -> Circuit:
    c = Circuit(4, 4)
    c.H(0)
    c.CX(0, 1)
    c.Rz(0.3, 2)
    c.CSWAP(0, 1, 2)
    c.CRz(0.4, 2, 3)
    c.CY(1, 3)
    c.ZZPhase(0.1, 2, 0)
    c.Tdg(3)
    c.measure_all()
    c.name = "test_circuit"
    return c
