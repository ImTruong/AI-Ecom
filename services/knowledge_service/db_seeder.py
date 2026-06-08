import os
import csv
import json
import re
import psycopg2
from psycopg2.extras import RealDictCursor

# Global de-duplication maps
category_map = {}
product_map = {}
variant_map = {}

# Directories inside container
DATA_DIR = "/AI/data"

DB_CONFIGS = {
    "auth": {
        "url": os.getenv("USER_DATABASE_URL", "postgresql://auth_user:auth_pass@auth_db:5432/auth_db"),
        "tables": ["address", "user"]
    },
    "product": {
        "url": os.getenv("PRODUCT_DATABASE_URL", "postgresql://product_user:product_pass@product_db:5432/product_db"),
        "tables": ["product_variant_options", "product_variants", "attribute_values", "attributes", "products", "categories"]
    },
    "tracking": {
        "url": os.getenv("TRACKING_DATABASE_URL", "postgresql://tracking_user:tracking_pass@tracking_db:5432/tracking_db"),
        "tables": ["product_views", "cart_actions", "purchase_actions", "tracking_events"]
    }
}

def get_connection(db_key):
    config = DB_CONFIGS[db_key]
    return psycopg2.connect(config["url"])

def clean_value(val, data_type=str):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.upper() == "NULL":
        return None
    if data_type == bool:
        return s.lower() in ("true", "1", "yes", "t")
    if data_type == int:
        return int(s)
    if data_type == float:
        return float(s)
    return s

def truncate_tables():
    print("--- Truncating PostgreSQL Tables ---")
    for key, config in DB_CONFIGS.items():
        conn = get_connection(key)
        try:
            with conn.cursor() as cur:
                for table in config["tables"]:
                    # user is a reserved keyword in postgres
                    tbl_quoted = f'"{table}"' if table == "user" else table
                    print(f"Truncating table {tbl_quoted} in {key}_db...")
                    cur.execute(f"TRUNCATE TABLE {tbl_quoted} CASCADE;")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error truncating {key}_db: {e}")
            raise e
        finally:
            conn.close()

