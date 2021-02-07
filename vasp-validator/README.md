# Diem VASP Validator

## Usage

Install the library:

```
pipenv install --dev diem-vasp-validator
```

There are three conceptually different ways to use the validator:

1. As a stand-alone tool, invoked on the command line and running
   predefined set of tests.
2. As a collection of regular Python tests running along the rest of the
   tests in the VASP development project, allowing the user to choose
   a subset of the tests suiting their specific needs.
3. As a package imported in the user's testing code to develop custom test
   cases with minimal prior assumptions.

   
### Stand-alone execution

Implement `vasp_validator.vasp_proxy.VaspProxy` interface in any importable
location. Invoke the following command:

```
validate-vasp path.to.the.interface.implementation.module VaspProxyImplementation
```

Here, the first argument is the module path to the interface implementation;
the second argument is the implementing class name.


### Integration with existing tests and selective execution

Implement `vasp_validator.vasp_proxy.VaspProxy` interface in any importable
location. Assuming pytest is used to run the host project tests, like this:

```
pytest ./tests
```

Add to your root `conftest.py` file, an implementation of function 
`pytest_create_vasp_proxy()`. Make it return an instance of the aforementioned
interface. You can see an example in `tests/conftest.py`. Run the tests again
with additional arguments:

```
pytest -p vasp_validator.tests.plugin --pyargs vasp_validator.tests ./tests
```

- `-p` flag loads the validation plugin for pytest, which calls the user's
  implementation of `pytest_create_vasp_proxy()`.
- `--pyargs` selects which tests to run in any granularity needed. Specifying  
  `vasp_validator.tests` will run all the available tests that come bundled
   with the validation tool. Consult pytest documentation for details.
- `./tests` instructs to run the regular existing tests in your project in
  addition to the VASP validator tests.

The command will run all your tests along with all the VASP Validator tests
and the results will appear as part of the same testing report.


### As a validation library

For maximum control, import `vasp_validator.ValidatorClient` and use it as
a remote VASP mock/simulator to implement your own tests. As a matter of
fact the predefined tests do exactly that. The tests could be copies as-is
(from `vasp_validator/tests`) and modified to suit the specific needs.
With this approach there is no need to implement the testee interface as
everything is under the user's control.


## Development

This library is somewhat unusual since, when installed, it allows importing
tests into the user's existing testing suite. Moreover, the library allows
injection of custom VASP implementations in multiple ways. As such, it is
expected the library developers understand how pytest configuration, fixtures
and hooks work. For example, there are two `tests` directories in the project,
both containing test cases. This is intentional: `vasp_validator/tests`
contains the tests that are packaged, distributed and used by the library
user; `tests/` contains tests that test the tests. After all, quis custodiet
ipsos custodes?

### Testing

The general steps are:

1. Boot two local instances of Reference Wallet. The fastest way is to run
 `make run-double` in the repository root directory.
2. Run `./test.sh` in the vasp-validator directory.

`test.sh` runs all the tests. It accepts all the usual pytest arguments;
for example this command:

```shell script
./test.sh --tb=no -r A
```

Will suppress all the traceback output but will show tests summary in the end.

The first argument can be a test selection string to filter tests found in
`vasp_validator/tests`:

```shell script
./test.sh test_send_tx_no_travel_rule::test_send_tx_no_travel_rule
```

The command will run only the test `test_send_tx_no_travel_rule` found in
`vasp_validator/tests/test_send_tx_no_travel_rule.py`.
