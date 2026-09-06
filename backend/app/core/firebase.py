import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Inisialisasi Firebase Admin SDK dari Variable ENV (Railway) atau File (Localhost)."""
    try:
        if not firebase_admin._apps:
            firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
            firebase_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")

            # 1. Coba baca dari Variable String JSON (Railway)
            if firebase_json:
                try:
                    cred_dict = json.loads(firebase_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK berhasil diinisialisasi via ENV JSON!")
                    return True
                except Exception as e:
                    logger.error(f"Gagal parse FIREBASE_CREDENTIALS_JSON: {str(e)}")

            # 2. Coba baca dari File Path (Localhost)
            if os.path.exists(firebase_path):
                cred = credentials.Certificate(firebase_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK berhasil diinisialisasi via File!")
                return True
            
            # 3. Fallback jika file berada di root backend
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            alt_path = os.path.join(base_dir, "firebase-credentials.json")
            if os.path.exists(alt_path):
                cred = credentials.Certificate(alt_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK berhasil diinisialisasi via Alt Path!")
                return True

            logger.warning("Kredensial Firebase tidak ditemukan baik di ENV maupun File.")
            return False
        return True
    except Exception as e:
        logger.error(f"Gagal menginisialisasi Firebase Admin SDK: {str(e)}")
        return False

# Inisialisasi saat modul dimuat
FIREBASE_INITIALIZED = initialize_firebase()


def verify_token(token: str) -> dict:
    if not FIREBASE_INITIALIZED:
        if os.getenv("ALLOW_DEV_AUTH", "false").lower() == "true":
            logger.warning("DEVELOPMENT MODE: Bypassing Firebase auth with mock user")
            return {
                "uid": "dev_user_001",
                "email": "dev@example.com",
                "name": "Development User",
                "role": "user"
            }
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan autentikasi tidak tersedia. Firebase belum diinisialisasi."
        )
    
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token sudah kedaluwarsa. Silakan login ulang."
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token sudah dicabut. Silakan login ulang."
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token tidak valid. Pastikan token Firebase yang benar."
        )
    except Exception as e:
        logger.error(f"Error verifikasi token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Gagal memverifikasi token autentikasi"
        )


def get_user_role(claims: dict) -> str:
    return claims.get("role", "user")