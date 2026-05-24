OpenAPI (Swagger)
=================

Интерактивная документация API доступна при запущенном сервере по адресу
``/api/docs/`` (Swagger UI). Сырая схема OpenAPI 3 — по адресу ``/api/schema/``.

При сборке Sphinx файл ``schema.yml`` генерируется командой ``make html`` в
каталоге ``docs`` (см. ``docs/Makefile``) и подключается ниже.

.. note::

   Файл ``_static/schema.yml`` создаётся автоматически и не обязан храниться в
   репозитории; перед ``make html`` он пересобирается из кода Django.

.. literalinclude:: ../_static/schema.yml
   :language: yaml
