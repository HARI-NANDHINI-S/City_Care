import os
import sys
import sqlite3
import argparse
from typing import List, Tuple, Set

def get_db_referenced_paths(db_path: str) -> Set[str]:
    """Retrieve all image paths stored in the active SQLite database using read-only access."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    cur = conn.cursor()
    cur.execute("SELECT original_image_path FROM issue_images WHERE original_image_path IS NOT NULL;")
    paths = set(row[0] for row in cur.fetchall() if row[0])
    cur.execute("SELECT annotated_image_path FROM issue_images WHERE annotated_image_path IS NOT NULL;")
    for row in cur.fetchall():
        if row[0]:
            paths.add(row[0])
    conn.close()
    return paths

def inventory_uploads(uploads_dir: str, referenced_paths: Set[str]) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """Identify referenced vs orphaned upload files."""
    referenced = []
    orphaned = []
    
    if not os.path.exists(uploads_dir):
        return referenced, orphaned
        
    for fname in sorted(os.listdir(uploads_dir)):
        fpath = os.path.join(uploads_dir, fname)
        if not os.path.isfile(fpath):
            continue
            
        size = os.path.getsize(fpath)
        # Check both relative URL format (/uploads/original/fname) and relative filename
        is_ref = (
            f"/uploads/original/{fname}" in referenced_paths or
            f"uploads/original/{fname}" in referenced_paths or
            fname in referenced_paths
        )
        
        if is_ref:
            referenced.append((fpath, size))
        else:
            orphaned.append((fpath, size))
            
    return referenced, orphaned

def main():
    parser = argparse.ArgumentParser(description="Audit and clean orphaned files in backend/uploads/original.")
    parser.add_argument("--db", default="backend/civicsense.db", help="Path to SQLite database")
    parser.add_argument("--dir", default="backend/uploads/original", help="Path to uploads original directory")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Perform dry-run only without deleting (default: True)")
    parser.add_argument("--confirm-delete", action="store_true", default=False, help="Explicit confirmation required to perform deletion")
    args = parser.parse_args()

    print("=" * 70)
    print("      CIVICVISION AI — UPLOAD STORAGE AUDIT UTILITY")
    print("=" * 70)
    print(f"Database Path : {args.db}")
    print(f"Uploads Dir   : {args.dir}")
    print(f"Dry-Run Mode  : {'YES (Safe Inspection)' if not args.confirm_delete else 'NO (DELETION ENABLED)'}")
    print("-" * 70)

    try:
        ref_paths = get_db_referenced_paths(args.db)
    except Exception as e:
        print(f"ERROR accessing database: {e}")
        sys.exit(1)

    referenced, orphaned = inventory_uploads(args.dir, ref_paths)
    
    print(f"Referenced Uploads (in DB) : {len(referenced)} files")
    for p, sz in referenced:
        print(f"  [REFERENCED] {os.path.basename(p)} ({sz} bytes)")
        
    print(f"\nOrphaned Uploads (not in DB): {len(orphaned)} files")
    total_orphan_bytes = sum(sz for _, sz in orphaned)
    for p, sz in orphaned:
        print(f"  [ORPHANED]   {os.path.basename(p)} ({sz} bytes)")
    print(f"Total Orphaned Disk Usage: {total_orphan_bytes / 1024:.2f} KB ({total_orphan_bytes} bytes)")

    if args.confirm_delete:
        print("\n[ACTION] Explicit confirmation provided. Deleting orphaned files...")
        deleted_count = 0
        for p, sz in orphaned:
            try:
                os.remove(p)
                deleted_count += 1
            except Exception as e:
                print(f"  Failed to delete {p}: {e}")
        print(f"Cleanup complete. Deleted {deleted_count} orphaned files.")
    else:
        print("\n[NOTICE] Dry-run complete. Zero files were deleted. Pass --confirm-delete to delete orphaned files.")

if __name__ == "__main__":
    main()
