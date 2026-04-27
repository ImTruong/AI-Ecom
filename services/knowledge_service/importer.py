import os
import json
import time
import pandas as pd
import psycopg2
from urllib.parse import urlparse
from neo4j import GraphDatabase

class KnowledgeImporter:
    def __init__(self, uri, user, password):
        auth = (user, password) if user and password and user != "none" else None
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            print("Cleaning up old data...")
            session.run("MATCH (n) DETACH DELETE n")

    def create_constraints(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT voucher_id IF NOT EXISTS FOR (v:Voucher) REQUIRE v.id IS UNIQUE")

    def import_data(self, csv_path, batch_size=500):
        if not os.path.exists(csv_path):
            return
        df = pd.read_csv(csv_path).fillna('')
        print(f"Importing {len(df)} interactions...")

        product_rows = {
            "VIEWED": [],
            "SEARCHED": [],
            "ADDED_TO_CART": [],
        }
        search_rows = []

        for _, row in df.iterrows():
            user_id = int(row['user_id'])
            action = str(row['action']).strip().upper()
            pid = int(row['product_id']) if str(row['product_id']).strip() else 0
            ts = row['timestamp']
            query = str(row.get('query', '')).strip()

            if action == 'SEARCH' and query and pid <= 0:
                search_rows.append({'user_id': user_id, 'query': query, 'ts': ts})
                continue

            if pid <= 0:
                continue

            rel_type = "VIEWED"
            if action == 'SEARCH':
                rel_type = "SEARCHED"
            elif 'CART' in action:
                rel_type = "ADDED_TO_CART"

            product_rows[rel_type].append({
                'user_id': user_id,
                'product_id': pid,
                'ts': ts
            })

        with self.driver.session() as session:
            for rel_type, rows in product_rows.items():
                for i in range(0, len(rows), batch_size):
                    chunk = rows[i:i + batch_size]
                    session.run(f"""
                        UNWIND $rows AS row
                        MERGE (u:User {{id: row.user_id}})
                        MERGE (p:Product {{id: row.product_id}})
                        MERGE (u)-[r:{rel_type}]->(p)
                        SET r.timestamp = row.ts
                    """, rows=chunk)

            for i in range(0, len(search_rows), batch_size):
                chunk = search_rows[i:i + batch_size]
                session.run("""
                    UNWIND $rows AS row
                    MERGE (u:User {id: row.user_id})
                    MERGE (s:Search {query: row.query})
                    MERGE (u)-[r:SEARCHED]->(s)
                    SET r.timestamp = row.ts
                """, rows=chunk)

    def _connect_postgres(self, db_url):
        if not db_url:
            return None
        parsed = urlparse(db_url)
        return psycopg2.connect(
            dbname=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432
        )

    def _fetch_categories(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description, icon FROM categories")
            return cur.fetchall()

    def _fetch_products(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, description, price, image_url, product_type, attributes, category_id, is_active
                FROM products
                WHERE is_active = TRUE
            """)
            return cur.fetchall()

    def _fetch_vouchers(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, code, name, description, discount_type, discount_value, min_order_value,
                       max_discount, end_date, is_global, is_active
                FROM vouchers
                WHERE is_active = TRUE
            """)
            return cur.fetchall()

    def _fetch_tracking_views(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT customer_id, product_id, timestamp FROM product_views")
            return cur.fetchall()

    def _fetch_tracking_carts(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT customer_id, product_id, action_type, timestamp FROM cart_actions")
            return cur.fetchall()

    def _fetch_tracking_purchases(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT customer_id, product_id, timestamp FROM purchase_actions")
            return cur.fetchall()

    def _fetch_tracking_searches(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT customer_id, query, timestamp FROM search_history")
            return cur.fetchall()

    def import_products_from_db(self, db_url):
        if not db_url:
            print("No PRODUCT_DATABASE_URL provided, skipping product import.")
            return
        conn = self._connect_postgres(db_url)
        if not conn:
            print("Failed to connect to product database.")
            return
        try:
            categories = self._fetch_categories(conn)
            products = self._fetch_products(conn)
        finally:
            conn.close()

        with self.driver.session() as session:
            print(f"Importing {len(categories)} categories and {len(products)} products...")
            for cid, name, desc, icon in categories:
                session.run("""
                    MERGE (c:Category {id: $id})
                    SET c.name = $name,
                        c.description = $desc,
                        c.icon = $icon
                """, id=cid, name=name, desc=desc or "", icon=icon or "box")

            for pid, name, desc, price, image_url, ptype, attrs, category_id, is_active in products:
                attributes = attrs if isinstance(attrs, dict) else {}
                attrs_json = json.dumps(attributes, ensure_ascii=False)
                session.run("""
                    MERGE (p:Product {id: $id})
                    SET p.name = $name,
                        p.description = $desc,
                        p.price = $price,
                        p.image_url = $image_url,
                        p.product_type = $ptype,
                        p.attributes = $attrs,
                        p.is_active = $is_active
                    WITH p
                    MATCH (c:Category {id: $category_id})
                    MERGE (p)-[:BELONGS_TO]->(c)
                """, id=pid, name=name, desc=desc or "", price=float(price) if price is not None else 0,
                     image_url=image_url or "", ptype=ptype or "generic", attrs=attrs_json,
                     is_active=bool(is_active), category_id=category_id)

    def import_vouchers_from_db(self, db_url):
        if not db_url:
            print("No VOUCHER_DATABASE_URL provided, skipping voucher import.")
            return
        conn = self._connect_postgres(db_url)
        if not conn:
            print("Failed to connect to voucher database.")
            return
        try:
            vouchers = self._fetch_vouchers(conn)
        finally:
            conn.close()

        with self.driver.session() as session:
            print(f"Importing {len(vouchers)} vouchers...")
            for row in vouchers:
                (vid, code, name, desc, dtype, dvalue, min_value,
                 max_discount, end_date, is_global, is_active) = row
                session.run("""
                    MERGE (v:Voucher {id: $id})
                    SET v.code = $code,
                        v.name = $name,
                        v.description = $desc,
                        v.discount_type = $dtype,
                        v.discount_value = $dvalue,
                        v.min_order_value = $min_value,
                        v.max_discount = $max_discount,
                        v.end_date = $end_date,
                        v.is_global = $is_global,
                        v.is_active = $is_active
                """, id=vid, code=code, name=name, desc=desc or "", dtype=dtype,
                     dvalue=float(dvalue) if dvalue is not None else 0,
                     min_value=float(min_value) if min_value is not None else 0,
                     max_discount=float(max_discount) if max_discount is not None else None,
                     end_date=str(end_date), is_global=bool(is_global), is_active=bool(is_active))

    def import_tracking_from_db(self, db_url):
        if not db_url:
            print("No TRACKING_DATABASE_URL provided, skipping tracking import.")
            return
        conn = self._connect_postgres(db_url)
        if not conn:
            print("Failed to connect to tracking database.")
            return
        try:
            views = self._fetch_tracking_views(conn)
            carts = self._fetch_tracking_carts(conn)
            purchases = self._fetch_tracking_purchases(conn)
            searches = self._fetch_tracking_searches(conn)
        finally:
            conn.close()

        with self.driver.session() as session:
            print(f"Importing tracking: {len(views)} views, {len(carts)} cart actions, {len(purchases)} purchases, {len(searches)} searches...")
            for customer_id, product_id, ts in views:
                if not customer_id or not product_id:
                    continue
                session.run("""
                    MERGE (u:User {id: $uid})
                    WITH u
                    MATCH (p:Product {id: $pid})
                    MERGE (u)-[r:VIEWED {timestamp: $ts}]->(p)
                """, uid=customer_id, pid=product_id, ts=ts)

            for customer_id, product_id, action_type, ts in carts:
                if not customer_id or not product_id:
                    continue
                rel = "ADDED_TO_CART" if action_type == "add" else "CART_ACTION"
                session.run(f"""
                    MERGE (u:User {{id: $uid}})
                    WITH u
                    MATCH (p:Product {{id: $pid}})
                    MERGE (u)-[r:{rel} {{timestamp: $ts}}]->(p)
                """, uid=customer_id, pid=product_id, ts=ts)

            for customer_id, product_id, ts in purchases:
                if not customer_id or not product_id:
                    continue
                session.run("""
                    MERGE (u:User {id: $uid})
                    WITH u
                    MATCH (p:Product {id: $pid})
                    MERGE (u)-[r:BOUGHT {timestamp: $ts}]->(p)
                """, uid=customer_id, pid=product_id, ts=ts)

            for customer_id, search_query, ts in searches:
                if not customer_id or not search_query:
                    continue
                session.run("""
                    MERGE (u:User {id: $uid})
                    MERGE (s:Search {query: $search_query})
                    MERGE (u)-[r:SEARCHED {timestamp: $ts}]->(s)
                """, uid=customer_id, search_query=search_query, ts=ts)

if __name__ == "__main__":
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    importer = KnowledgeImporter(uri, "neo4j", "password123")
    importer.clear_database()
    importer.create_constraints()
    importer.import_data("/data_user500.csv")
    importer.import_products_from_db(os.getenv("PRODUCT_DATABASE_URL"))
    importer.import_vouchers_from_db(os.getenv("VOUCHER_DATABASE_URL"))
    importer.import_tracking_from_db(os.getenv("TRACKING_DATABASE_URL"))
    importer.close()
    print("Graph Data Refresh Complete (Dynamic Mode)!")
