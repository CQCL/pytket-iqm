# Copyright 2020-2023 Cambridge Quantum Computing
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

import json
import os
from typing import cast, Dict, List, Optional, Sequence, Tuple, Union
from uuid import UUID
from iqm.iqm_client.iqm_client import Circuit as IQMCircuit
from iqm.iqm_client.iqm_client import Instruction, IQMClient, Metadata, Status
import numpy as np
from pytket.backends import Backend, CircuitStatus, ResultHandle, StatusEnum
from pytket.backends.backend import KwargTypes
from pytket.backends.backend_exceptions import CircuitNotRunError
from pytket.backends.backendinfo import BackendInfo
from pytket.backends.backendresult import BackendResult
from pytket.backends.resulthandle import _ResultIdTuple
from pytket.circuit import Circuit, Node, OpType
from pytket.extensions.iqm._metadata import __extension_version__
from pytket.passes import (
    BasePass,
    SequencePass,
    SynthesiseTket,
    FullPeepholeOptimise,
    FlattenRegisters,
    RebaseCustom,
    DecomposeBoxes,
    RemoveRedundancies,
    DefaultMappingPass,
    DelayMeasures,
    SimplifyInitial,
    KAKDecomposition,
    CliffordSimp,
)
from pytket.predicates import (
    ConnectivityPredicate,
    GateSetPredicate,
    NoClassicalControlPredicate,
    NoFastFeedforwardPredicate,
    NoBarriersPredicate,
    NoMidMeasurePredicate,
    NoSymbolsPredicate,
    Predicate,
)
from pytket.architecture import Architecture
from pytket.utils import prepare_circuit
from pytket.utils.outcomearray import OutcomeArray
from .config import IQMConfig

# Mapping of natively supported instructions' names to members of Pytket OpType
_IQM_PYTKET_OP_MAP = {
    "phased_rx": OpType.PhasedX,
    "cz": OpType.CZ,
    "measurement": OpType.Measure,
    "barrier": OpType.Barrier,
}


class IqmAuthenticationError(Exception):
    """Raised when there is no IQM access credentials available."""

    def __init__(self) -> None:
        super().__init__("No IQM access credentials provided or found in config file.")


