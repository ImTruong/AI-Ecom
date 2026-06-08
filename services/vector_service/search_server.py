import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer


PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000/api/products/").rstrip("/") + "/"
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "products")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
PORT = int(os.getenv("SEARCH_SERVER_PORT", "8002"))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)


def qdrant_search(query_vector, limit):
    if hasattr(client, "search"):
        return client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
    if hasattr(client, "search_points"):
        return client.search_points(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
    search_request = models.SearchRequest(
        vector=query_vector,
        limit=limit,
        with_payload=True,
        with_vector=False,
    )
    response = client.http.search_api.search_points(
        collection_name=COLLECTION_NAME,
        search_request=search_request,
    )
    return response.result


def fetch_products():
    try:
        response = requests.get(PRODUCT_SERVICE_URL, timeout=8)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return {int(p["id"]): normalize_product_payload(p) for p in data if p.get("id") is not None}
    except Exception as exc:
        print(f"Product enrichment failed: {exc}")
    return {}


def normalize_product_payload(product):
    if not isinstance(product, dict):
        return {}
    normalized = dict(product)
    product_type = str(normalized.get("product_type") or "").strip().lower()
    if not product_type or product_type == "generic":
        normalized["product_type"] = infer_product_type(normalized)
    return normalized


def infer_product_type(product):
    text = " ".join(str(product.get(key) or "") for key in ["category", "name", "description", "product_type"]).lower()
    if any(word in text for word in ["book", "novel", "python", "programming"]):
        return "book"
    if any(word in text for word in ["clothing", "hoodie", "jeans", "t-shirt", "shirt", "cotton", "denim"]):
        return "clothes"
    if any(word in text for word in ["shoe", "sneaker", "boots"]):
        return "shoes"
    if any(word in text for word in ["furniture", "sofa", "desk", "chair", "table"]):
        return "furniture"
    if any(word in text for word in ["cosmetic", "serum", "cleansing", "foam", "cream"]):
        return "cosmetic"
    if any(word in text for word in ["toy", "puzzle", "games"]):
        return "toy"
    if any(word in text for word in ["sport", "fitness"]):
        return "sport_equipment"
    if any(word in text for word in ["jewelry", "necklace", "ring", "wallet", "sunglasses", "accessories"]):
        return "accessory"
    if any(word in text for word in ["laptop", "phone", "electronics", "smartwatch", "camera", "headphone"]):
        return "electronic"
    if any(word in text for word in ["food", "snack", "drink"]):
        return "food"
    return "accessory"


class SearchHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.write_json({"success": True, "service": "qdrant-search"})
            return
        if parsed.path != "/api/recommendations/search":
            self.write_json({"success": False, "error": "Not found"}, status=404)
            return

        params = parse_qs(parsed.query)
        query = (params.get("query") or [""])[0].strip()
        limit = int((params.get("limit") or ["12"])[0])
        limit = max(1, min(limit, 30))
        if not query:
            self.write_json({"success": False, "query": query, "recommendations": []})
            return

        try:
            vector = embedding_model.encode(query).tolist()
            results = qdrant_search(vector, limit)
            product_map = fetch_products()
            recommendations = []
            for result in results:
                product_id = int(result.id)
                payload = product_map.get(product_id) or normalize_product_payload(result.payload or {})
                recommendations.append(
                    {
                        "id": product_id,
                        "score": float(result.score),
                        "payload": payload,
                        "source": "qdrant",
                        "reason": "Semantic vector search via Qdrant",
                    }
                )
            self.write_json(
                {
                    "success": bool(recommendations),
                    "query": query,
                    "strategy": "qdrant_semantic_search",
                    "recommendations": recommendations,
                }
            )
        except Exception as exc:
            self.write_json({"success": False, "error": str(exc), "recommendations": []}, status=500)

    def log_message(self, fmt, *args):
        return

    def write_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"Starting Qdrant semantic search server on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), SearchHandler).serve_forever()
