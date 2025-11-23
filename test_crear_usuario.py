"""
Script de prueba para verificar endpoint de creación de usuario
"""
import requests
import json

# URL del endpoint
url = "http://localhost:8000/api/v1/usuarios/crearUsuarioRol"

# Datos del usuario (exactamente como los envía el frontend)
datos_usuario = {
    "email": "testeco@empresa.com",
    "nombre": "TestECO",
    "rol": "viewer",
    "telefono": "",
    "departamento": "S/N",
    "contrasena": "123qwe"
}

# Primero necesitamos login para obtener el token
login_url = "http://localhost:8000/api/v1/auth/login"
login_data = {
    "email": "admin@empresa.com",
    "contrasena": "admin123"
}

print("🔐 Iniciando sesión como admin...")
try:
    response_login = requests.post(login_url, json=login_data)
    if response_login.status_code == 200:
        token = response_login.json()["access_token"]
        print(f"✅ Token obtenido: {token[:20]}...")
        
        # Ahora crear el usuario
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("\n👤 Creando usuario...")
        print(f"Datos: {json.dumps(datos_usuario, indent=2)}")
        
        response = requests.post(url, json=datos_usuario, headers=headers)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📄 Respuesta:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 201:
            print("\n✅ ¡Usuario creado exitosamente!")
        else:
            print("\n❌ Error al crear usuario")
    else:
        print(f"❌ Error en login: {response_login.status_code}")
        print(response_login.json())
        
except Exception as e:
    print(f"❌ Error: {e}")
