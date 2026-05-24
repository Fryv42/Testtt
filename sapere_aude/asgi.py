import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sapere_aude.settings')
from django.core.asgi import get_asgi_application
django_http_app = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from app.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_http_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})