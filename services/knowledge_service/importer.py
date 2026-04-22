import pandas as pd
from neo4j import GraphDatabase
import os
import time

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
            session.run("CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")

    def import_data(self, csv_path):
        if not os.path.exists(csv_path): return
        df = pd.read_csv(csv_path)
        with self.driver.session() as session:
            print(f"Importing {len(df)} interactions...")
            for _, row in df.iterrows():
                user_id = int(row['user_id'])
                action = str(row['action']).upper()
                pid = int(row['product_id'])
                ts = row['timestamp']
                session.run("MERGE (u:User {id: $id})", id=user_id)
                if pid > 0:
                    rel_type = "VIEWED"
                    if action == 'SEARCH': rel_type = "SEARCHED"
                    elif 'CART' in action: rel_type = "ADDED_TO_CART"
                    
                    session.run(f"""
                        MERGE (p:Product {{id: $pid}})
                        WITH p, $uid as uid
                        MATCH (u:User {{id: uid}})
                        MERGE (u)-[r:{rel_type} {{timestamp: $ts}}]->(p)
                    """, uid=user_id, pid=pid, ts=ts)

    def seed_rich_data(self):
        # We don't hardcode products anymore, just categories
        with self.driver.session() as session:
            print("Seeding Category metadata...")
            categories = ["Programming", "T-Shirt", "Self-Help", "Hoodie", "Accessories"]
            for cat in categories:
                session.run("MERGE (c:Category {name: $name})", name=cat)

if __name__ == "__main__":
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    importer = KnowledgeImporter(uri, "neo4j", "password123")
    importer.clear_database()
    importer.create_constraints()
    importer.import_data("/data_user500.csv")
    importer.seed_rich_data()
    importer.close()
    print("Graph Data Refresh Complete (Dynamic Mode)!")
