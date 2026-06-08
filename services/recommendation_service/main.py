from __future__ import annotations

import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import numpy as np
import requests
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase

try:
    import tensorflow as tf
except Exception:  # Keeps the API alive if the image is still missing TensorFlow.
    tf = None


app = FastAPI(title="Recommendation Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TRACKING_SERVICE_URL = os.getenv("TRACKING_SERVICE_URL", "http://tracking-service:8000/api/tracking/").rstrip("/") + "/"
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000/api/products/").rstrip("/") + "/"
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8000/api/cart/").rstrip("/") + "/"
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000/api/orders/").rstrip("/") + "/"
RECOMMENDATION_SEARCH_SERVICE_URL = os.getenv(
    "RECOMMENDATION_SEARCH_SERVICE_URL", "http://recommendation-search-service:8002"
).rstrip("/")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "products")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
MODEL_DIR = Path(os.getenv("RECOMMENDER_MODEL_DIR", "/app/AI/new"))
MODEL_PATH = Path(os.getenv("RECOMMENDER_MODEL_PATH", MODEL_DIR / "GRU_best_model.h5"))
ENCODER_PATH = Path(os.getenv("RECOMMENDER_ENCODER_PATH", MODEL_DIR / "encoders.pkl"))
SEQUENCE_LENGTH = int(os.getenv("RECOMMENDER_SEQUENCE_LENGTH", "20"))
CANDIDATE_LIMIT = int(os.getenv("RECOMMENDER_CANDIDATE_LIMIT", "30"))
DEFAULT_LIMIT = int(os.getenv("RECOMMENDER_DEFAULT_LIMIT", "10"))
QDRANT_CONTEXT_LIMIT = int(os.getenv("QDRANT_CONTEXT_LIMIT", "5"))
QDRANT_CONTEXT_TIMEOUT = float(os.getenv("QDRANT_CONTEXT_TIMEOUT", "2.5"))
MODEL_SCORE_LIMIT = int(os.getenv("RECOMMENDER_MODEL_SCORE_LIMIT", str(CANDIDATE_LIMIT)))

ACTION_WEIGHTS = {
    "pv": 1,
    "cart": 2,
    "buy": 3,
}


@dataclass(frozen=True)
class ProductSignal:
    product_id: int
    behavior: str
    timestamp: str = ""
    source: str = ""


