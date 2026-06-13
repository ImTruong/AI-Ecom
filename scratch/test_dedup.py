import csv
import re
import os

DATA_DIR = "/home/truong/CodeProject/SAD/AI-Ecom/AI/data"

def clean_name(name):
    return re.sub(r"\s*\(ID\s+\d+\)\s*", "", name).strip()

def dry_run():
    # 1. Categories
    category_map = {}
    seen_categories = {}
    categories_rows = []
    
    with open(os.path.join(DATA_DIR, "categories.csv"), "r") as f:
        for r in csv.DictReader(f):
            cid = int(r["id"])
            cname_clean = clean_name(r["name"])
            if cname_clean not in seen_categories:
                seen_categories[cname_clean] = cid
                category_map[cid] = cid
                categories_rows.append((cid, cname_clean + " (new)"))
            else:
                category_map[cid] = seen_categories[cname_clean]
                
    print(f"Categories: Total in CSV={len(category_map)}, Primary (unique)={len(categories_rows)}")
    
    # 2. Products
    product_map = {}
    seen_products = {}
    product_clean_names = {}
    products_rows = []
    
    with open(os.path.join(DATA_DIR, "products.csv"), "r") as f:
        for r in csv.DictReader(f):
            pid = int(r["id"])
            pname_clean = clean_name(r["name"])
            product_clean_names[pid] = pname_clean
            
            if pname_clean not in seen_products:
                seen_products[pname_clean] = pid
                product_map[pid] = pid
                products_rows.append((pid, pname_clean + " (new)", category_map[int(r["category_id"])]))
            else:
                product_map[pid] = seen_products[pname_clean]
                
    print(f"Products: Total in CSV={len(product_map)}, Primary (unique)={len(products_rows)}")
    
    # 3. Variants
    variant_map = {}
    primary_variants = {}  # (clean_product_name, variant_name) -> primary_variant_id
    variants_rows = []
    
    # First pass: identify and save primary variants
    with open(os.path.join(DATA_DIR, "product_variants.csv"), "r") as f:
        variants = list(csv.DictReader(f))
        
    for v in variants:
        vid = int(v["id"])
        pid = int(v["product_id"])
        vname = v["name"].strip()
        clean_pname = product_clean_names.get(pid)
        primary_pid = product_map.get(pid)
        
        if pid == primary_pid:
            primary_variants[(clean_pname, vname)] = vid
            variant_map[vid] = vid
            variants_rows.append((vid, primary_pid, vname))
            
    # Second pass: map duplicate variants to primary variants
    for v in variants:
        vid = int(v["id"])
        pid = int(v["product_id"])
        vname = v["name"].strip()
        clean_pname = product_clean_names.get(pid)
        primary_pid = product_map.get(pid)
        
        if pid != primary_pid:
            primary_vid = primary_variants.get((clean_pname, vname))
            if primary_vid is None:
                # Fallback to any variant of primary product if name doesn't match
                # Let's find any variant with this clean_pname
                fallback_vids = [pvid for (cp, vn), pvid in primary_variants.items() if cp == clean_pname]
                primary_vid = fallback_vids[0] if fallback_vids else None
            variant_map[vid] = primary_vid
            
    print(f"Variants: Total in CSV={len(variants)}, Primary (unique)={len(variants_rows)}")
    
    # 4. Variant Options
    options_rows = []
    with open(os.path.join(DATA_DIR, "product_variant_options.csv"), "r") as f:
        for r in csv.DictReader(f):
            vid = int(r["variant_id"])
            if variant_map.get(vid) == vid:
                options_rows.append(r)
    print(f"Variant Options: Total in CSV={len(options_rows)} (filtered from CSV)")
    
    # 5. Tracking Views
    views_rows = []
    with open(os.path.join(DATA_DIR, "product_views.csv"), "r") as f:
        for r in csv.DictReader(f):
            pid = int(r["product_id"])
            mapped_pid = product_map.get(pid)
            if mapped_pid:
                views_rows.append((r["customer_id"], mapped_pid))
    print(f"Product Views: Total mapped={len(views_rows)}")

if __name__ == "__main__":
    dry_run()
