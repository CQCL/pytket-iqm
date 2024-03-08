Changelog
~~~~~~~~~

Unreleased
----------

* Updated pytket version requirement to 1.25.
* Updated iqm-client version requirement to 17.1.


0.11.0 (January 2024)
---------------------

* Updated pytket version requirement to 1.24.
* Python 3.12 support added, 3.9 dropped.

0.10.0 (January 2024)
---------------------

* Updated pytket version requirement to 1.23.
* Add some additional post-routing optimisations to the default compilation pass for `optimisation_level=2`.
* Updated iqm-client version requirement to 15.2.

0.9.0 (November 2023)
---------------------

* Updated pytket version requirement to 1.22.

0.8.0 (October 2023)
--------------------

* Don't include ``SimplifyInitial`` in default passes; instead make it an option
  to ``process_circuits()``.
* Updated pytket version requirement to 1.21.

0.7.0 (October 2023)
--------------------

* Update pytket version requirement to 1.20.
* Update iqm-client version requirement to 14.0.
* Fix job status checks.
* Add support for token-based authentication.

0.6.0 (March 2023)
------------------

* Updated pytket version requirement to 1.13.
* Updated iqm-client version requirement to 11.8.
* New method ``IQMBackend.get_metadata()`` for reteieving metadata associated
  with a ``ResultHandle``.

0.5.0 (November 2022)
---------------------

* Updated iqm-client version requirement to 9.1.
* IQMBackend initializer now does not accept a settings file.
* IQMBackend initializer now retrieves device name and qubit names from backend
  server instead of configuration file.
* IQMBackend initializer now retrieves qubit coupling (connectivity) and native
  gateset from backend server instead of hard-coded constants.
* Updated pytket version requirement to 1.8.

0.4.0 (August 2022)
-------------------

* Updated iqm-client version requirement to 4.3.
* IQMBackend initializer now requires an authentication server URL, which may be
  stored in config.
* Updated pytket version requirement to 1.5.
* Support for python 3.10.

0.3.0 (April 2022)
------------------

* Updated pytket version requirement to 1.1.
* Rename ``device`` parameter for ``IQMBackend`` to ``settings``.
* Remove default values for URL and settings file.
* Add ``NoBarriersPredicate`` to ``IQMBackend``.

0.2.0 (March 2022)
------------------

* Updated pytket version requirement to 1.0.

0.1.0 (February 2022)
---------------------

* Initial release.
