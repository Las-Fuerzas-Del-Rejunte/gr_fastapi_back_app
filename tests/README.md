# Tests

Este directorio contiene los tests del proyecto.

## Estructura

```
tests/
├── __init__.py
├── conftest.py          # Configuración y fixtures globales
├── test_main.py         # Tests de endpoints principales
├── test_auth.py         # Tests de autenticación
├── test_security.py     # Tests de funciones de seguridad
├── test_config.py       # Tests de configuración
├── test_schemas.py      # Tests de validación de schemas
└── test_exceptions.py   # Tests de excepciones personalizadas
```

## Ejecución de Tests

### Ejecutar todos los tests
```powershell
python -m pytest
```

### Ejecutar con reporte de cobertura
```powershell
python -m pytest --cov=app --cov-report=html
```

### Ejecutar tests específicos
```powershell
# Por archivo
python -m pytest tests/test_main.py

# Por clase
python -m pytest tests/test_main.py::TestMainEndpoints

# Por función
python -m pytest tests/test_main.py::TestMainEndpoints::test_root_endpoint
```

### Ver reporte de cobertura
```powershell
# Abrir reporte HTML
start htmlcov/index.html
```

## Markers

- `@pytest.mark.asyncio` - Tests asíncronos
- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.slow` - Tests lentos

## Fixtures Disponibles

- `client` - Cliente HTTP async para tests
- `mock_mongodb` - Mock de MongoDB
- `mock_beanie` - Mock de Beanie
- `mock_current_user` - Usuario autenticado mock
- `mock_auth_token` - Token JWT mock
- `auth_headers` - Headers de autenticación

## Cobertura Objetivo

El objetivo es mantener una cobertura mínima del 60% del código.

## Buenas Prácticas

1. **Nombres descriptivos**: Los tests deben tener nombres que describan claramente qué están probando
2. **Arrange-Act-Assert**: Estructura clara de preparación, ejecución y validación
3. **Tests independientes**: Cada test debe ser independiente y no depender del orden de ejecución
4. **Mocks apropiados**: Usar mocks para dependencias externas (BD, APIs, etc.)
5. **Tests rápidos**: Los tests unitarios deben ejecutarse rápidamente
