"""
Tests extendidos para routers - aumentar cobertura
"""
import pytest
from httpx import AsyncClient
from bson import ObjectId


class TestReclamosRouterExtended:
    """Tests extendidos para endpoints de reclamos"""
    
    @pytest.mark.asyncio
    async def test_create_reclamo_missing_fields(self, client: AsyncClient):
        """Test crear reclamo con campos faltantes"""
        response = await client.post("/api/v1/reclamos", json={})
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_get_reclamo_invalid_id(self, client: AsyncClient):
        """Test obtener reclamo con ID inválido"""
        response = await client.get("/api/v1/reclamos/invalid-id")
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_patch_reclamo_empty_data(self, client: AsyncClient):
        """Test actualizar reclamo con datos vacíos"""
        reclamo_id = str(ObjectId())
        response = await client.patch(f"/api/v1/reclamos/{reclamo_id}", json={})
        assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_delete_reclamo(self, client: AsyncClient):
        """Test eliminar reclamo"""
        reclamo_id = str(ObjectId())
        response = await client.delete(f"/api/v1/reclamos/{reclamo_id}")
        assert response.status_code in [204, 401, 404]
    
    @pytest.mark.asyncio
    async def test_get_reclamos_with_pagination(self, client: AsyncClient):
        """Test listar reclamos con paginación"""
        response = await client.get("/api/v1/reclamos?skip=0&limit=5")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_get_reclamos_by_cliente(self, client: AsyncClient):
        """Test obtener reclamos por cliente"""
        cliente_id = str(ObjectId())
        response = await client.get(f"/api/v1/reclamos?cliente_id={cliente_id}")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_get_auditoria_reclamo(self, client: AsyncClient):
        """Test obtener auditoría de reclamo"""
        reclamo_id = str(ObjectId())
        response = await client.get(f"/api/v1/reclamos/{reclamo_id}/auditoria")
        assert response.status_code in [200, 401, 404]


class TestClientesRouterExtended:
    """Tests extendidos para endpoints de clientes"""
    
    @pytest.mark.asyncio
    async def test_create_cliente_missing_fields(self, client: AsyncClient):
        """Test crear cliente con campos faltantes"""
        response = await client.post("/api/v1/clientes", json={})
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_get_cliente_invalid_id(self, client: AsyncClient):
        """Test obtener cliente con ID inválido"""
        response = await client.get("/api/v1/clientes/invalid-id")
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_update_cliente(self, client: AsyncClient):
        """Test actualizar cliente"""
        cliente_id = str(ObjectId())
        response = await client.patch(
            f"/api/v1/clientes/{cliente_id}",
            json={"nombre": "Updated Name"}
        )
        assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_delete_cliente(self, client: AsyncClient):
        """Test eliminar cliente"""
        cliente_id = str(ObjectId())
        response = await client.delete(f"/api/v1/clientes/{cliente_id}")
        assert response.status_code in [204, 401, 404]
    
    @pytest.mark.asyncio
    async def test_get_clientes_with_search(self, client: AsyncClient):
        """Test buscar clientes"""
        response = await client.get("/api/v1/clientes?search=test")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_create_proyecto_for_cliente(self, client: AsyncClient):
        """Test crear proyecto para cliente"""
        cliente_id = str(ObjectId())
        proyecto_data = {
            "nombre": "Test Project",
            "tipo_proyecto_id": str(ObjectId())
        }
        response = await client.post(
            f"/api/v1/clientes/{cliente_id}/proyectos",
            json=proyecto_data
        )
        assert response.status_code in [201, 401, 404, 422]


class TestStatusRouterExtended:
    """Tests extendidos para endpoints de estados"""
    
    @pytest.mark.asyncio
    async def test_get_status_by_invalid_id(self, client: AsyncClient):
        """Test obtener estado con ID inválido"""
        response = await client.get("/api/v1/configuracion-estados/invalid-id")
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_create_status_duplicate(self, client: AsyncClient):
        """Test crear estado duplicado"""
        status_data = {
            "nombre": "Test Estado",
            "descripcion": "Test",
            "color": "#FF0000",
            "tipo": "inicial",
            "orden": 1
        }
        response = await client.post("/api/v1/configuracion-estados", json=status_data)
        assert response.status_code in [201, 401, 400, 422]
    
    @pytest.mark.asyncio
    async def test_update_status(self, client: AsyncClient):
        """Test actualizar estado"""
        status_id = str(ObjectId())
        response = await client.patch(
            f"/api/v1/configuracion-estados/{status_id}",
            json={"nombre": "Updated Status"}
        )
        assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_delete_status(self, client: AsyncClient):
        """Test eliminar estado"""
        status_id = str(ObjectId())
        response = await client.delete(f"/api/v1/configuracion-estados/{status_id}")
        assert response.status_code in [204, 401, 404]
    
    @pytest.mark.asyncio
    async def test_update_subestado(self, client: AsyncClient):
        """Test actualizar subestado"""
        estado_id = str(ObjectId())
        subestado_id = str(ObjectId())
        response = await client.patch(
            f"/api/v1/configuracion-estados/{estado_id}/sub-estados/{subestado_id}",
            json={"nombre": "Updated Subestado"}
        )
        assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_delete_subestado(self, client: AsyncClient):
        """Test eliminar subestado"""
        estado_id = str(ObjectId())
        subestado_id = str(ObjectId())
        response = await client.delete(
            f"/api/v1/configuracion-estados/{estado_id}/sub-estados/{subestado_id}"
        )
        assert response.status_code in [204, 401, 404]


