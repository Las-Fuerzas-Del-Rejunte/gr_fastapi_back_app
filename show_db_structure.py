"""
Script para mostrar la estructura completa de la base de datos MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def show_database_structure():
    # Conectar a MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["sistema_reclamos"]
    
    # Obtener todas las colecciones
    collections = await db.list_collection_names()
    
    print("=" * 70)
    print(f"📊 BASE DE DATOS: sistema_reclamos")
    print(f"📋 Total de colecciones: {len(collections)}")
    print("=" * 70)
    
    for coll_name in sorted(collections):
        print(f"\n{'=' * 70}")
        print(f"📁 COLECCIÓN: {coll_name}")
        print("=" * 70)
        
        collection = db[coll_name]
        
        # Contar documentos
        count = await collection.count_documents({})
        print(f"📊 Total documentos: {count}")
        
        if count > 0:
            # Obtener un documento de muestra
            sample = await collection.find_one()
            
            if sample:
                print(f"\n📝 CAMPOS:")
                print("-" * 70)
                
                for key, value in sample.items():
                    value_type = type(value).__name__
                    
                    # Mostrar información más detallada según el tipo
                    if isinstance(value, dict):
                        print(f"  • {key:25s} → {value_type:15s} (objeto con {len(value)} campos)")
                    elif isinstance(value, list):
                        list_len = len(value)
                        if list_len > 0:
                            first_item_type = type(value[0]).__name__
                            print(f"  • {key:25s} → {value_type:15s} (array de {list_len} elementos, tipo: {first_item_type})")
                        else:
                            print(f"  • {key:25s} → {value_type:15s} (array vacío)")
                    else:
                        # Truncar valores largos
                        str_value = str(value)
                        if len(str_value) > 40:
                            str_value = str_value[:37] + "..."
                        print(f"  • {key:25s} → {value_type:15s} = {str_value}")
        else:
            print("\n⚠️  Colección vacía")
    
    print("\n" + "=" * 70)
    print("✅ Estructura completa mostrada")
    print("=" * 70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(show_database_structure())