class IQMBackend(Backend):
    """
    Interface to an IQM device or simulator.
    """

    _supports_shots = True
    _supports_counts = True
    _supports_contextual_optimisation = True
    _persistent_handles = True

    def __init__(
        self,
        url: str,
        arch: Optional[List[List[str]]] = None,
        auth_server_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Construct a new IQM backend.

        Requires _either_ a valid auth server URL, username and password, _or_ a tokens
        file.

        Auth server URL, username and password can either be provided as parameters or
        set in config using :py:meth:`pytket.extensions.iqm.set_iqm_config`.

        Path to the tokens file is read from the environmment variable
        ``IQM_TOKENS_FILE``. If set, this overrides any other credentials provided as
        arguments.

        :param url: base URL for requests
        :param arch: Optional list of couplings between the qubits defined, if
        not set the default value from the server is used.
        :param auth_server_url: base URL of authentication server
        :param username: IQM username
        :param password: IQM password
        """
        super().__init__()
        self._url = url
        config = IQMConfig.from_default_config_file()

        if auth_server_url is None:
            auth_server_url = config.auth_server_url
        tokens_file = os.getenv("IQM_TOKENS_FILE")
        if username is None:
            username = config.username
        if password is None:
            password = config.password
        if (username is None or password is None) and tokens_file is None:
            raise IqmAuthenticationError()

        if tokens_file is None:
            self._client = IQMClient(
                self._url,
                auth_server_url=auth_server_url,
                username=username,
                password=password,
            )
        else:
            self._client = IQMClient(self._url, tokens_file=tokens_file)
        _iqmqa = self._client.get_quantum_architecture()
        self._operations = [_IQM_PYTKET_OP_MAP[op] for op in _iqmqa.operations]
        self._qubits = [_as_node(qb) for qb in _iqmqa.qubits]
        self._n_qubits = len(self._qubits)
        if arch is None:
            arch = _iqmqa.qubit_connectivity
        coupling = [(_as_node(a), _as_node(b)) for (a, b) in arch]
        if any(qb not in self._qubits for couple in coupling for qb in couple):
            raise ValueError("Architecture contains qubits not in device")
        self._arch = Architecture(coupling)
        self._backendinfo = BackendInfo(
            name=type(self).__name__,
            device_name=_iqmqa.name,
            version=__extension_version__,
            architecture=self._arch,
            gate_set=set(self._operations),
        )

    @property
    def backend_info(self) -> BackendInfo:
        return self._backendinfo

    @property
    def required_predicates(self) -> List[Predicate]:
        return [
            NoClassicalControlPredicate(),
            NoFastFeedforwardPredicate(),
            NoBarriersPredicate(),
            NoMidMeasurePredicate(),
            NoSymbolsPredicate(),
            GateSetPredicate(set(self._operations)),
            ConnectivityPredicate(self._arch),
        ]

    def rebase_pass(self) -> BasePass:
        return _iqm_rebase()

    def default_compilation_pass(self, optimisation_level: int = 1) -> BasePass:
        assert optimisation_level in range(3)
        passes = [DecomposeBoxes(), FlattenRegisters()]
        if optimisation_level == 0:
            passes.append(self.rebase_pass())  # to satisfy MaxTwoQubitGatesPredicate
        elif optimisation_level == 1:
            passes.append(SynthesiseTket())
        elif optimisation_level == 2:
            passes.append(FullPeepholeOptimise())
        passes.append(DefaultMappingPass(self._arch))
        passes.append(DelayMeasures())
        if optimisation_level == 2:
            passes.append(KAKDecomposition(allow_swaps=False))
            passes.append(CliffordSimp(allow_swaps=False))
            passes.append(SynthesiseTket())
        passes.append(self.rebase_pass())
        passes.append(RemoveRedundancies())
        return SequencePass(passes)

    @property
    def _result_id_type(self) -> _ResultIdTuple:
        return (bytes, str)

    def process_circuits(
        self,
        circuits: Sequence[Circuit],
        n_shots: Union[None, int, Sequence[Optional[int]]] = None,
        valid_check: bool = True,
        **kwargs: KwargTypes,
    ) -> List[ResultHandle]:
        """
        See :py:meth:`pytket.backends.Backend.process_circuits`.

        Supported `kwargs`:
        - `postprocess`: apply end-of-circuit simplifications and classical
          postprocessing to improve fidelity of results (bool, default False)
        - `simplify_initial`: apply the pytket ``SimplifyInitial`` pass to improve
          fidelity of results assuming all qubits initialized to zero (bool, default
          False)
        """
        circuits = list(circuits)
        n_shots_list = Backend._get_n_shots_as_list(
            n_shots,
            len(circuits),
            optional=False,
        )

        if valid_check:
            self._check_all_circuits(circuits)

        postprocess = kwargs.get("postprocess", False)
        simplify_initial = kwargs.get("postprocess", False)

        handles = []
        for i, (c, n_shots) in enumerate(zip(circuits, n_shots_list)):
            if postprocess:
                c0, ppcirc = prepare_circuit(c, allow_classical=False, xcirc=_xcirc)
                ppcirc_rep = ppcirc.to_dict()
            else:
                c0, ppcirc_rep = c, None
            if simplify_initial:
                SimplifyInitial(
                    allow_classical=False, create_all_qubits=True, xcirc=_xcirc
                ).apply(c0)
            instrs = _translate_iqm(c0)
            qm = {str(qb): _as_name(cast(Node, qb)) for qb in c.qubits}
            iqmc = IQMCircuit(
                name=c.name if c.name else f"circuit_{i}",
                instructions=instrs,
                metadata=None,
            )
            run_id = self._client.submit_circuits(
                [iqmc], qubit_mapping=qm, shots=n_shots
            )
            handles.append(ResultHandle(run_id.bytes, json.dumps(ppcirc_rep)))
        for handle in handles:
            self._cache[handle] = dict()
        return handles

    def _update_cache_result(
        self, handle: ResultHandle, result_dict: Dict[str, BackendResult]
    ) -> None:
        if handle in self._cache:
            self._cache[handle].update(result_dict)
        else:
            self._cache[handle] = result_dict

    def circuit_status(self, handle: ResultHandle) -> CircuitStatus:
        self._check_handle_type(handle)
        run_id = UUID(bytes=cast(bytes, handle[0]))
        run_result = self._client.get_run(run_id)
        status = run_result.status
        if status == Status.PENDING_EXECUTION:
            return CircuitStatus(StatusEnum.SUBMITTED)
        elif status == Status.READY:
            measurements = cast(dict, run_result.measurements)[0]
            shots = OutcomeArray.from_readouts(
                np.array(
                    [[r[0] for r in rlist] for cbstr, rlist in measurements.items()],
                    dtype=int,
                )
                .transpose()
                .tolist()
            )
            ppcirc_rep = json.loads(cast(str, handle[1]))
            ppcirc = Circuit.from_dict(ppcirc_rep) if ppcirc_rep is not None else None
            self._update_cache_result(
                handle, {"result": BackendResult(shots=shots, ppcirc=ppcirc)}
            )
            return CircuitStatus(StatusEnum.COMPLETED)
        else:
            assert status == Status.FAILED
            return CircuitStatus(StatusEnum.ERROR, cast(str, run_result.message))

    def get_result(self, handle: ResultHandle, **kwargs: KwargTypes) -> BackendResult:
        """
        See :py:meth:`pytket.backends.Backend.get_result`.
        Supported kwargs: `timeout` (default 900).
        """
        try:
            return super().get_result(handle)
        except CircuitNotRunError:
            timeout = kwargs.get("timeout", 900)
            # Wait for job to finish; result will then be in the cache.
            run_id = UUID(bytes=cast(bytes, handle[0]))
            self._client.wait_for_results(run_id, timeout_secs=cast(float, timeout))
            circuit_status = self.circuit_status(handle)
            if circuit_status.status is StatusEnum.COMPLETED:
                return cast(BackendResult, self._cache[handle]["result"])
            else:
                assert circuit_status.status is StatusEnum.ERROR
                raise RuntimeError(circuit_status.message)

    def get_metadata(self, handle: ResultHandle, **kwargs: KwargTypes) -> Metadata:
        """Return the metadata corresponding to the handle.

        Use keyword arguments to specify parameters to be used in retrieving
        the metadata.

        * `timeout`: maximum time to wait for remote job to finish

        Example usage:
            n_shots = 100
            backend.run_circuit(circuit, n_shots=n_shots, timeout=30)
            handle = backend.process_circuits([circuit], n_shots=n_shots)[0]
            result = backend.get_result(handle)
            metadata = backend.get_metadata(handle)
            print([qm.physical_name for qm in metadata.request.qubit_mapping])

        :param handle: handle to results
        :type handle: ResultHandle
        :return: Metadata corresponding to handle
        :rtype: Metadata
        """
        self._check_handle_type(handle)
        if handle in self._cache and "metadata" in self._cache[handle]:
            return cast(Metadata, self._cache[handle]["metadata"])
        # Wait for job to finish, capture metadata and store it in cache
        timeout = kwargs.get("timeout", 900)
        run_id = UUID(bytes=cast(bytes, handle[0]))
        run_result = self._client.wait_for_results(
            run_id, timeout_secs=cast(float, timeout)
        )
        self._cache[handle]["metadata"] = run_result.metadata
        return cast(Metadata, self._cache[handle]["metadata"])


def _as_node(qname: str) -> Node:
    assert qname.startswith("QB")
    x = int(qname[2:])
    assert x >= 1
    return Node(x - 1)


def _as_name(qnode: Node) -> str:
    assert qnode.reg_name == "node"
    return f"QB{qnode.index[0] + 1}"


def _translate_iqm(circ: Circuit) -> Tuple[Instruction, ...]:
    """Convert a circuit in the IQM gate set to IQM list representation."""
    instrs = []
    for cmd in circ.get_commands():
        op = cmd.op
        qbs = cmd.qubits
        cbs = cmd.bits
        optype = op.type
        params = op.params
        if optype == OpType.PhasedX:
            instr = Instruction(
                name="phased_rx",
                implementation=None,
                qubits=(str(qbs[0]),),
                args={"angle_t": 0.5 * params[0], "phase_t": 0.5 * params[1]},
            )
        elif optype == OpType.CZ:
            instr = Instruction(
                name="cz",
                implementation=None,
                qubits=(str(qbs[0]), str(qbs[1])),
                args={},
            )
        else:
            assert optype == OpType.Measure
            instr = Instruction(
                name="measurement",
                implementation=None,
                qubits=(str(qbs[0]),),
                args={"key": str(cbs[0])},
            )
        instrs.append(instr)
    return tuple(instrs)


def _iqm_rebase() -> BasePass:
    # CX replacement
    c_cx = Circuit(2)
    c_cx.add_gate(OpType.PhasedX, [-0.5, 0.5], [1])
    c_cx.CZ(0, 1)
    c_cx.add_gate(OpType.PhasedX, [0.5, 0.5], [1])

    # TK1 replacement
    c_tk1 = (
        lambda a, b, c: Circuit(1)
        .add_gate(OpType.PhasedX, [-1, (a - c) / 2], [0])
        .add_gate(OpType.PhasedX, [1 + b, a], [0])
    )

    return RebaseCustom({OpType.CZ, OpType.PhasedX}, c_cx, c_tk1)


_xcirc = Circuit(1).add_gate(OpType.PhasedX, [1, 0], [0]).add_phase(0.5)
