#!/usr/bin/env python3
"""
Database Reset Script
Clears all vector data from Qdrant database
"""

import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class DatabaseResetter:
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        """Initialize database resetter"""
        print("Initializing Database Resetter...")
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port, check_compatibility=False)
        self.collection_name = "ntu_courses"
    
    def check_connection(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            collections = self.client.get_collections()
            print(f"Connected to Qdrant. Found {len(collections.collections)} collections")
            return True
        except Exception as e:
            print(f"Failed to connect to Qdrant: {e}")
            print("Make sure Qdrant is running: docker compose up -d")
            return False
    
    def list_collections(self):
        """List all existing collections"""
        try:
            collections = self.client.get_collections()
            if collections.collections:
                print("Existing collections:")
                for collection in collections.collections:
                    count = self.client.count(collection_name=collection.name)
                    print(f"  - {collection.name}: {count.count} points")
            else:
                print("No collections found")
        except Exception as e:
            print(f"Error listing collections: {e}")
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete specific collection"""
        try:
            self.client.delete_collection(collection_name=collection_name)
            print(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def delete_all_collections(self) -> bool:
        """Delete all collections"""
        try:
            collections = self.client.get_collections()
            deleted_count = 0
            
            for collection in collections.collections:
                if self.delete_collection(collection.name):
                    deleted_count += 1
            
            print(f"Deleted {deleted_count} collections")
            return True
        except Exception as e:
            print(f"Failed to delete collections: {e}")
            return False
    
    def reset_specific_collection(self, collection_name: str = None) -> bool:
        """Reset specific collection (default: ntu_courses)"""
        target_collection = collection_name or self.collection_name
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if target_collection in collection_names:
                count_before = self.client.count(collection_name=target_collection)
                print(f"Collection '{target_collection}' has {count_before.count} points")
                
                # Delete the collection
                self.delete_collection(target_collection)
                print(f"Reset collection: {target_collection}")
                return True
            else:
                print(f"Collection '{target_collection}' does not exist")
                return True
                
        except Exception as e:
            print(f"Failed to reset collection: {e}")
            return False
    
    def reset_all(self) -> bool:
        """Reset entire database"""
        print("Resetting entire vector database...")
        return self.delete_all_collections()


def main():
    """Main execution function"""
    print("=" * 50)
    print("VECTOR DATABASE RESET TOOL")
    print("=" * 50)
    
    resetter = DatabaseResetter()
    
    # Check connection first
    if not resetter.check_connection():
        sys.exit(1)
    
    # Show current state
    print("\nCurrent database state:")
    resetter.list_collections()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--all":
            # Reset all collections
            print("\nResetting ALL collections...")
            if resetter.reset_all():
                print("Database completely reset")
            else:
                print("Failed to reset database")
                sys.exit(1)
                
        elif command == "--collection" and len(sys.argv) > 2:
            # Reset specific collection
            collection_name = sys.argv[2]
            print(f"\nResetting collection: {collection_name}")
            if resetter.reset_specific_collection(collection_name):
                print(f"Collection '{collection_name}' reset")
            else:
                print(f"Failed to reset collection '{collection_name}'")
                sys.exit(1)
                
        elif command == "--help":
            print("\nUsage:")
            print("  python reset_db.py                    # Reset ntu_courses collection")
            print("  python reset_db.py --all              # Reset all collections")
            print("  python reset_db.py --collection NAME  # Reset specific collection")
            print("  python reset_db.py --help             # Show this help")
            
        else:
            print(f"\nUnknown command: {command}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # Default: reset ntu_courses collection
        print(f"\nResetting default collection: {resetter.collection_name}")
        if resetter.reset_specific_collection():
            print("Default collection reset")
        else:
            print("Failed to reset default collection")
            sys.exit(1)
    
    print("\nNext steps:")
    print("  Run: python ingest/embed_upload.py (to reload data)")
    print("  Run: python scripts/test_vector_db.py (to verify functionality)")


if __name__ == "__main__":
    main() 