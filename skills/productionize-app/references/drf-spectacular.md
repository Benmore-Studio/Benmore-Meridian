# DRF Spectacular Setup Guide

## Installation

```bash
pip install drf-spectacular
# Add to requirements.txt
```

## settings/base.py

```python
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Cattle Management API',
    'DESCRIPTION': 'Full-stack cattle feedlot management system API',
    'VERSION': '1.4.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}
```

## URL Configuration (cattle/urls.py)

```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    ...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

## @extend_schema Examples

### Simple ViewSet
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(tags=['Lots'])
class LotViewSet(viewsets.ModelViewSet):
    ...
    
    @extend_schema(
        summary="Get lot closeout report",
        parameters=[OpenApiParameter('interest_rate', float, description='Override interest rate')],
    )
    @action(detail=True, methods=['get'])
    def closeout(self, request, pk=None):
        ...
```

### Auth endpoints
```python
@extend_schema(tags=['Auth'], summary="Login with email + password")
class LoginView(APIView):
    ...
```

### Skip internal endpoints
```python
@extend_schema(exclude=True)
class InternalHealthCheckView(APIView):
    ...
```

## Smoke Test

```bash
cd backend
python manage.py spectacular --color --validate-examples
# Should print "Schema generation successful" with no errors
```

If errors appear, they are usually missing serializer fields or unresolved FK references.
Add `@extend_schema(exclude=True)` to any problematic internal endpoint to skip it.

## Common Fixes

| Error | Fix |
|-------|-----|
| `Unable to guess serializer` | Add `serializer_class` or `@extend_schema(responses=MySerializer)` |
| `circular import` | Use string reference: `'myapp.serializers.MySerializer'` |
| `400 on schema endpoint` | Check `DEFAULT_AUTHENTICATION_CLASSES` — schema endpoint should allow anonymous |
