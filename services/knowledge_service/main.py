from fastapi import FastAPI, HTTPException
from neo4j import GraphDatabase
import os

app = FastAPI(title="Knowledge Base Service")

class GraphDB:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        auth = (user, password) if user and password and user != "none" else None
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

db = GraphDB()

@app.get("/recommendations/{user_id}")
def get_graph_recommendations(user_id: int):
    """Recommend products based on 'People also bought' logic in the Graph."""
    query = """
    MATCH (u:User {id: $uid})-[:BOUGHT]->(p:Product)<-[:BOUGHT]-(other:User)-[:BOUGHT]->(reco:Product)
    WHERE NOT (u)-[:BOUGHT]->(reco) AND reco <> p
    RETURN reco.id as id, count(*) as weight
    ORDER BY weight DESC LIMIT 5
    """
    with db.driver.session() as session:
        result = session.run(query, uid=user_id)
        recommendations = [{"product_id": record["id"], "weight": record["weight"]} for record in result]
    
    return {"user_id": user_id, "recommendations": recommendations}

@app.get("/path/{user_id}/{product_id}")
def get_path(user_id: int, product_id: int):
    """Show how a user is connected to a product."""
    query = """
    MATCH path = shortestPath((u:User {id: $uid})-[*..3]-(p:Product {id: $pid}))
    RETURN path
    """
    with db.driver.session() as session:
        result = session.run(query, uid=user_id, pid=product_id)
        # Simplified return
        return {"status": "success", "message": "Path found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