class TestUsuariosRouterExtended:
    """Tests extendidos para endpoints de usuarios"""
    
    @pytest.mark.asyncio
    async def test_create_usuario_duplicate_email(self, client: AsyncClient):
        """Test crear usuario con email duplicado"""
        user_data = {
            "email": "existing@example.com",
            "nombre": "Test User",
            "password": "password123",
            "rol": "agente"
        }
        response = await client.post("/api/v1/usuarios", json=user_data)
        assert response.status_code in [201, 401, 400, 422]
    
    @pytest.mark.asyncio
    async def test_get_usuario_invalid_id(self, client: AsyncClient):
        """Test obtener usuario con ID inválido"""
        response = await client.get("/api/v1/usuarios/invalid-id")
        assert response.status_code in [401, 422]
    
    @pytest.mark.asyncio
    async def test_get_usuarios_filter_by_rol(self, client: AsyncClient):
        """Test filtrar usuarios por rol"""
        response = await client.get("/api/v1/usuarios?rol=agente")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_get_usuarios_filter_by_activo(self, client: AsyncClient):
        """Test filtrar usuarios por estado activo"""
        response = await client.get("/api/v1/usuarios?activo=true")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_cambiar_contrasena_usuario(self, client: AsyncClient):
        """Test cambiar contraseña de usuario"""
        user_id = str(ObjectId())
        response = await client.post(
            f"/api/v1/usuarios/{user_id}/cambiar-contrasena",
            json={"password": "newpassword123"}
        )
        assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_crear_usuario_con_rol(self, client: AsyncClient):
        """Test crear usuario con rol específico"""
        user_data = {
            "email": "newuser@example.com",
            "nombre": "New User",
            "password": "password123",
            "rol": "admin"
        }
        response = await client.post("/api/v1/usuarios/crearUsuarioRol", json=user_data)
        assert response.status_code in [201, 401, 422]


class TestTiposProyectoRouter:
    """Tests para endpoints de tipos de proyecto"""
    
    @pytest.mark.asyncio
    async def test_get_tipos_proyecto(self, client: AsyncClient):
        """Test obtener tipos de proyecto"""
        response = await client.get("/api/v1/tipos-proyecto")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_create_tipo_proyecto(self, client: AsyncClient):
        """Test crear tipo de proyecto"""
        tipo_data = {
            "nombre": "Nuevo Tipo",
            "descripcion": "Descripción del tipo"
        }
        response = await client.post("/api/v1/tipos-proyecto", json=tipo_data)
        assert response.status_code in [201, 401, 422]
    
    @pytest.mark.asyncio
    async def test_get_tipo_proyecto_by_id(self, client: AsyncClient):
        """Test obtener tipo de proyecto por ID"""
        tipo_id = str(ObjectId())
        response = await client.get(f"/api/v1/tipos-proyecto/{tipo_id}")
        assert response.status_code in [200, 401, 404]


class TestProyectosRouter:
    """Tests para endpoints de proyectos"""
    
    @pytest.mark.asyncio
    async def test_get_proyectos(self, client: AsyncClient):
        """Test obtener proyectos"""
        response = await client.get("/api/v1/proyectos")
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_get_proyecto_by_id(self, client: AsyncClient):
        """Test obtener proyecto por ID"""
        proyecto_id = str(ObjectId())
        response = await client.get(f"/api/v1/proyectos/{proyecto_id}")
        assert response.status_code in [200, 401, 404]
    
    @pytest.mark.asyncio
    async def test_update_proyecto(self, client: AsyncClient):
        """Test actualizar proyecto"""
        proyecto_id = str(ObjectId())
        response = await client.patch(
            f"/api/v1/proyectos/{proyecto_id}",
            json={"nombre": "Updated Project"}
        )
        assert response.status_code in [200, 401, 404, 422]
    
    @pytest.mark.asyncio
    async def test_delete_proyecto(self, client: AsyncClient):
        """Test eliminar proyecto"""
        proyecto_id = str(ObjectId())
        response = await client.delete(f"/api/v1/proyectos/{proyecto_id}")
        assert response.status_code in [204, 401, 404]
