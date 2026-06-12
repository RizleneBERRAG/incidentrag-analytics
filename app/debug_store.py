from app.store import ChromaStore

store = ChromaStore()
store.ensure_collection()

data = store.collection.get()

print("TOTAL IDS:", len(data["ids"]))
print("EXEMPLE:", data["ids"][:5])