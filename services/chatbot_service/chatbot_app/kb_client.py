from neo4j import GraphDatabase
import os

class KBClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            print(f"[NEO4J] Connected to {uri}")
        except Exception as e:
            print(f"[NEO4J] Connection Failure: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def get_user_history(self, user_id):
        if not self.driver: return []
        with self.driver.session() as session:
            # Flexible relationship type matching and property access
            query = """
            MATCH (u:User {id: $user_id})-[r]->(p:Product)
            WHERE type(r) CONTAINS 'VIEW' OR type(r) CONTAINS 'CART' OR type(r) CONTAINS 'SEARCH'
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
            RETURN p.id as product_id, p.name as name, type(r) as action, 
                   COALESCE(c.name, 'Chưa phân loại') as category, c.id as category_id
            ORDER BY r.timestamp DESC LIMIT 10
            """
            result = session.run(query, user_id=user_id)
            return [dict(record) for record in result]

    def get_product_details(self, product_ids):
        if not self.driver: return []
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)
            WHERE p.id IN $product_ids
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
            RETURN p.id as id, p.name as name, COALESCE(c.name, 'Chưa phân loại') as category, 
                   p.price as price, p.description as description, COALESCE(p.rating, 5.0) as rating,
                   COALESCE(p.product_type, 'generic') as product_type, COALESCE(p.image_url, '') as image_url
            """
            result = session.run(query, product_ids=product_ids)
            return [dict(record) for record in result]

    def get_top_rated_products(self, limit=5):
        if not self.driver: return []
        with self.driver.session() as session:
            # Fallback for rating if it doesn't exist yet
            query = """
            MATCH (p:Product)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
            RETURN p.id as id, p.name as name, COALESCE(c.name, 'Chưa phân loại') as category, 
                   p.price as price, COALESCE(p.rating, 0.0) as rating,
                   COALESCE(p.product_type, 'generic') as product_type, COALESCE(p.image_url, '') as image_url
            ORDER BY rating DESC LIMIT $limit
            """
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]

    def get_active_vouchers(self, limit=5):
        if not self.driver: return []
        with self.driver.session() as session:
            query = """
            MATCH (v:Voucher)
            WHERE v.is_active = true
            RETURN v.id as id, v.code as code, v.name as name, v.description as description,
                   v.discount_type as discount_type, v.discount_value as discount_value
            ORDER BY v.discount_value DESC LIMIT $limit
            """
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]

    def search_products(self, keyword, limit=5):
        if not self.driver: return []
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)
            WHERE p.name CONTAINS $keyword OR EXISTS {
                MATCH (p)-[:BELONGS_TO]->(c:Category)
                WHERE c.name CONTAINS $keyword
            }
            RETURN p.id as id, p.name as name, p.price as price
            LIMIT $limit
            """
            result = session.run(query, keyword=keyword, limit=limit)
            return [dict(record) for record in result]

    def record_user_action(self, user_id, action, product_id=None):
        if not self.driver: return
        with self.driver.session() as session:
            # Sync with the relationship names in importer.py (VIEWED, SEARCHED, ADDED_TO_CART)
            rel_type = action.upper()
            if rel_type == 'VIEW': rel_type = 'VIEWED'
            elif rel_type == 'SEARCH': rel_type = 'SEARCHED'
            elif rel_type == 'CART': rel_type = 'ADDED_TO_CART'

            query = """
            MERGE (u:User {id: $user_id})
            WITH u
            MATCH (p:Product {id: $product_id})
            MERGE (u)-[r:""" + rel_type + """ {timestamp: timestamp()}]->(p)
            """
            session.run(query, user_id=user_id, product_id=product_id)

# Singleton
_kb_instance = None
def get_kb_client():
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KBClient()
    return _kb_instance
