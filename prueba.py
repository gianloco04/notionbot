from notion_client import Client
import json

notion = Client(auth="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")

# IDs

supasend_db_id = "237d54d6757581e1952fe0133d4871d6"
todo_db_id = "236d54d67575812a89c1dadd08a74f24"

# 1. Obtener la última página creada en Supasend
response = notion.databases.query(
    database_id=supasend_db_id,
    sorts=[{"timestamp": "created_time", "direction": "descending"}],
    page_size=1
)

if not response["results"]:
    print("No se encontraron páginas en la base Supasend.")
    exit()

pagina_supasend = response["results"][0]
pagina_id = pagina_supasend["id"]

# 2. Obtener los bloques de contenido de esa página
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
    parent={"database_id": todo_db_id},
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

print(f"✅ Página creada en la To Do List con título: '{titulo}'")

# 5. Archivar (borrar) la página de Supasend
notion.pages.update(
    page_id=pagina_id,
    archived=True
)

print(f"🗑️ Página original de Supasend archivada correctamente.")