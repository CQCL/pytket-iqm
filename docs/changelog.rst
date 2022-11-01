Changelog
~~~~~~~~~

0.5.0 (October 2022)
-------------------

* Updated iqm-client version requirement to 9.1.
* IQMBackend initializer now does not accept a settings file.
* IQMBackend initializer now retrieves device name and qubit names from backend
  server instead of configuration file.
* IQMBackend initializer now retrieves qubit coupling (connectivity) and native
gateset from backend server instead of hard-coded constants.

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