class ProductClient:
    def list_products(self, limit: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            params = {"search": search} if search else None
            response = requests.get(PRODUCT_SERVICE_URL, params=params, timeout=8)
            response.raise_for_status()
            products = response.json()
            if not isinstance(products, list):
                return []
            products = [normalize_product_payload(product) for product in products]
            return products[:limit] if limit else products
        except Exception as exc:
            print(f"Product Service Error: {exc}")
            return []

    def get_product_map(self, product_ids: Iterable[int]) -> Dict[int, Dict[str, Any]]:
        wanted = {int(pid) for pid in product_ids if _to_int(pid)}
        if not wanted:
            return {}
        products = self.list_products()
        return {int(p["id"]): p for p in products if _to_int(p.get("id")) in wanted}


class GraphClient:
    def __init__(self) -> None:
        auth = (NEO4J_USER, NEO4J_PASSWORD) if NEO4J_USER and NEO4J_PASSWORD and NEO4J_PASSWORD != "none" else None
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=auth)

    def close(self) -> None:
        self.driver.close()

    def fetch_candidates(self, user_id: int, seed_ids: Sequence[int], excluded_ids: Set[int], limit: int) -> List[Dict[str, Any]]:
        if not seed_ids:
            return self.popular_products(limit)

        results: List[Dict[str, Any]] = []
        seen: Set[int] = set()
        for source, rel_type, weight in [
            ("other_users_bought", "BOUGHT", 3.0),
            ("other_users_added_to_cart", "ADDED_TO_CART", 2.0),
            ("other_users_viewed", "VIEWED", 1.0),
        ]:
            remaining = limit - len(results)
            if remaining <= 0:
                break
            rows = self._related_products(user_id, seed_ids, excluded_ids | seen, rel_type, source, weight, remaining)
            for row in rows:
                pid = _to_int(row.get("id"))
                if pid and pid not in seen:
                    seen.add(pid)
                    results.append(row)
        return results[:limit] if results else self.popular_products(limit, excluded_ids)

    def popular_products(self, limit: int, excluded_ids: Optional[Set[int]] = None) -> List[Dict[str, Any]]:
        excluded_ids = excluded_ids or set()
        query = """
        MATCH (p:Product)
        WHERE coalesce(p.is_active, true) = true AND NOT p.id IN $excluded_ids
        OPTIONAL MATCH (:User)-[b:BOUGHT]->(p)
        OPTIONAL MATCH (:User)-[c:ADDED_TO_CART]->(p)
        OPTIONAL MATCH (:User)-[v:VIEWED]->(p)
        WITH p, count(DISTINCT b) AS buys, count(DISTINCT c) AS carts, count(DISTINCT v) AS views
        RETURN p.id AS id,
               (buys * 3.0 + carts * 2.0 + views) AS graph_score,
               'popular' AS source,
               buys, carts, views
        ORDER BY graph_score DESC, p.id ASC
        LIMIT $limit
        """
        try:
            with self.driver.session() as session:
                return [dict(record) for record in session.run(query, excluded_ids=list(excluded_ids), limit=limit)]
        except Exception as exc:
            print(f"Neo4j popular query error: {exc}")
            return []

    def _related_products(
        self,
        user_id: int,
        seed_ids: Sequence[int],
        excluded_ids: Set[int],
        rel_type: str,
        source: str,
        weight: float,
        limit: int,
    ) -> List[Dict[str, Any]]:
        query = f"""
        MATCH (other:User)-[seed_action:ADDED_TO_CART]->(seed:Product)
        WHERE seed.id IN $seed_ids AND other.id <> $user_id
        MATCH (other)-[target:{rel_type}]->(p:Product)
        WHERE coalesce(p.is_active, true) = true
          AND NOT p.id IN $seed_ids
          AND NOT p.id IN $excluded_ids
          AND (
            seed_action.timestamp IS NULL
            OR target.timestamp IS NULL
            OR toString(target.timestamp) >= toString(seed_action.timestamp)
          )
        WITH p, count(DISTINCT other) AS users, count(target) AS interactions
        RETURN p.id AS id,
               (users * $weight + interactions) AS graph_score,
               $source AS source,
               users,
               interactions
        ORDER BY graph_score DESC, users DESC, p.id ASC
        LIMIT $limit
        """
        try:
            with self.driver.session() as session:
                return [
                    dict(record)
                    for record in session.run(
                        query,
                        user_id=user_id,
                        seed_ids=list(seed_ids),
                        excluded_ids=list(excluded_ids),
                        weight=weight,
                        source=source,
                        limit=limit,
                    )
                ]
        except Exception as exc:
            print(f"Neo4j {source} query error: {exc}")
            return []


class VectorSearchClient:
    def __init__(self) -> None:
        self.load_error = ""

    @property
    def ready(self) -> bool:
        return True

    def search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        if not query:
            return []
        try:
            points = self._scroll_points(limit=max(limit * 20, 1000))
            scored = []
            for point in points:
                payload = normalize_product_payload(point.get("payload") or {})
                score = self._keyword_score(query, payload)
                point_id = _to_int(point.get("id") or payload.get("id"))
                if score > 0 and point_id:
                    scored.append(
                        {
                            "id": point_id,
                            "score": score,
                            "payload": payload,
                            "source": "qdrant",
                            "reason": "Search result from Qdrant product index",
                        }
                    )
            scored.sort(key=lambda item: item["score"], reverse=True)
            return scored[:limit]
        except Exception as exc:
            print(f"Qdrant search error: {exc}")
            return []

    def _scroll_points(self, limit: int) -> List[Dict[str, Any]]:
        response = requests.post(
            f"http://{QDRANT_HOST}:{QDRANT_PORT}/collections/{QDRANT_COLLECTION}/points/scroll",
            json={"limit": limit, "with_payload": True, "with_vector": False},
            timeout=8,
        )
        response.raise_for_status()
        return (response.json().get("result") or {}).get("points") or []

    def _keyword_score(self, query: str, payload: Dict[str, Any]) -> float:
        terms = [term for term in query.lower().split() if term]
        if not terms:
            return 0.0
        text = " ".join(
            str(payload.get(key) or "")
            for key in ["name", "category", "product_type", "raw_text", "description"]
        ).lower()
        score = 0.0
        for term in terms:
            if term in text:
                score += 1.0
            if term and str(payload.get("name") or "").lower().find(term) >= 0:
                score += 2.0
        return score / max(len(terms), 1)


