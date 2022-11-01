# pytket-iqm

[Pytket](https://cqcl.github.io/tket/pytket/api/index.html) is a python module
providing an extensive set of tools for compiling and executing quantum circuits.

`pytket-iqm` is an extension to `pytket` that allows `pytket` circuits to be
executed on [IQM](https://meetiqm.com/)'s quantum devices and simulators.

## Getting started

`pytket-iqm` is available for Python 3.8, 3.9 and 3.10, on Linux, macOS
and Windows. To install, run:

```shell
pip install pytket-iqm
```

This will install `pytket` if it isn't already installed, and add new classes
and methods into the `pytket.extensions` namespace.

API documentation is available
[here](https://cqcl.github.io/pytket-iqm/api/index.html).

Under the hood, `pytket-iqm` uses `iqm-client` to interact with the devices. See
the IQM Client [documentation](https://iqm-finland.github.io/iqm-client/) and
Pytket [documentation](https://cqcl.github.io/tket/pytket/api/) for more info.

To use the integration, initialise an `IQMBackend`, construct a Pytket circuit,
compile it and run. Here is a small example of running a GHZ state circuit:

```python
from pytket.extensions.iqm import IQMBackend
from pytket.circuit import Circuit

backend = IQMBackend(
	url="https://cortex-demo.qc.iqm.fi",
	auth_server_url="https://auth.demo.qc.iqm.fi",
	username="USERNAME",
    password="PASSWORD",
)

circuit = Circuit(3, 3)
circuit.H(0)
circuit.CX(0, 1)
circuit.CX(0, 2)
circuit.measure_all()
circuit = backend.get_compiled_circuit(circuit)

result = backend.run_circuit(c, n_shots=100)
print(result.get_shots())
```

The IQM Client documentation includes the [set of currently supported
instructions]
(https://iqm-finland.github.io/iqm-client/api/iqm_client.iqm_client.html).
`pytket-iqm` retrieves the set from the IQM backend during the initialisation;
then `get_compiled_circuit()` takes care of compiling the circuit into the
form suitable to run on the backend.

During the backend initialisation, `pytket-iqm` also retrieves the names of
physical qubits and qubit connectivity. You can override the qubit connectivity
by providing the `arch` parameter to `IQMBackend` constructor, but it generally
does not make sense, since the IQM server reports the valid quantum architecture
relevant to the given backend URL.

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
changes on the `develop` branch, and open a PR from your fork. If it passes
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
skipped. To enable them, set the following environment variables:

```shell
export PYTKET_RUN_REMOTE_TESTS=1
export PYTKET_REMOTE_IQM_AUTH_SERVER_URL=https://auth.demo.qc.iqm.fi
export PYTKET_REMOTE_IQM_USERNAME=YOUR_USERNAME
export PYTKET_REMOTE_IQM_PASSWORD=YOUR_PASSWORD
```

When adding a new feature, please add a test for it. When fixing a bug, please
add a test that demonstrates the fix.
