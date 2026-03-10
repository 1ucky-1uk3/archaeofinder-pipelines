#!/usr/bin/env python3
"""
ArchaeoFinder Supabase Deduplizierung
Findet und entfernt doppelte/ähnliche Einträge direkt in Supabase
"""

import os
import json
import numpy as np
from supabase import create_client
from collections import defaultdict
import hashlib

class SupabaseDeduplicator:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "https://neyudzqjqbqfaxbfnglx.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.items = []
        self.table = "fibula_embeddings"
        
    def load_all_embeddings(self):
        """Lädt alle Embeddings aus Supabase"""
        print("🏺 Lade Daten aus Supabase...")
        
        # Pagination für große Tabellen
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            response = self.supabase.table(self.table)\
                .select("id, image_url, title, embedding, source, created_at")\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if not response.data:
                break
                
            all_data.extend(response.data)
            offset += page_size
            
            if len(response.data) < page_size:
                break
        
        self.items = all_data
        print(f"✅ {len(self.items)} Einträge aus Supabase geladen")
        return len(self.items)
    
    def find_hash_duplicates(self):
        """Findet exakte Duplikate"""
        print("\n🔍 Suche exakte Duplikate...")
        
        hash_dict = defaultdict(list)
        
        for item in self.items:
            # Hash aus URL + Titel
            unique_str = f"{item.get('image_url', '')}{item.get('title', '')}"
            item_hash = hashlib.md5(unique_str.encode()).hexdigest()
            hash_dict[item_hash].append(item)
        
        duplicates = []
        for hash_val, items in hash_dict.items():
            if len(items) > 1:
                duplicates.append({
                    'hash': hash_val,
                    'count': len(items),
                    'items': items,
                    'keep_id': items[0]['id'],
                    'remove_ids': [i['id'] for i in items[1:]]
                })
        
        print(f"📊 {len(duplicates)} exakte Duplikat-Gruppen gefunden")
        for dup in duplicates[:3]:
            print(f"   - {dup['hash'][:8]}: {dup['count']} Einträge (IDs: {dup['remove_ids'][:3]}...)")
        
        return duplicates
    
    def find_embedding_duplicates(self, threshold=0.98, max_comparisons=10000):
        """Findet ähnliche Einträge per Cosine Similarity"""
        print(f"\n🔍 Suche ähnliche Einträge (Threshold: {threshold})...")
        
        # Nur Items mit Embeddings
        items_with_emb = [(i, item) for i, item in enumerate(self.items) 
                          if item.get('embedding')]
        
        print(f"   {len(items_with_emb)} Einträge mit Embeddings")
        
        if len(items_with_emb) > 5000:
            print(f"   ⚠️  Zu viele Einträge, begrenze auf {max_comparisons} Vergleiche")
            items_with_emb = items_with_emb[:max_comparisons]
        
        duplicates = []
        checked = set()
        
        for i, (idx1, item1) in enumerate(items_with_emb):
            if idx1 in checked:
                continue
            
            emb1 = np.array(item1['embedding'])
            group = [item1]
            
            for idx2, item2 in items_with_emb[i+1:]:
                if idx2 in checked:
                    continue
                
                emb2 = np.array(item2['embedding'])
                
                # Cosine Similarity
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                
                if similarity >= threshold:
                    group.append(item2)
                    checked.add(idx2)
            
            if len(group) > 1:
                duplicates.append({
                    'count': len(group),
                    'items': group,
                    'keep_id': group[0]['id'],
                    'remove_ids': [i['id'] for i in group[1:]],
                    'similarity': threshold
                })
        
        print(f"📊 {len(duplicates)} ähnliche Gruppen gefunden")
        return duplicates
    
    def preview_deletions(self, all_duplicates):
        """Zeigt Vorschau der Löschungen"""
        print("\n" + "="*60)
        print("📋 VORSCHAU: Zu löschende Einträge")
        print("="*60)
        
        total_remove = sum(len(d['remove_ids']) for d in all_duplicates)
        
        for dup in all_duplicates[:5]:  # Zeige nur erst 5
            print(f"\n   Gruppe ({dup['count']} Einträge):")
            print(f"   → Behalte ID: {dup['keep_id']}")
            print(f"   → Lösche IDs: {dup['remove_ids']}")
        
        if len(all_duplicates) > 5:
            print(f"\n   ... und {len(all_duplicates) - 5} weitere Gruppen")
        
        print(f"\n   GESAMT: {total_remove} Einträge zum Löschen")
        print(f"   Verbleiben: {len(self.items) - total_remove}")
        print("="*60)
        
        return total_remove
    
    def delete_duplicates(self, all_duplicates, dry_run=True):
        """Löscht Duplikate aus Supabase"""
        print(f"\n🧹 LÖSCHUNG ({'SIMULATION' if dry_run else 'ECHT'})...")
        
        all_remove_ids = []
        for dup in all_duplicates:
            all_remove_ids.extend(dup['remove_ids'])
        
        if not all_remove_ids:
            print("   Keine Einträge zum Löschen")
            return
        
        print(f"   {len(all_remove_ids)} Einträge werden {'SIMULIERT' if dry_run else 'GElÖSCHT'}")
        
        if dry_run:
            print("\n   ⚠️  DRY RUN - nichts wurde gelöscht!")
            print("   Setze dry_run=False um wirklich zu löschen")
            return
        
        # Backup erstellen
        print("\n💾 Erstelle Backup...")
        backup_data = []
        for dup in all_duplicates:
            for item in dup['items']:
                backup_data.append(item)
        
        backup_file = f"supabase_backup_{len(self.items)}_items.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Backup gespeichert: {backup_file}")
        
        # Lösche in Batches (Supabase Limit)
        batch_size = 100
        deleted = 0
        
        for i in range(0, len(all_remove_ids), batch_size):
            batch = all_remove_ids[i:i+batch_size]
            
            try:
                response = self.supabase.table(self.table)\
                    .delete()\
                    .in_("id", batch)\
                    .execute()
                deleted += len(batch)
                print(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} gelöscht")
            except Exception as e:
                print(f"   ❌ Fehler bei Batch {i//batch_size + 1}: {e}")
        
        print(f"\n✅ Bereinigung abgeschlossen: {deleted} Einträge gelöscht")

def main():
    print("🏺 ArchaeoFinder Supabase Deduplizierung")
    print("="*60)
    
    dedup = SupabaseDeduplicator()
    
    # 1. Daten laden
    count = dedup.load_all_embeddings()
    if count == 0:
        return
    
    # 2. Duplikate finden
    hash_dups = dedup.find_hash_duplicates()
    
    # 3. Ähnliche finden (optional)
    if count < 3000:
        emb_dups = dedup.find_embedding_duplicates(threshold=0.98)
    else:
        print("\n⏭️  Überspringe Embedding-Check (zu viele Daten)")
        emb_dups = []
    
    # 4. Zusammenfassen
    all_dups = hash_dups + emb_dups
    
    if not all_dups:
        print("\n✅ Keine Duplikate gefunden!")
        return
    
    # 5. Vorschau
    dedup.preview_deletions(all_dups)
    
    # 6. Bereinigung (Simulation)
    dedup.delete_duplicates(all_dups, dry_run=True)
    
    print("\n💡 Nächster Schritt:")
    print("   1. Prüfe ob die Vorschau korrekt ist")
    print("   2. Editiere Skript: dry_run=True → dry_run=False")
    print("   3. Führe erneut aus")

if __name__ == "__main__":
    main()
