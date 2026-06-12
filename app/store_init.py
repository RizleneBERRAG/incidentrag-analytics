from app.store import ChromaStore

def main():
    store = ChromaStore()
    store.ensure_collection()
    print("Chroma initialisé en local ✔")

if __name__ == "__main__":
    main()