class PurchaseModel:
    def __init__(self) -> None:
        self.model = None
        self.encoders: Dict[str, Any] = {}
        self.load_error = ""
        self._load()

    @property
    def ready(self) -> bool:
        return self.model is not None and bool(self.encoders)

    def _load(self) -> None:
        if tf is None:
            self.load_error = "TensorFlow is not installed"
            return
        try:
            self.model = tf.keras.models.load_model(str(MODEL_PATH))
            with ENCODER_PATH.open("rb") as file:
                self.encoders = pickle.load(file)
            print(f"Loaded GRU recommender model from {MODEL_PATH}")
        except Exception as exc:
            self.load_error = str(exc)
            print(f"Could not load recommender model: {exc}")

    def predict(self, history: Sequence[ProductSignal], products: Dict[int, Dict[str, Any]], target_id: int) -> Optional[float]:
        if not self.ready:
            return None
        target_encoded = self._encode("item_encoder", target_id, offset=1)
        if target_encoded is None:
            return None

        encoded_behaviors: List[int] = []
        encoded_items: List[int] = []
        encoded_categories: List[int] = []
        for signal in history[-SEQUENCE_LENGTH:]:
            product = products.get(signal.product_id, {})
            behavior = self._encode("behavior_encoder", signal.behavior)
            item = self._encode("item_encoder", signal.product_id, offset=1)
            category = self._encode("category_encoder", product.get("category_id"), offset=1)
            if behavior is None or item is None or category is None:
                continue
            encoded_behaviors.append(behavior)
            encoded_items.append(item)
            encoded_categories.append(category)

        encoded_behaviors, encoded_items, encoded_categories = _left_pad(
            encoded_behaviors, encoded_items, encoded_categories, length=SEQUENCE_LENGTH
        )
        try:
            inputs = [
                np.array([encoded_behaviors], dtype=np.int32),
                np.array([encoded_items], dtype=np.int32),
                np.array([encoded_categories], dtype=np.int32),
                np.array([[target_encoded]], dtype=np.int32),
            ]
            return float(self.model.predict(inputs, verbose=0)[0][0])
        except Exception as exc:
            print(f"Model prediction error for product {target_id}: {exc}")
            return None

    def _encode(self, encoder_name: str, raw_value: Any, offset: int = 0) -> Optional[int]:
        if raw_value is None:
            return None
        encoder = self.encoders.get(encoder_name)
        if encoder is None:
            return None
        try:
            return int(encoder.transform([raw_value])[0]) + offset
        except Exception:
            try:
                return int(encoder.transform([str(raw_value)])[0]) + offset
            except Exception:
                return None


product_client = ProductClient()
graph_client = GraphClient()
vector_search_client = VectorSearchClient()
purchase_model = PurchaseModel()


@app.on_event("shutdown")
def shutdown_event() -> None:
    graph_client.close()


@app.get("/api/recommendations/search")
async def search_products(query: str, limit: int = 12) -> Dict[str, Any]:
    limit = _clamp(limit, 1, 30)
    vector_results = vector_search_client.search(query, limit)
    if vector_results:
        product_map = product_client.get_product_map([result["id"] for result in vector_results if result.get("id")])
        recommendations = []
        for result in vector_results:
            product_id = result.get("id")
            payload = product_map.get(product_id) or result.get("payload") or {}
            recommendations.append({**result, "payload": normalize_product_payload(payload)})
        return {
            "success": True,
            "query": query,
            "strategy": "qdrant_search",
            "recommendations": recommendations[:limit],
        }

    products = product_client.list_products(limit=limit, search=query)
    return _product_response(
        products,
        note=vector_search_client.load_error or "Fallback to Product Service keyword search",
        strategy="keyword_search_fallback",
    )


