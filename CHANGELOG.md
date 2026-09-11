# CHANGELOG


## v0.7.0 (2025-07-09)

### Features

- Updated to new arkitekt stack
  ([`65c7563`](https://github.com/arkitektio/fluss-next/commit/65c7563666a2774811f156a41b7e876b7f142b73))

- Replaced HerreAuthLink with FaktsAuthLink in ArkitektNextFluss. - Updated build_service method to
  remove Herre parameter. - Changed Docker images in docker-compose.yml from nightly to dev versions
  for fluss_next and init services. - Updated rath dependency version from 3.4 to 3.5.1 in
  pyproject.toml and uv.lock. - Added new dependencies: docstring-parser, fieldz, inflection,
  jsonpatch, and jsonpointer in uv.lock. - Added rekuest-next dependency in both regular and dev
  dependencies. - Created an empty __init__.py file in fluss_next/api directory.


## v0.6.1 (2025-05-13)


## v0.6.0 (2025-05-10)

### Bug Fixes

- Upgrade to 3.4 and add py.typed
  ([`5c13b6f`](https://github.com/arkitektio/fluss-next/commit/5c13b6fae34e29551a1afedcd69e36e909b56989))

### Features

- Update version to 0.5.0 and refactor NodeWithError class in tests
  ([`7cf7647`](https://github.com/arkitektio/fluss-next/commit/7cf7647d585c3e6d3bb949d06894ef8bdf0790b3))


## v0.5.0 (2025-05-10)

### Features

- Add integration tests and configuration for Fluss workspace creation
  ([`82c07d3`](https://github.com/arkitektio/fluss-next/commit/82c07d35117d6b03751bef78b768a95441b870ea))

- Created a new configuration file `fluss.yaml` for database, Django, Redis, and S3 settings. -
  Implemented an integration test for workspace creation in `test_create_workspace.py`.


## v0.4.0 (2025-05-04)

### Features

- Refactor port tests to separate integer and float port validations
  ([`724d077`](https://github.com/arkitektio/fluss-next/commit/724d077b19f497fbe41716a530df190f796d3309))


## v0.3.0 (2025-05-04)

### Features

- Add initial tests for the inputs module
  ([`058d1fc`](https://github.com/arkitektio/fluss-next/commit/058d1fc1f102411876dbcc27645ad4e254a65a8c))


## v0.2.0 (2025-02-20)
