import tarfile
import os
import sys

archives = ['train.tar.gz', 'test1.tar.gz', 'test2.tar.gz']

for archive in archives:
    print(f"\n--- ARCHIVE: {archive} ---")
    if not os.path.exists(archive):
        print("NOT FOUND")
        continue
        
    try:
        with tarfile.open(archive, "r:gz") as tar:
            members = tar.getmembers()
            print(f"Total files/dirs: {len(members)}")
            
            top_levels = set([m.name.split('/')[0] for m in members if '/' in m.name])
            print(f"Top level dirs: {top_levels}")
            
            india_files = [m for m in members if "India" in m.name]
            print(f"India subset files: {len(india_files)}")
            
            if india_files:
                india_imgs = [m for m in india_files if m.name.endswith('.jpg')]
                india_xmls = [m for m in india_files if m.name.endswith('.xml')]
                print(f"India images: {len(india_imgs)}, India XMLs: {len(india_xmls)}")
                
                if india_xmls:
                    sample_xml = india_xmls[0]
                    f = tar.extractfile(sample_xml)
                    if f:
                        print(f"Sample XML ({sample_xml.name}) snippet:")
                        print(f.read().decode('utf-8')[:400])
                    
    except Exception as e:
        print(f"Error: {e}")
