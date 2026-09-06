import os
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_JSON")

# Inisialisasi Firebase Admin SDK
def initialize_firebase():
    """Inisialisasi Firebase Admin SDK dengan error handling yang lebih baik."""
    try:
        if not firebase_admin._apps:
            if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
                logger.warning(f"File kredensial Firebase tidak ditemukan: {FIREBASE_CREDENTIALS_PATH}")
                logger.warning("Autentikasi Firebase akan dinonaktifkan. Pastikan untuk:")
                logger.warning("1. Download firebase-credentials.json dari Firebase Console")
                logger.warning("2. Simpan di: " + os.path.abspath(FIREBASE_CREDENTIALS_PATH))
                return False
            
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK berhasil diinisialisasi")
            return True
        return True
    except Exception as e:
        logger.error(f"Gagal menginisialisasi Firebase Admin SDK: {str(e)}")
        logger.error("Pastikan file firebase-credentials.json valid dan memiliki format JSON yang benar")
        return False

# Inisialisasi saat modul dimuat
FIREBASE_INITIALIZED = initialize_firebase()


def verify_token(token: str) -> dict:
    """Verifikasi Firebase ID token menggunakan Admin SDK.

    Args:
        token: Firebase ID token (JWT) dari header Authorization.

    Returns:
        dict: Claims token yang sudah ter-decode (uid, email, name, dll).

    Raises:
        HTTPException: 401 jika token invalid, expired, atau tidak terverifikasi.
    """
    if not FIREBASE_INITIALIZED:
        # Development mode bypass - HANYA untuk local testing
        # PENTING: Set ALLOW_DEV_AUTH=true DI .env.local SAJA, JANGAN di production!
        if os.getenv("ALLOW_DEV_AUTH", "false").lower() == "true":
            logger.warning("⚠️  DEVELOPMENT MODE: Bypassing Firebase auth with mock user")
            logger.warning("⚠️  JANGAN gunakan ALLOW_DEV_AUTH=true di production!")
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
    """Ambil role user dari claims token, default 'user'.

    Args:
        claims: Dictionary claims hasil verify_token.

    Returns:
        str: Role user ('user' jika tidak ada key 'role').
    """
    return claims.get("role", "user")
