Quiz Service Documentation
==========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   openapi

Модули
======

.. automodule:: app.models
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: app.serializers
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: app.services
   :members:
   :undoc-members:

.. automodule:: app.repositories
   :members:
   :undoc-members:

.. automodule:: app.consumers
   :members:
   :undoc-members:

.. automodule:: app.observer_pattern
   :members:
   :undoc-members:

REST API (ViewSet)
------------------

Описание HTTP-эндпоинтов генерируется из кода через **drf-spectacular** и
доступно в разделе :doc:`openapi` (встроенный ``schema.yml``) и в Swagger UI
по адресу ``/api/docs/`` на запущенном сервере. Полный ``automodule`` для
``app.views`` не используется, чтобы сборка Sphinx не обращалась к БД при
документировании атрибутов вроде ``queryset``.