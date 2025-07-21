from notion_client import Client
import os
from datetime import datetime

# Leer variables de entorno
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ORIGEN_ID = os.getenv("DATABASE_ORIGEN_ID")
DATABASE_DESTINO_ID = os.getenv("DATABASE_DESTINO_ID")

print(f"[{datetime.now()}] Iniciando bot...")
print("NOTION_TOKEN:", "OK" if NOTION_TOKEN else "FALTA")
print("DATABASE_ORIGEN_ID:", DATABASE_ORIGEN_ID)
print("DATABASE_DESTINO_ID:", DATABASE_DESTINO_ID)

if not all([NOTION_TOKEN, DATABASE_ORIGEN_ID, DATABASE_DESTINO_ID]):
    print("❌ Faltan variables de entorno")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

def obtener_todas_las_paginas(database_id):
    """Obtiene TODAS las páginas de una base de datos, manejando paginación"""
    todas_las_paginas = []
    start_cursor = None
    
    while True:
        query_params = {
            "database_id": database_id,
            "sorts": [{"timestamp": "created_time", "direction": "descending"}],
            "page_size": 100  # Máximo permitido por Notion
        }
        
        if start_cursor:
            query_params["start_cursor"] = start_cursor
            
        response = notion.databases.query(**query_params)
        paginas = response.get("results", [])
        todas_las_paginas.extend(paginas)
        
        # Si no hay más páginas, salir del bucle
        if not response.get("has_more", False):
            break
            
        start_cursor = response.get("next_cursor")
    
    return todas_las_paginas

def obtener_titulo_de_pagina(pagina_id):
    """Obtiene el título de una página buscando en sus bloques"""
    try:
        bloques = notion.blocks.children.list(block_id=pagina_id)["results"]
        
        for bloque in bloques:
            tipo = bloque["type"]
            contenido = bloque.get(tipo, {})
            
            if "rich_text" in contenido and contenido["rich_text"]:
                return contenido["rich_text"][0]["plain_text"]
        
        return "Sin título"
    except Exception as e:
        print(f"❌ Error obteniendo título de {pagina_id}: {e}")
        return "Error al obtener título"

def crear_pagina_destino(titulo, database_destino_id):
    """Crea una nueva página en la base de datos destino"""
    try:
        nueva_pagina = notion.pages.create(
            parent={"database_id": database_destino_id},
            properties={
                "Name": {
                    "title": [{
                        "text": {
                            "content": titulo
                        }
                    }]
                }
            },
        )
        return nueva_pagina["id"]
    except Exception as e:
        print(f"❌ Error creando página '{titulo}': {e}")
        return None

def archivar_pagina(pagina_id):
    """Archiva una página"""
    try:
        notion.pages.update(page_id=pagina_id, archived=True)
        return True
    except Exception as e:
        print(f"❌ Error archivando página {pagina_id}: {e}")
        return False

# SCRIPT PRINCIPAL
try:
    # 1. Obtener TODAS las páginas activas en la base origen
    print("🔍 Obteniendo páginas de la base origen...")
    paginas = obtener_todas_las_paginas(DATABASE_ORIGEN_ID)
    
    if not paginas:
        print("ℹ️ No se encontraron páginas en la base origen.")
        exit(0)
    
    print(f"📋 Encontradas {len(paginas)} páginas para procesar")
    
    # 2. Procesar cada página
    exitosos = 0
    errores = 0
    
    for i, pagina in enumerate(paginas, 1):
        pagina_id = pagina["id"]
        
        print(f"\n[{i}/{len(paginas)}] Procesando página {pagina_id}")
        
        # Obtener título
        titulo = obtener_titulo_de_pagina(pagina_id)
        print(f"📄 Título: '{titulo}'")
        
        # Crear nueva página en destino
        nueva_pagina_id = crear_pagina_destino(titulo, DATABASE_DESTINO_ID)
        
        if nueva_pagina_id:
            print(f"✅ Página creada en destino: {nueva_pagina_id}")
            
            # Archivar página original
            if archivar_pagina(pagina_id):
                print(f"🗑️ Página original archivada")
                exitosos += 1
            else:
                errores += 1
        else:
            errores += 1
    
    # 3. Resumen final
    print(f"\n📊 RESUMEN:")
    print(f"✅ Páginas procesadas exitosamente: {exitosos}")
    print(f"❌ Errores: {errores}")
    print(f"📋 Total procesadas: {len(paginas)}")
    
except Exception as e:
    print(f"💥 Error fatal: {e}")
    exit(1)

print(f"[{datetime.now()}] Bot finalizado")
