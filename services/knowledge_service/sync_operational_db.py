import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# DB configurations
DB_URLS = {
    "auth": os.getenv("USER_DATABASE_URL", "postgresql://auth_user:auth_pass@auth_db:5432/auth_db"),
    "product": os.getenv("PRODUCT_DATABASE_URL", "postgresql://product_user:product_pass@product_db:5432/product_db"),
    "tracking": os.getenv("TRACKING_DATABASE_URL", "postgresql://tracking_user:tracking_pass@tracking_db:5432/tracking_db"),
    "cart": os.getenv("CART_DATABASE_URL", "postgresql://cart_user:cart_pass@cart_db:5432/cart_db"),
    "order": os.getenv("ORDER_DATABASE_URL", "postgresql://order_user:order_pass@order_db:5432/order_db")
}

def get_connection(key):
    return psycopg2.connect(DB_URLS[key])

def run_sync():
    print("=========================================")
    print("🔄 STARTING OPERATIONAL DB SYNC...")
    print("=========================================")

    # 1. Fetch products and variants details from product_db
    print("Fetching product catalog...")
    conn_p = get_connection("product")
    products = {}
    variants = {}
    try:
        with conn_p.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name, price, image_url, product_type FROM products")
            for row in cur.fetchall():
                products[row["id"]] = row
                
            cur.execute("SELECT id, product_id, name, price_override, sku, image_url FROM product_variants")
            for row in cur.fetchall():
                pid = row["product_id"]
                if pid not in variants:
                    variants[pid] = []
                variants[pid].append(row)
    finally:
        conn_p.close()

    print(f"Loaded {len(products)} products and variants for {len(variants)} products.")

    # Helper function to get product and variant info
    def get_product_variant_info(product_id):
        prod = products.get(product_id)
        if not prod:
            return None
        
        # Get first variant if exists
        p_variants = variants.get(product_id, [])
        if p_variants:
            v = p_variants[0]
            price = v["price_override"] if v["price_override"] is not None else prod["price"]
            return {
                "product_id": product_id,
                "product_name": prod["name"],
                "image_url": v["image_url"] or prod["image_url"] or "",
                "variant_id": v["id"],
                "variant_name": v["name"],
                "price": price
            }
        else:
            return {
                "product_id": product_id,
                "product_name": prod["name"],
                "image_url": prod["image_url"] or "",
                "variant_id": None,
                "variant_name": "",
                "price": prod["price"]
            }

    # 2. Fetch customers and addresses from auth_db
    print("Fetching customers and addresses...")
    conn_a = get_connection("auth")
    addresses = {}
    users = {}
    try:
        with conn_a.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT id, full_name, phone, address FROM "user"')
            for row in cur.fetchall():
                users[row["id"]] = row
                
            cur.execute("SELECT id, customer_id, full_name, phone, street_address, city, state, postal_code, country, is_default FROM address")
            for row in cur.fetchall():
                cid = row["customer_id"]
                if cid not in addresses:
                    addresses[cid] = []
                addresses[cid].append(row)
    finally:
        conn_a.close()

    # Helper to get shipping info
    def get_shipping_info(customer_id):
        # 1. Search default address
        c_addrs = addresses.get(customer_id, [])
        addr = None
        for a in c_addrs:
            if a["is_default"]:
                addr = a
                break
        if not addr and c_addrs:
            addr = c_addrs[0]
            
        if addr:
            addr_line = f"{addr['street_address']}, {addr['city']}, {addr['state']}, {addr['postal_code']}, {addr['country']}"
            return {
                "address_id": addr["id"],
                "full_name": addr["full_name"],
                "phone": addr["phone"],
                "address_line": addr_line
            }
            
        # 2. Search user table fallback
        user = users.get(customer_id)
        if user:
            return {
                "address_id": 0,
                "full_name": user["full_name"] or f"Customer {customer_id}",
                "phone": user["phone"] or "0000000000",
                "address_line": user["address"] or "No Address Provided"
            }
            
        return {
            "address_id": 0,
            "full_name": f"Customer {customer_id}",
            "phone": "0000000000",
            "address_line": "No Address Provided"
        }

    # 3. Fetch tracking events to simulate cart state
    print("Simulating cart states and purchase orders chronologically...")
    conn_t = get_connection("tracking")
    cart_actions = []
    purchase_actions = []
    try:
        with conn_t.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT customer_id, product_id, product_type, action_type, timestamp FROM cart_actions ORDER BY timestamp")
            cart_actions = cur.fetchall()
            
            cur.execute("SELECT customer_id, product_id, product_type, order_id, price, quantity, timestamp FROM purchase_actions ORDER BY timestamp")
            purchase_actions = cur.fetchall()
    finally:
        conn_t.close()

    # Group purchase actions by order_id
    orders_dict = {}
    for pa in purchase_actions:
        oid = pa["order_id"]
        if oid not in orders_dict:
            orders_dict[oid] = {
                "customer_id": pa["customer_id"],
                "timestamp": pa["timestamp"],
                "items": []
            }
        orders_dict[oid]["items"].append(pa)

    # Chronologically simulate cart items
    # Whenever a customer purchases items, those items are checked out and removed from the active cart.
    customer_carts = {} # customer_id -> {(product_type, product_id): quantity}
    
    # Process actions chronologically
    all_actions = []
    for ca in cart_actions:
        all_actions.append(("cart", ca["timestamp"], ca))
    for oid, order_info in orders_dict.items():
        all_actions.append(("purchase", order_info["timestamp"], order_info))
        
    all_actions.sort(key=lambda x: x[1])

    for act_type, ts, data in all_actions:
        if act_type == "cart":
            cid = data["customer_id"]
            pid = data["product_id"]
            ptype = data["product_type"]
            act = data["action_type"].strip().lower()
            
            if cid not in customer_carts:
                customer_carts[cid] = {}
                
            key = (ptype, pid)
            if act == "add":
                customer_carts[cid][key] = customer_carts[cid].get(key, 0) + 1
            elif act in ("remove", "delete"):
                if key in customer_carts[cid]:
                    del customer_carts[cid][key]
        elif act_type == "purchase":
            cid = data["customer_id"]
            if cid in customer_carts:
                # Remove purchased items from active cart
                for item in data["items"]:
                    key = (item["product_type"], item["product_id"])
                    if key in customer_carts[cid]:
                        # Decrease or remove
                        del customer_carts[cid][key]

    # Clean empty carts
    customer_carts = {cid: items for cid, items in customer_carts.items() if items}

    # 4. Truncate operational databases
    print("Clearing cart_db and order_db tables...")
    conn_c = get_connection("cart")
    try:
        with conn_c.cursor() as cur:
            cur.execute("TRUNCATE TABLE carts, cart_items CASCADE;")
        conn_c.commit()
    except Exception as e:
        conn_c.rollback()
        print(f"Error truncating cart_db: {e}")
        raise e
    finally:
        conn_c.close()

    conn_o = get_connection("order")
    try:
        with conn_o.cursor() as cur:
            cur.execute("TRUNCATE TABLE orders, order_items, ship_tracking CASCADE;")
        conn_o.commit()
    except Exception as e:
        conn_o.rollback()
        print(f"Error truncating order_db: {e}")
        raise e
    finally:
        conn_o.close()

    # 5. Populate Carts Database
    print("Populating cart_db...")
    conn_c = get_connection("cart")
    try:
        with conn_c.cursor() as cur:
            for cid, items in customer_carts.items():
                # Create cart
                cur.execute(
                    "INSERT INTO carts (customer_id, created_at, updated_at) VALUES (%s, NOW(), NOW()) RETURNING id;",
                    (cid,)
                )
                cart_id = cur.fetchone()[0]
                
                # Create cart items
                for (ptype, pid), qty in items.items():
                    info = get_product_variant_info(pid)
                    if not info:
                        continue
                    
                    cur.execute(
                        """INSERT INTO cart_items (cart_id, product_type, product_id, variant_id, product_name, variant_name, image_url, quantity, price, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW());""",
                        (cart_id, ptype, pid, info["variant_id"], info["product_name"], info["variant_name"], info["image_url"], qty, info["price"])
                    )
        conn_c.commit()
        print(f"Created {len(customer_carts)} carts successfully.")
    except Exception as e:
        conn_c.rollback()
        print(f"Error seeding cart_db: {e}")
        raise e
    finally:
        conn_c.close()

    # 6. Populate Orders Database
    print("Populating order_db...")
    conn_o = get_connection("order")
    try:
        with conn_o.cursor() as cur:
            for oid, order_info in sorted(orders_dict.items()):
                cid = order_info["customer_id"]
                ts = order_info["timestamp"]
                items = order_info["items"]
                
                # Calculate totals
                total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in items)
                final_amount = total_amount
                
                # Get shipping details
                ship = get_shipping_info(cid)
                
                # Insert order (using original order_id to keep relationship consistency!)
                cur.execute(
                    """INSERT INTO orders (id, customer_id, total_amount, discount_amount, final_amount, status, payment_method, shipping_address_id, shipping_full_name, shipping_phone, shipping_address_line, created_at, updated_at)
                       VALUES (%s, %s, %s, 0, %s, 'delivered', 'cod', %s, %s, %s, %s, %s, %s);""",
                    (oid, cid, total_amount, final_amount, ship["address_id"], ship["full_name"], ship["phone"], ship["address_line"], ts, ts)
                )
                
                # Insert order items
                for item in items:
                    pid = item["product_id"]
                    ptype = item["product_type"]
                    qty = item["quantity"]
                    price = item["price"]
                    
                    info = get_product_variant_info(pid)
                    pname = info["product_name"] if info else "Product " + str(pid)
                    vname = info["variant_name"] if info else ""
                    vid = info["variant_id"] if info else None
                    img = info["image_url"] if info else ""
                    
                    cur.execute(
                        """INSERT INTO order_items (order_id, product_type, product_id, variant_id, variant_name, image_url, product_name, price, quantity)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                        (oid, ptype, pid, vid, vname, img, pname, price, qty)
                    )
                
                # Insert shipment tracking
                cur.execute(
                    """INSERT INTO ship_tracking (order_id, status, location, note, carrier, tracking_code, event_time, created_by_user_id, created_by_user_type, created_at)
                       VALUES (%s, 'delivered', %s, 'Delivered successfully based on purchase log', 'ExpressCarrier', %s, %s, 1, 'staff', %s);""",
                    (oid, ship["address_line"], f"TRK{oid}99", ts, ts)
                )
        conn_o.commit()
        print(f"Created {len(orders_dict)} orders successfully.")
    except Exception as e:
        conn_o.rollback()
        print(f"Error seeding order_db: {e}")
        raise e
    finally:
        conn_o.close()

    # 7. Reset Operational Database Sequences
    print("Resetting sequences in cart_db and order_db...")
    for key, tables in [("cart", ["carts", "cart_items"]), ("order", ["orders", "order_items", "ship_tracking"])]:
        conn = get_connection(key)
        try:
            with conn.cursor() as cur:
                for table in tables:
                    cur.execute("SELECT pg_get_serial_sequence(%s, 'id');", (table,))
                    seq_res = cur.fetchone()
                    if seq_res and seq_res[0]:
                        seq_name = seq_res[0]
                        print(f"Resetting sequence {seq_name} for table {table} in {key}_db...")
                        cur.execute(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table}), 1), true);")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error resetting sequences for {key}_db: {e}")
        finally:
            conn.close()

    print("\n=========================================")
    print("🎉 OPERATIONAL DB SYNC COMPLETE!")
    print("=========================================")

if __name__ == "__main__":
    run_sync()
