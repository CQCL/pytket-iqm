# pytket-iqm

[![Slack](https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white)](https://tketusers.slack.com/join/shared_invite/zt-18qmsamj9-UqQFVdkRzxnXCcKtcarLRA#)
[![Stack Exchange](https://img.shields.io/badge/StackExchange-%23ffffff.svg?style=for-the-badge&logo=StackExchange)](https://quantumcomputing.stackexchange.com/tags/pytket)

[Pytket](https://tket.quantinuum.com/api-docs/index.html) is a python module
providing an extensive set of tools for compiling and executing quantum circuits.

`pytket-iqm` is an extension to `pytket` that allows `pytket` circuits to be
executed on [IQM](https://meetiqm.com/)'s quantum devices and simulators.

Some useful links:
- [API Documentation](https://tket.quantinuum.com/extensions/pytket-iqm/)

## Getting started

`pytket-iqm` is available for Python 3.10, 3.11 and 3.12, on Linux, macOS
and Windows. To install, run:

```shell
pip install pytket-iqm
```

This will install `pytket` if it isn't already installed, and add new classes
and methods into the `pytket.extensions` namespace.

API documentation is available
[here](https://tket.quantinuum.com/extensions/pytket-iqm/).

Under the hood, `pytket-iqm` uses `iqm-client` to interact with the devices. See
the IQM Client [documentation](https://iqm-finland.github.io/iqm-client/) and
Pytket [documentation](https://tket.quantinuum.com/api-docs/) for more info.

To use the integration, initialise an `IQMBackend`, construct a Pytket circuit,
compile it and run. Here is a small example of running a GHZ state circuit:

```python
from pytket.extensions.iqm import IQMBackend
from pytket.circuit import Circuit

backend = IQMBackend(device="garnet", api_token="API_TOKEN")

circuit = Circuit(3, 3)
circuit.H(0)
circuit.CX(0, 1)
circuit.CX(0, 2)
circuit.measure_all()
compiled_circuit = backend.get_compiled_circuit(circuit)

result = backend.run_circuit(compiled_circuit, n_shots=100)
print(result.get_shots())
```

Note that the API token can be provided explicitly as an argument when
constructing the backend; alternatively it can be stored in pytket config (see
`IQMConfig.set_iqm_config()`); or it can be stored in a file whose location is
given by the environment variable `IQM_TOKENS_FILE`.

The IQM Client documentation includes the [set of currently supported
instructions]
(https://iqm-finland.github.io/iqm-client/api/iqm.iqm_client.models.Instruction.html).
`pytket-iqm` retrieves the set from the IQM backend during the initialisation;
then `get_compiled_circuit()` takes care of compiling the circuit into the
form suitable to run on the backend.

During the backend initialisation, `pytket-iqm` also retrieves the names of
physical qubits and qubit connectivity.

(Note: At the moment IQM does not provide a quantum computing service open to the 
general public. Please contact their [sales team](https://www.meetiqm.com/contact/)
to set up your access to an IQM quantum computer.)

## Bugs and feature requests

Please file bugs and feature requests on the GitHub
[issue tracker](https://github.com/CQCL/pytket-iqm/issues).

## Development

To install an extension in editable mode, simply change to its subdirectory
within the `modules` directory, and run:

```shell
pip install -e .
```

## Contributing

Pull requests are welcome. To make a PR, first fork the repo, make your proposed
changes on the `main` branch, and open a PR from your fork. If it passes
tests and is accepted after review, it will be merged in.

### Code style

#### Formatting

All code should be formatted using
[black](https://black.readthedocs.io/en/stable/), with default options. This is
checked on the CI.

#### Type annotation

On the CI, [mypy](https://mypy.readthedocs.io/en/stable/) is used as a static
type checker and all submissions must pass its checks. You should therefore run
`mypy` locally on any changed files before submitting a PR. Because of the way
extension modules embed themselves into the `pytket` namespace this is a little
complicated, but it should be sufficient to run the script `modules/mypy-check`
(passing as a single argument the root directory of the module to test). The
script requires `mypy` 0.800 or above.

#### Linting

We use [pylint](https://pypi.org/project/pylint/) on the CI to check compliance
with a set of style requirements (listed in `.pylintrc`). You should run
`pylint` over any changed files before submitting a PR, to catch any issues.

### Tests

To run the tests:

```shell
cd tests
pip install -r test-requirements.txt
pytest
```

By default, the remote tests, which run against the real backend server, are 
skipped. To enable them, set the environment variable
`PYTKET_RUN_REMOTE_TESTS=1` and make sure you have your API token stored either
in pytket config or in a file whose location is given by the environment
variable `IQM_TOKENS_FILE`.

When adding a new feature, please add a test for it. When fixing a bug, please
add a test that demonstrates the fix.
