#!/usr/bin/env python3
"""
ArchaeoFinder Deduplizierungs-Skript
Findet und entfernt doppelte/ähnliche Bilder aus der Datenbank
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from collections import defaultdict

class Deduplicator:
    def __init__(self, db_path="/app/data/fibula_embeddings.json"):
        self.db_path = Path(db_path)
        self.items = []
        self.duplicates = []
        
    def load_database(self):
        """Lädt die bestehende Datenbank"""
        print("🏺 Lade Datenbank...")
        if not self.db_path.exists():
            print(f"❌ Datenbank nicht gefunden: {self.db_path}")
            return False
            
        with open(self.db_path, 'r', encoding='utf-8') as f:
            self.items = json.load(f)
        
        print(f"✅ {len(self.items)} Einträge geladen")
        return True
    
    def find_hash_duplicates(self):
        """Findet exakte Duplikate per Bild-Hash"""
        print("\n🔍 Suche exakte Duplikate (Hash)...")
        
        hash_dict = defaultdict(list)
        
        for idx, item in enumerate(self.items):
            # Erstelle Hash aus Bild-URL + Titel
            unique_str = f"{item.get('image_url', '')}{item.get('title', '')}"
            item_hash = hashlib.md5(unique_str.encode()).hexdigest()
            hash_dict[item_hash].append(idx)
        
        # Finde Duplikate
        exact_duplicates = []
        for hash_val, indices in hash_dict.items():
            if len(indices) > 1:
                exact_duplicates.append({
                    'hash': hash_val,
                    'count': len(indices),
                    'indices': indices,
                    'keep': indices[0],  # Behalte ersten
                    'remove': indices[1:]  # Entferne Rest
                })
        
        print(f"📊 {len(exact_duplicates)} exakte Duplikate gefunden")
        for dup in exact_duplicates[:5]:  # Zeige erst 5
            print(f"   - Hash {dup['hash'][:8]}...: {dup['count']} Einträge")
        
        return exact_duplicates
    
    def find_similar_embeddings(self, threshold=0.98):
        """Findet ähnliche Bilder per Embedding (Cosine Similarity)"""
        print(f"\n🔍 Suche ähnliche Bilder (Threshold: {threshold})...")
        
        similar_groups = []
        embeddings = []
        
        # Lade Embeddings
        for idx, item in enumerate(self.items):
            emb = item.get('embedding')
            if emb:
                embeddings.append((idx, np.array(emb)))
        
        print(f"   {len(embeddings)} Embeddings geladen")
        
        # Vergleiche paarweise (vereinfacht für große Datenmengen)
        checked = set()
        
        for i, (idx1, emb1) in enumerate(embeddings[:500]):  # Limit für Performance
            if idx1 in checked:
                continue
                
            group = [idx1]
            
            for idx2, emb2 in embeddings[i+1:]:
                if idx2 in checked:
                    continue
                    
                # Cosine Similarity
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                
                if similarity >= threshold:
                    group.append(idx2)
                    checked.add(idx2)
            
            if len(group) > 1:
                similar_groups.append({
                    'count': len(group),
                    'indices': group,
                    'keep': group[0],
                    'remove': group[1:],
                    'similarity': threshold
                })
                
            if len(similar_groups) >= 100:  # Limit Ausgabe
                break
        
        print(f"📊 {len(similar_groups)} ähnliche Gruppen gefunden")
        return similar_groups
    
    def clean_database(self, duplicates, dry_run=True):
        """Bereinigt die Datenbank"""
        print(f"\n🧹 Bereinigung ({'Simulation' if dry_run else 'ECHT'})...")
        
        to_remove = set()
        
        # Sammle alle zu löschenden Indizes
        for dup in duplicates:
            to_remove.update(dup['remove'])
        
        print(f"   {len(to_remove)} Einträge zum Löschen")
        
        if dry_run:
            print("\n⚠️  DRY RUN - keine Änderungen!")
            print("   Führe mit dry_run=False aus um zu bereinigen")
            return
        
        # Erstelle neue saubere Liste
        clean_items = []
        for idx, item in enumerate(self.items):
            if idx not in to_remove:
                clean_items.append(item)
        
        # Backup erstellen
        backup_path = self.db_path.with_suffix('.json.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        print(f"✅ Backup erstellt: {backup_path}")
        
        # Überschreibe mit sauberen Daten
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(clean_items, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Datenbank bereinigt: {len(self.items)} → {len(clean_items)} Einträge")
        print(f"   {len(to_remove)} Duplikate entfernt")
    
    def generate_report(self, hash_dups, embedding_dups):
        """Erstellt einen Bericht"""
        print("\n" + "="*60)
        print("📊 DEDUPLIZIERUNGS-BERICHT")
        print("="*60)
        print(f"Gesamteinträge:     {len(self.items)}")
        print(f"Exakte Duplikate:   {len(hash_dups)} Gruppen")
        print(f"Ähnliche Bilder:    {len(embedding_dups)} Gruppen")
        
        total_to_remove = sum(len(d['remove']) for d in hash_dups + embedding_dups)
        print(f"Zu entfernen:       {total_to_remove} Einträge")
        print(f"Verbleibend:        {len(self.items) - total_to_remove} Einträge")
        print("="*60)

def main():
    print("🏺 ArchaeoFinder Deduplizierung")
    print("="*60)
    
    dedup = Deduplicator()
    
    # 1. Datenbank laden
    if not dedup.load_database():
        return
    
    # 2. Exakte Duplikate finden
    hash_dups = dedup.find_hash_duplicates()
    
    # 3. Ähnliche Embeddings finden (optional - dauert länger)
    if len(dedup.items) < 1000:  # Nur für kleinere DBs
        embedding_dups = dedup.find_similar_embeddings(threshold=0.98)
    else:
        print("\n⏭️  Überspringe Embedding-Prüfung (zu viele Einträge)")
        embedding_dups = []
    
    # 4. Bericht erstellen
    dedup.generate_report(hash_dups, embedding_dups)
    
    # 5. Bereinigung (erstmal als Simulation)
    all_duplicates = hash_dups + embedding_dups
    if all_duplicates:
        dedup.clean_database(all_duplicates, dry_run=True)
        
        print("\n💡 Nächster Schritt:")
        print("   Führe aus mit dry_run=False um wirklich zu bereinigen")
    else:
        print("\n✅ Keine Duplikate gefunden!")

if __name__ == "__main__":
    main()