@app.get("/api/recommendations/{user_id}")
async def get_user_recommendations(
    user_id: int,
    limit: int = DEFAULT_LIMIT,
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    limit = _clamp(limit, 1, 10)
    try:
        history = _build_user_history(user_id, authorization)
        excluded_ids = {signal.product_id for signal in history if signal.source in {"cart", "purchase"}}

        if not history:
            popular = await _popular_recommendations(limit)
            popular["strategy"] = "popular_for_new_user"
            return popular

        seed_ids = _unique_preserve_order([signal.product_id for signal in history])
        candidates = graph_client.fetch_candidates(user_id, seed_ids, excluded_ids, CANDIDATE_LIMIT)
        if len(candidates) < CANDIDATE_LIMIT:
            used_ids = {int(c["id"]) for c in candidates if _to_int(c.get("id"))}
            candidates.extend(graph_client.popular_products(CANDIDATE_LIMIT - len(candidates), excluded_ids | used_ids))

        candidate_ids = _unique_preserve_order([_to_int(c.get("id")) for c in candidates if _to_int(c.get("id"))])
        if not candidate_ids:
            return await _popular_recommendations(limit)

        product_map = product_client.get_product_map(set(candidate_ids) | {signal.product_id for signal in history})
        qdrant_first = _qdrant_context_recommendations(
            history=history,
            product_map=product_map,
            excluded_ids=excluded_ids,
            limit=min(QDRANT_CONTEXT_LIMIT, limit),
        )
        qdrant_ids = {int(item["id"]) for item in qdrant_first if _to_int(item.get("id"))}

        scored = []
        max_graph_score = max([float(c.get("graph_score") or 0) for c in candidates] or [1.0]) or 1.0
        score_candidates = sorted(
            candidates,
            key=lambda item: float(item.get("graph_score") or 0),
            reverse=True,
        )[: max(MODEL_SCORE_LIMIT, limit)]
        for candidate in score_candidates:
            product_id = _to_int(candidate.get("id"))
            if not product_id or product_id in excluded_ids or product_id in qdrant_ids or product_id not in product_map:
                continue
            model_score = purchase_model.predict(history, product_map, product_id)
            graph_score = float(candidate.get("graph_score") or 0) / max_graph_score
            final_score = model_score if model_score is not None else graph_score
            scored.append(
                {
                    "id": product_id,
                    "score": round(float(final_score), 6),
                    "model_score": round(float(model_score), 6) if model_score is not None else None,
                    "graph_score": round(graph_score, 6),
                    "source": candidate.get("source", "graph"),
                    "reason": _source_reason(candidate.get("source", "graph")),
                    "payload": normalize_product_payload(product_map[product_id]),
                }
            )

        scored.sort(key=lambda item: (item["score"], item["graph_score"]), reverse=True)
        recommendations = (qdrant_first + scored)[:limit]
        if not recommendations:
            return await _popular_recommendations(limit)

        return {
            "success": True,
            "user_id": user_id,
            "strategy": "qdrant_context_then_cart_purchase_graph_gru",
            "model_ready": purchase_model.ready,
            "model_error": purchase_model.load_error if not purchase_model.ready else None,
            "history_count": len(history),
            "context_product_ids": seed_ids[:SEQUENCE_LENGTH],
            "qdrant_context_count": len(qdrant_first),
            "candidate_count": len(candidates),
            "model_scored_count": len(score_candidates),
            "recommendations": recommendations,
        }
    except Exception as exc:
        print(f"Recommendation pipeline error: {exc}")
        fallback = await _popular_recommendations(limit)
        fallback["note"] = f"Fallback after recommendation error: {exc}"
        return fallback


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "success": True,
        "model_ready": purchase_model.ready,
        "model_error": purchase_model.load_error or None,
        "qdrant_ready": vector_search_client.ready,
        "qdrant_error": vector_search_client.load_error or None,
    }


