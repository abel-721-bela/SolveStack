try:
    from sentence_transformers import SentenceTransformer
    print("Loading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
