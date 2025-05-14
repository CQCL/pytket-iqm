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
from uuid import UUID

import pytest
from iqm.iqm_client.errors import ClientAuthenticationError
from iqm.iqm_client.models import Metadata, RunRequest

from pytket.backends import StatusEnum
from pytket.circuit import Circuit
from pytket.extensions.iqm import IQMBackend

# Skip remote tests if not specified
skip_remote_tests: bool = os.getenv("PYTKET_RUN_REMOTE_TESTS") is None
REASON = "PYTKET_RUN_REMOTE_TESTS not set (requires configuration of IQM credentials)"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_iqm(authenticated_iqm_backend: IQMBackend, sample_circuit: Circuit) -> None:
    # Run a circuit on the demo device.
    b = authenticated_iqm_backend
    c = b.get_compiled_circuit(sample_circuit)
    n_shots = 10
    res = b.run_circuit(c, n_shots=n_shots, timeout=30)
    shots = res.get_shots()
    counts = res.get_counts()
    assert len(shots) == n_shots
    assert sum(counts.values()) == n_shots


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_invalid_cred() -> None:
    with pytest.raises(ClientAuthenticationError):
        _ = IQMBackend(device="garnet", api_token="invalid")


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_handles(
    authenticated_iqm_backend: IQMBackend, sample_circuit: Circuit
) -> None:
    b = authenticated_iqm_backend
    c = b.get_compiled_circuit(sample_circuit)
    n_shots = 5
    res = b.run_circuit(c, n_shots=n_shots, timeout=30)
    shots = res.get_shots()
    assert len(shots) == n_shots
    counts = res.get_counts()
    assert sum(counts.values()) == n_shots
    handles = b.process_circuits([c, c], n_shots=n_shots)
    assert len(handles) == 2
    for handle in handles:
        assert b.circuit_status(handle).status in [
            StatusEnum.SUBMITTED,
            StatusEnum.COMPLETED,
        ]
    results = b.get_results(handles)
    for handle in handles:
        assert b.circuit_status(handle).status == StatusEnum.COMPLETED
    for result in results:
        assert result.get_shots().shape == (n_shots, c.n_qubits)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_metadata(
    authenticated_iqm_backend: IQMBackend, sample_circuit: Circuit
) -> None:
    b = authenticated_iqm_backend
    c = b.get_compiled_circuit(sample_circuit)
    n_shots = 5
    b.run_circuit(c, n_shots=n_shots, timeout=30)
    handle = b.process_circuits([c], n_shots=n_shots)[0]
    b.get_result(handle)
    metadata = b.get_metadata(handle)
    assert isinstance(metadata, Metadata)
    assert isinstance(metadata.calibration_set_id, UUID)
    assert isinstance(metadata.request, RunRequest)
    assert len(metadata.request.circuits) == 1
    assert metadata.request.circuits[0].name == c.name
    assert metadata.request.calibration_set_id is None
    assert isinstance(metadata.request.qubit_mapping, list)
    assert len(metadata.request.qubit_mapping) == c.n_qubits
    assert metadata.request.shots == n_shots


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_none_nshots(
    authenticated_iqm_backend: IQMBackend, sample_circuit: Circuit
) -> None:
    b = authenticated_iqm_backend
    c = b.get_compiled_circuit(sample_circuit)
    with pytest.raises(ValueError) as error_info:
        _ = b.process_circuits([c])
    assert "Parameter n_shots is required" in str(error_info.value)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_default_pass(authenticated_iqm_backend: IQMBackend) -> None:
    b = authenticated_iqm_backend
    for ol in range(3):
        comp_pass = b.default_compilation_pass(ol)
        c = Circuit(3, 3)
        c.H(0)
        c.CX(0, 1)
        c.CSWAP(1, 0, 2)
        c.ZZPhase(0.84, 2, 0)
        c.measure_all()
        comp_pass.apply(c)
        for pred in b.required_predicates:
            assert pred.verify(c)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_postprocess(authenticated_iqm_backend: IQMBackend) -> None:
    b = authenticated_iqm_backend
    assert b.supports_contextual_optimisation
    c = Circuit(2, 2)
    c.Y(0)
    c.Z(1)
    c.measure_all()
    c = b.get_compiled_circuit(c)
    h = b.process_circuit(c, n_shots=10, postprocess=True)
    r = b.get_result(h)
    shots = r.get_shots()
    assert len(shots) == 10
    assert all(len(shot) == 2 for shot in shots)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_backendinfo(authenticated_iqm_backend: IQMBackend) -> None:
    b = authenticated_iqm_backend
    info = b.backend_info
    assert info.name == type(b).__name__
    assert len(info.gate_set) >= 3
