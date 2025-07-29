import pytest
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
import os

# Test the password hashing functions directly
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password_byte_enc)

def create_access_token(data: dict, secret_key: str = "test_secret", expire_minutes: int = 30):
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

class TestPasswordHashing:
    def test_hash_password_creates_different_hash(self):
        """Same password should create different hashes due to salt"""
        password = "test_password123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    def test_verify_password_correct(self):
        """Password verification should work for correct password"""
        password = "test_password123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Password verification should fail for wrong password"""
        password = "test_password123"
        wrong_password = "wrong_password123"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_special_characters(self):
        """Password hashing should work with special characters"""
        password = "p@ssw0rd!#$%"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

class TestJWTToken:
    def test_create_access_token(self):
        """JWT token creation should include correct user data"""
        user_data = {
            "sub": "test@example.com",
            "user_id": "123e4567-e89b-12d3-a456-426614174000"
        }
        secret_key = "test_secret_key_for_testing"
        
        token = create_access_token(user_data, secret_key)
        
        # Decode token to verify contents
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        assert decoded["sub"] == user_data["sub"]
        assert decoded["user_id"] == user_data["user_id"]
        assert "exp" in decoded
        
        # Expiration should be in the future
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        assert exp_time > datetime.now(timezone.utc)
        
    def test_token_expiration_time(self):
        """Token should expire at the correct time"""
        user_data = {"sub": "test@example.com", "user_id": "test-id"}
        secret_key = "test_secret_key"
        expire_minutes = 60
        
        token = create_access_token(user_data, secret_key, expire_minutes)
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        
        # Should be within 1 minute of expected time
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60
    
    def test_invalid_token_verification(self):
        """Invalid tokens should raise exceptions"""
        user_data = {"sub": "test@example.com"}
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"
        
        token = create_access_token(user_data, correct_secret)
        
        # Should work with correct secret
        decoded = jwt.decode(token, correct_secret, algorithms=["HS256"])
        assert decoded["sub"] == user_data["sub"]
        
        # Should fail with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, wrong_secret, algorithms=["HS256"])
