"""
Firebase Initialization Module - Layer 0 Foundation
Handles Firebase Admin SDK initialization with proper error handling and singleton pattern.
CRITICAL: Must have serviceAccountKey.json in project root before running.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, auth, db as realtime_db
from firebase_admin.exceptions import FirebaseError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FirebaseManager:
    """Singleton manager for Firebase services with robust error handling"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.app = None
            self.firestore_client = None
            self.realtime_db = None
            self._initialized = True
    
    def initialize(self, service_account_path: str = "serviceAccountKey.json") -> bool:
        """
        Initialize Firebase Admin SDK with comprehensive error handling
        
        Args:
            service_account_path: Path to Firebase service account key JSON
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Check if file exists
            key_path = Path(service_account_path)
            if not key_path.exists():
                logger.error(f"Service account key not found at {service_account_path}")
                return False
            
            # Read and validate JSON
            with open(key_path, 'r') as f:
                key_data = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            if not all(field in key_data for field in required_fields):
                logger.error("Service account key missing required fields")
                return False
            
            # Initialize Firebase
            cred = credentials.Certificate(str(key_path))
            
            # Check if already initialized
            if not firebase_admin._apps:
                self.app = firebase_admin.initialize_app(cred, {
                    'databaseURL': f"https://{key_data['project_id']}.firebaseio.com"
                })
                logger.info(f"Firebase initialized for project: {key_data['project_id']}")
            else:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            
            # Initialize clients
            self.firestore_client = firestore.client()
            self.realtime_db = realtime_db
            
            # Test connection
            self._test_connections()
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in service account key: {e}")
            return False
        except FirebaseError as e:
            logger.error(f"Firebase initialization error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected initialization error: {e}")
            return False
    
    def _test_connections(self) -> None:
        """Test Firestore and Realtime Database connections"""
        try:
            # Test Firestore
            test_ref = self.firestore_client.collection('_health_check').document('test')
            test_ref.set({'timestamp': firestore.SERVER_TIMESTAMP})
            test_ref.delete()
            logger.info("Firestore connection successful")
            
            # Test Realtime Database if configured
            if hasattr(self, 'app') and self.app.project_id:
                logger.info(f"Realtime Database configured for project: {self.app.project_id}")
                
        except Exception as e:
            logger.warning(f"Connection test warning (non-critical): {e}")
    
    def get_firestore(self) -> firestore.Client:
        """Get Firestore client with lazy initialization"""
        if self.firestore_client is None:
            if not self.initialize():
                raise RuntimeError("Firebase not initialized")
        return self.firestore_client
    
    def get_realtime_db(self):
        """Get Realtime Database reference"""
        if self.realtime_db is None:
            if not self.initialize():
                raise RuntimeError("Firebase not initialized")
        return self.realtime_db

# Global instance
firebase_manager = FirebaseManager()