def seed_auth():
    print("\n--- Seeding Auth Database ---")
    conn = get_connection("auth")
    try:
        # 1. Customers (user table)
        user_path = os.path.join(DATA_DIR, "customer.csv")
        print(f"Reading {user_path}...")
        with open(user_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            users_data = []
            for r in reader:
                users_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["email"]),
                    clean_value(r["password_hash"]),
                    clean_value(r["full_name"]),
                    clean_value(r["phone"]),
                    clean_value(r["address"]),
                    clean_value(r["role"]),
                    clean_value(r["is_active"], bool),
                    clean_value(r["created_at"]),
                    clean_value(r["updated_at"])
                ))
        
        with conn.cursor() as cur:
            print(f"Inserting {len(users_data)} users...")
            cur.executemany(
                """INSERT INTO "user" (id, email, password_hash, full_name, phone, address, role, is_active, created_at, updated_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                users_data
            )
        
        # 2. Addresses
        address_path = os.path.join(DATA_DIR, "address.csv")
        print(f"Reading {address_path}...")
        with open(address_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            addresses_data = []
            for r in reader:
                addresses_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["customer_id"], int),
                    clean_value(r["full_name"]),
                    clean_value(r["phone"]),
                    clean_value(r["street_address"]),
                    clean_value(r["city"]),
                    clean_value(r["state"]),
                    clean_value(r["postal_code"]),
                    clean_value(r["country"]),
                    clean_value(r["address_type"]),
                    clean_value(r["is_default"], bool),
                    clean_value(r["is_active"], bool),
                    clean_value(r["created_at"]),
                    clean_value(r["updated_at"])
                ))
        
        with conn.cursor() as cur:
            print(f"Inserting {len(addresses_data)} addresses...")
            cur.executemany(
                """INSERT INTO address (id, customer_id, full_name, phone, street_address, city, state, postal_code, country, address_type, is_default, is_active, created_at, updated_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                addresses_data
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error seeding auth database: {e}")
        raise e
    finally:
        conn.close()

def clean_name(name):
    if not name:
        return ""
    # Remove "(ID XXX)" or "ID XXX" suffix
    cleaned = re.sub(r"\s*\(ID\s+\d+\)\s*", "", name)
    cleaned = re.sub(r"\s*ID\s+\d+\s*", "", cleaned)
    return cleaned.strip()

def seed_product():
    print("\n--- Seeding Product Database ---")
    conn = get_connection("product")
    try:
        # 1. Categories (De-duplicated)
        cat_path = os.path.join(DATA_DIR, "categories.csv")
        print(f"Reading and de-duplicating {cat_path}...")
        categories_data = []
        seen_categories = {}
        with open(cat_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                cid = int(r["id"])
                cname = clean_value(r["name"])
                cname_clean = clean_name(cname)
                
                if cname_clean not in seen_categories:
                    seen_categories[cname_clean] = cid
                    category_map[cid] = cid
                    
                    name_with_suffix = f"{cname_clean} (new)" if cname_clean else "Uncategorized (new)"
                    categories_data.append((
                        cid,
                        name_with_suffix,
                        clean_value(r["slug"]),
                        clean_value(r["description"]),
                        clean_value(r["icon"])
                    ))
                else:
                    category_map[cid] = seen_categories[cname_clean]
                    
        with conn.cursor() as cur:
            print(f"Inserting {len(categories_data)} unique categories...")
            cur.executemany(
                "INSERT INTO categories (id, name, slug, description, icon) VALUES (%s, %s, %s, %s, %s);",
                categories_data
            )

        # 2. Products (De-duplicated)
        prod_path = os.path.join(DATA_DIR, "products.csv")
        print(f"Reading and de-duplicating {prod_path}...")
        products_data = []
        seen_products = {}
        product_clean_names = {}
        with open(prod_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = int(r["id"])
                pname = clean_value(r["name"])
                pname_clean = clean_name(pname)
                product_clean_names[pid] = pname_clean
                
                orig_cat_id = clean_value(r["category_id"], int)
                mapped_cat_id = category_map.get(orig_cat_id, orig_cat_id)
                
                if pname_clean not in seen_products:
                    seen_products[pname_clean] = pid
                    product_map[pid] = pid
                    
                    name_with_suffix = f"{pname_clean} (new)" if pname_clean else "Product (new)"
                    products_data.append((
                        pid,
                        mapped_cat_id,
                        name_with_suffix,
                        clean_value(r["description"]),
                        clean_value(r["price"], float),
                        clean_value(r["image_url"]),
                        clean_value(r["supplier_id"], int),
                        clean_value(r["product_type"]),
                        clean_value(r["attributes"]),  # json string
                        clean_value(r["is_active"], bool),
                        clean_value(r["created_at"]),
                        clean_value(r["updated_at"])
                    ))
                else:
                    product_map[pid] = seen_products[pname_clean]
                    
        with conn.cursor() as cur:
            print(f"Inserting {len(products_data)} unique products...")
            cur.executemany(
                """INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, product_type, attributes, is_active, created_at, updated_at) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                products_data
            )

        # 3. Attributes (Keep as-is)
        attr_path = os.path.join(DATA_DIR, "attributes.csv")
        print(f"Reading {attr_path}...")
        attributes_data = []
        with open(attr_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                attributes_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["name"]),
                    clean_value(r["slug"])
                ))
        with conn.cursor() as cur:
            print(f"Inserting {len(attributes_data)} attributes...")
            cur.executemany(
                "INSERT INTO attributes (id, name, slug) VALUES (%s, %s, %s);",
                attributes_data
            )

        # 4. Attribute Values (Keep as-is)
        val_path = os.path.join(DATA_DIR, "attribute_values.csv")
        print(f"Reading {val_path}...")
        vals_data = []
        with open(val_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                vals_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["attribute_id"], int),
                    clean_value(r["value"]),
                    clean_value(r["slug"])
                ))
        with conn.cursor() as cur:
            print(f"Inserting {len(vals_data)} attribute values...")
            cur.executemany(
                "INSERT INTO attribute_values (id, attribute_id, value, slug) VALUES (%s, %s, %s, %s);",
                vals_data
            )

        # 5. Product Variants (De-duplicated)
        variant_path = os.path.join(DATA_DIR, "product_variants.csv")
        print(f"Reading and de-duplicating {variant_path}...")
        variants_data = []
        primary_variants = {}  # (clean_product_name, variant_name) -> primary_variant_id
        
        with open(variant_path, mode='r', encoding='utf-8') as f:
            raw_variants = list(csv.DictReader(f))
            
        # First pass: load and save primary variants
        for r in raw_variants:
            vid = int(r["id"])
            pid = int(r["product_id"])
            vname = r["name"].strip()
            clean_pname = product_clean_names.get(pid, "")
            primary_pid = product_map.get(pid)
            
            if pid == primary_pid:
                primary_variants[(clean_pname, vname)] = vid
                variant_map[vid] = vid
                variants_data.append((
                    vid,
                    primary_pid,
                    vname,
                    clean_value(r["price_override"], float),
                    clean_value(r["stock"], int),
                    clean_value(r["sku"]),
                    clean_value(r["image_url"]),
                    clean_value(r["is_active"], bool),
                    clean_value(r["options"])  # json string
                ))
                
        # Second pass: map duplicate variants to primary variants
        for r in raw_variants:
            vid = int(r["id"])
            pid = int(r["product_id"])
            vname = r["name"].strip()
            clean_pname = product_clean_names.get(pid, "")
            primary_pid = product_map.get(pid)
            
            if pid != primary_pid:
                primary_vid = primary_variants.get((clean_pname, vname))
                if primary_vid is None:
                    # Fallback to any variant of primary product if name doesn't match
                    fallback_vids = [pvid for (cp, vn), pvid in primary_variants.items() if cp == clean_pname]
                    primary_vid = fallback_vids[0] if fallback_vids else None
                variant_map[vid] = primary_vid
                
        with conn.cursor() as cur:
            print(f"Inserting {len(variants_data)} unique product variants...")
            cur.executemany(
                """INSERT INTO product_variants (id, product_id, name, price_override, stock, sku, image_url, is_active, options) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                variants_data
            )

        # 6. Product Variant Options (Filtered)
        option_path = os.path.join(DATA_DIR, "product_variant_options.csv")
        print(f"Reading and filtering {option_path}...")
        options_data = []
        with open(option_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                vid = int(r["variant_id"])
                if variant_map.get(vid) == vid:
                    options_data.append((
                        clean_value(r["id"], int),
                        vid,
                        clean_value(r["attribute_value_id"], int)
                    ))
        with conn.cursor() as cur:
            print(f"Inserting {len(options_data)} unique variant options...")
            cur.executemany(
                "INSERT INTO product_variant_options (id, variant_id, attribute_value_id) VALUES (%s, %s, %s);",
                options_data
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error seeding product database: {e}")
        raise e
    finally:
        conn.close()

def seed_tracking():
    print("\n--- Seeding Tracking Database ---")
    conn = get_connection("tracking")
    try:
        # 1. Product Views
        views_path = os.path.join(DATA_DIR, "product_views.csv")
        print(f"Reading and mapping {views_path}...")
        views_data = []
        with open(views_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = clean_value(r["product_id"], int)
                mapped_pid = product_map.get(pid, pid)
                views_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["customer_id"], int),
                    mapped_pid,
                    clean_value(r["product_type"]),
                    clean_value(r["session_id"]),
                    clean_value(r["timestamp"])
                ))
        with conn.cursor() as cur:
            print(f"Inserting {len(views_data)} mapped product views...")
            cur.executemany(
                "INSERT INTO product_views (id, customer_id, product_id, product_type, session_id, timestamp) VALUES (%s, %s, %s, %s, %s, %s);",
                views_data
            )

        # 2. Cart Actions
        carts_path = os.path.join(DATA_DIR, "cart_actions.csv")
        print(f"Reading and mapping {carts_path}...")
        carts_data = []
        with open(carts_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = clean_value(r["product_id"], int)
                mapped_pid = product_map.get(pid, pid)
                carts_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["customer_id"], int),
                    mapped_pid,
                    clean_value(r["product_type"]),
                    clean_value(r["action_type"]),
                    clean_value(r["quantity"], int),
                    clean_value(r["price"], float),
                    clean_value(r["timestamp"])
                ))
        with conn.cursor() as cur:
            print(f"Inserting {len(carts_data)} mapped cart actions...")
            cur.executemany(
                "INSERT INTO cart_actions (id, customer_id, product_id, product_type, action_type, quantity, price, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                carts_data
            )

        # 3. Purchase Actions
        purchases_path = os.path.join(DATA_DIR, "purchase_actions.csv")
        print(f"Reading and mapping {purchases_path}...")
        purchases_data = []
        with open(purchases_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = clean_value(r["product_id"], int)
                mapped_pid = product_map.get(pid, pid)
                purchases_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["customer_id"], int),
                    mapped_pid,
                    clean_value(r["product_type"]),
                    clean_value(r["order_id"], int),
                    clean_value(r["price"], float),
                    clean_value(r["quantity"], int),
                    clean_value(r["timestamp"])
                ))
        with conn.cursor() as cur:
            print(f"Inserting {len(purchases_data)} mapped purchase actions...")
            cur.executemany(
                "INSERT INTO purchase_actions (id, customer_id, product_id, product_type, order_id, price, quantity, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                purchases_data
            )

        # 4. Tracking Events
        events_path = os.path.join(DATA_DIR, "tracking_events.csv")
        print(f"Reading and mapping {events_path}...")
        events_data = []
        with open(events_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                pid = clean_value(r["product_id"], int)
                vid = clean_value(r["product_variant_id"], int)
                mapped_pid = product_map.get(pid, pid) if pid else None
                mapped_vid = variant_map.get(vid, vid) if vid else None
                events_data.append((
                    clean_value(r["id"], int),
                    clean_value(r["user_id"], int),
                    clean_value(r["session_id"]),
                    clean_value(r["event_type"]),
                    mapped_pid,
                    mapped_vid,
                    clean_value(r["metadata"]),  # json string
                    clean_value(r["created_at"])
                ))
        with conn.cursor() as cur:
            print(f"Inserting {len(events_data)} mapped tracking events...")
            cur.executemany(
                "INSERT INTO tracking_events (id, user_id, session_id, event_type, product_id, product_variant_id, metadata, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                events_data
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error seeding tracking database: {e}")
        raise e
    finally:
        conn.close()

def reset_sequences():
    print("\n--- Resetting PostgreSQL Sequences ---")
    for key, config in DB_CONFIGS.items():
        conn = get_connection(key)
        try:
            with conn.cursor() as cur:
                for table in config["tables"]:
                    tbl_quoted = f'"{table}"' if table == "user" else table
                    
                    # Get sequence name
                    cur.execute(
                        "SELECT pg_get_serial_sequence(%s, 'id');",
                        (table,)
                    )
                    seq_res = cur.fetchone()
                    if seq_res and seq_res[0]:
                        seq_name = seq_res[0]
                        print(f"Resetting sequence {seq_name} for table {tbl_quoted}...")
                        cur.execute(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {tbl_quoted}), 1), true);")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error resetting sequences in {key}_db: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    print("=========================================")
    print("🚀 DATABASE SEEDER STARTING...")
    print("=========================================")
    truncate_tables()
    seed_auth()
    seed_product()
    seed_tracking()
    reset_sequences()
    print("\n=========================================")
    print("🎉 ALL POSTGRES DATABASES SEEDED SUCCESSFULLY!")
    print("=========================================")
