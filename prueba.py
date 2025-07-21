from notion_client import Client
import os

# Leer variables de entorno
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ORIGEN_ID = os.getenv("DATABASE_ORIGEN_ID")
DATABASE_DESTINO_ID = os.getenv("DATABASE_DESTINO_ID")

print("NOTION_TOKEN:", "OK" if NOTION_TOKEN else "FALTA")
print("DATABASE_ORIGEN_ID:", DATABASE_ORIGEN_ID)
print("DATABASE_DESTINO_ID:", DATABASE_DESTINO_ID)

notion = Client(auth=NOTION_TOKEN)

# 1. Obtener todas las páginas activas en Supasend
response = notion.databases.query(
    database_id=DATABASE_ORIGEN_ID,
    filter={"property": "archived", "checkbox": {"equals": False}},
    sorts=[{"timestamp": "created_time", "direction": "ascending"}]
)

paginas = response.get("results", [])

if not paginas:
    print("❌ No se encontraron páginas en la base Supasend.")
    exit()

print(f"🔄 Procesando {len(paginas)} páginas...")

for pagina in paginas:
    pagina_id = pagina["id"]

    # 2. Obtener los bloques de contenido
    bloques = notion.blocks.children.list(block_id=pagina_id)["results"]

    # 3. Buscar el primer bloque de texto
    titulo = "Sin título"
    for bloque in bloques:
        tipo = bloque["type"]
        contenido = bloque[tipo]

        if "rich_text" in contenido and contenido["rich_text"]:
            titulo = contenido["rich_text"][0]["plain_text"]
            break

    # 4. Crear nueva página en la To Do List
    nueva_pagina = notion.pages.create(
        parent={"database_id": DATABASE_DESTINO_ID},
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

    print(f"✅ '{titulo}' copiado")

    # 5. Archivar página original
    notion.pages.update(page_id=pagina_id, archived=True)
    print(f"🗑️ Página {pagina_id} archivada")