def _build_user_history(user_id: int, authorization: Optional[str]) -> List[ProductSignal]:
    cart_signals = _fetch_current_cart_signals(authorization)
    purchase_signals = _fetch_recent_purchase_signals(authorization)
    tracking = _fetch_tracking_history(user_id)

    # Merge all signals
    all_signals = cart_signals + purchase_signals + tracking.get("cart", []) + tracking.get("purchase", []) + tracking.get("view", [])

    # Deduplicate based on (product_id, behavior, timestamp)
    seen = set()
    unique_signals = []
    for sig in all_signals:
        key = (sig.product_id, sig.behavior, sig.timestamp)
        if key not in seen:
            seen.add(key)
            unique_signals.append(sig)

    # Sort chronologically ascending (oldest first, newest last)
    unique_signals.sort(key=lambda s: s.timestamp or "")

    # Take the last 20 behaviors (most recent)
    return unique_signals[-SEQUENCE_LENGTH:]


def _qdrant_context_recommendations(
    history: Sequence[ProductSignal],
    product_map: Dict[int, Dict[str, Any]],
    excluded_ids: Set[int],
    limit: int,
) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []

    context_text = _build_qdrant_context_text(history, product_map)
    if not context_text:
        return []

    try:
        response = requests.get(
            f"{RECOMMENDATION_SEARCH_SERVICE_URL}/api/recommendations/search",
            params={"query": context_text[:1500], "limit": max(limit * 3, 10)},
            timeout=QDRANT_CONTEXT_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"Qdrant context recommendation error: {exc}")
        return []

    recommendations: List[Dict[str, Any]] = []
    seen: Set[int] = set()
    for item in data.get("recommendations") or []:
        product_id = _to_int(item.get("id"))
        if not product_id or product_id in excluded_ids or product_id in seen:
            continue
        payload = normalize_product_payload(item.get("payload") or {})
        if not payload:
            continue
        seen.add(product_id)
        raw_score = item.get("score")
        score = float(raw_score) if raw_score is not None else 0.0
        recommendations.append(
            {
                "id": product_id,
                "score": round(score, 6),
                "model_score": None,
                "graph_score": None,
                "source": "qdrant_context",
                "reason": "Semantic match from current cart and purchase context",
                "payload": payload,
            }
        )
        if len(recommendations) >= limit:
            break

    return recommendations


def _build_qdrant_context_text(history: Sequence[ProductSignal], product_map: Dict[int, Dict[str, Any]]) -> str:
    lines: List[str] = []
    for signal in history[-SEQUENCE_LENGTH:]:
        product = product_map.get(signal.product_id, {})
        text = _payload_to_text(product) or f"Product ID {signal.product_id}"
        label = {
            "pv": "Viewed",
            "cart": "Added to cart",
            "buy": "Purchased",
        }.get(signal.behavior, "Interacted")
        lines.extend([f"{label}: {text}"] * ACTION_WEIGHTS.get(signal.behavior, 1))
    return " ".join(lines).strip()


