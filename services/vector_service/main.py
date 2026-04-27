import requests
import time
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Configuration
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:8000/api/products/')
QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
COLLECTION_NAME = "products"

def fetch_products(retries=10, delay=5):
    print(f"🔍 Fetching products from {PRODUCT_SERVICE_URL}...")
    for i in range(retries):
        try:
            response = requests.get(PRODUCT_SERVICE_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ Attempt {i+1}/{retries} failed: {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                print(f"❌ Error fetching products after {retries} attempts.")
                return []

def format_product_text(p):
    """Combine all product-relevant fields into a single descriptive string."""
    parts = [
        f"Product Name: {p.get('name', '')}",
        f"Category: {p.get('category', '')}",
        f"Type: {p.get('product_type', '')}",
    ]

    if p.get('description'):
        parts.append(f"Description: {p['description']}")

    if p.get('attributes') and isinstance(p.get('attributes'), dict):
        attrs = ", ".join([f"{k}: {v}" for k, v in p['attributes'].items()])
        if attrs:
            parts.append(f"Attributes: {attrs}")

    if p.get('variants') and isinstance(p.get('variants'), list):
        variant_names = ", ".join([v.get('name', '') for v in p['variants'] if v.get('name')])
        if variant_names:
            parts.append(f"Options: {variant_names}")

    skip_keys = {
        'id', 'name', 'description', 'price', 'image_url', 'category',
        'category_id', 'supplier_id', 'created_at', 'updated_at',
        'product_type', 'attributes', 'variants'
    }
    for key in sorted(p.keys()):
        if key in skip_keys:
            continue
        value = p.get(key)
        if value in (None, '', [], {}):
            continue
        if isinstance(value, dict):
            extra = ", ".join([f"{k}: {v}" for k, v in value.items()])
            parts.append(f"{key}: {extra}")
        elif isinstance(value, list):
            parts.append(f"{key}: {', '.join([str(v) for v in value if v])}")
        else:
            parts.append(f"{key}: {value}")

    return ". ".join([p for p in parts if p]) + "."

def main():
    print("🚀 Starting Vector Service...")
    
    # Initialize model
    print("🧠 Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize Qdrant client
    print(f"📡 Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Ensure collection exists
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        print(f"💎 Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    # 1. Fetch products
    products = fetch_products()
    if not products:
        print("📭 No products found to index.")
        return

    print(f"📝 Processing {len(products)} products...")
    
    points = []
    for p in products:
        text = format_product_text(p)
        print(f"  - Embedding: {p['name']}")
        
        # Generate embedding
        vector = model.encode(text).tolist()
        
        # Create Qdrant point
        points.append(PointStruct(
            id=p['id'],
            vector=vector,
            payload={
                "id": p['id'],
                "name": p['name'],
                "category": p['category'],
                "product_type": p['product_type'],
                "price": p['price'],
                "image_url": p.get('image_url', ''),
                "raw_text": text
            }
        ))

    # 2. Upload to Qdrant
    print(f"📤 Uploading {len(points)} points to Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    print("✅ Vector synchronization complete!")

if __name__ == "__main__":
    main()