def _payload_to_text(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""
    raw_text = payload.get("raw_text")
    if raw_text:
        return str(raw_text)
    parts = [
        f"Product Name: {payload.get('name', '')}",
        f"Category: {payload.get('category', '')}",
        f"Type: {payload.get('product_type', '')}",
        f"Description: {payload.get('description', '')}",
    ]
    return ". ".join([part for part in parts if part and not part.endswith(": ")]) + "."


def _fetch_current_cart_signals(authorization: Optional[str]) -> List[ProductSignal]:
    if not authorization:
        return []
    data = _get_json(CART_SERVICE_URL, headers={"Authorization": authorization})
    items = (data.get("data") or {}).get("items") or []
    items = sorted(items, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return [
        ProductSignal(int(item["product_id"]), "cart", item.get("updated_at") or item.get("created_at") or "", "cart")
        for item in items
        if _to_int(item.get("product_id"))
    ]


def _fetch_recent_purchase_signals(authorization: Optional[str]) -> List[ProductSignal]:
    if not authorization:
        return []
    data = _get_json(f"{ORDER_SERVICE_URL}mine/", headers={"Authorization": authorization})
    orders = data.get("data") or []
    signals: List[ProductSignal] = []
    for order in sorted(orders, key=lambda item: item.get("created_at") or "", reverse=True):
        for item in order.get("items") or []:
            pid = _to_int(item.get("product_id"))
            if pid:
                signals.append(ProductSignal(pid, "buy", order.get("created_at") or "", "purchase"))
    return signals


def _fetch_tracking_history(user_id: int) -> Dict[str, List[ProductSignal]]:
    data = _get_json(f"{TRACKING_SERVICE_URL}user-history/{user_id}/")
    history = data.get("data") or {}
    return {
        "cart": [_signal_from_tracking(item, "cart", "cart") for item in history.get("carts", []) if _to_int(item.get("product_id"))],
        "purchase": [_signal_from_tracking(item, "buy", "purchase") for item in history.get("purchases", []) if _to_int(item.get("product_id"))],
        "view": [_signal_from_tracking(item, "pv", "view") for item in history.get("views", []) if _to_int(item.get("product_id"))],
    }


def _signal_from_tracking(item: Dict[str, Any], behavior: str, source: str) -> ProductSignal:
    return ProductSignal(int(item["product_id"]), behavior, item.get("timestamp") or "", source)


def _get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"GET {url} failed: {exc}")
        return {}


async def _popular_recommendations(limit: int) -> Dict[str, Any]:
    rows = graph_client.popular_products(limit)
    ids = [_to_int(row.get("id")) for row in rows if _to_int(row.get("id"))]
    product_map = product_client.get_product_map(ids)
    recommendations = []
    max_score = max([float(row.get("graph_score") or 0) for row in rows] or [1.0]) or 1.0
    for row in rows:
        pid = _to_int(row.get("id"))
        if pid and pid in product_map:
            graph_score = float(row.get("graph_score") or 0) / max_score
            recommendations.append(
                {
                    "id": pid,
                    "score": round(graph_score, 6),
                    "model_score": None,
                    "graph_score": round(graph_score, 6),
                    "source": row.get("source", "popular"),
                    "reason": "Popular with other customers",
                    "payload": normalize_product_payload(product_map[pid]),
                }
            )
    if recommendations:
        return {"success": True, "strategy": "popular", "recommendations": recommendations[:limit]}

    products = product_client.list_products(limit=limit)
    return _product_response(products, note="Fallback to Product Service", strategy="product_service_fallback")


def _product_response(products: List[Dict[str, Any]], note: str, strategy: str) -> Dict[str, Any]:
    return {
        "success": bool(products),
        "note": note,
        "strategy": strategy,
        "recommendations": [
            {"id": product.get("id"), "score": None, "payload": product, "source": strategy, "reason": note}
            for product in products
        ],
    }


def normalize_product_payload(product: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(product, dict):
        return {}
    normalized = dict(product)
    product_type = str(normalized.get("product_type") or "").strip().lower()
    if not product_type or product_type == "generic":
        normalized["product_type"] = infer_product_type(normalized)
    return normalized


def infer_product_type(product: Dict[str, Any]) -> str:
    text = " ".join(
        str(product.get(key) or "")
        for key in ["category", "name", "description", "product_type"]
    ).lower()
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


def _source_reason(source: str) -> str:
    return {
        "other_users_bought": "Customers with similar carts bought this",
        "other_users_added_to_cart": "Customers with similar carts also added this",
        "other_users_viewed": "Customers with similar carts viewed this",
        "popular": "Popular with other customers",
    }.get(source, "Recommended from shopping behavior")


def _left_pad(behaviors: List[int], items: List[int], categories: List[int], length: int) -> tuple[List[int], List[int], List[int]]:
    behaviors = behaviors[-length:]
    items = items[-length:]
    categories = categories[-length:]
    pad_len = length - len(behaviors)
    return [0] * pad_len + behaviors, [0] * pad_len + items, [0] * pad_len + categories


def _unique_preserve_order(values: Iterable[Optional[int]]) -> List[int]:
    seen: Set[int] = set()
    result: List[int] = []
    for value in values:
        pid = _to_int(value)
        if pid and pid not in seen:
            seen.add(pid)
            result.append(pid)
    return result


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
