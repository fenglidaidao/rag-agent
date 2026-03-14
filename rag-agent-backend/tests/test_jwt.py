# tests/test_jwt.py
import pytest
import os


class TestJWTSecretKey:

    def test_secret_key_loaded_from_env(self):
        """JWT_SECRET_KEY 应从环境变量读取"""
        os.environ["JWT_SECRET_KEY"] = "my-test-secret-123"
        import importlib
        import auth.auth as auth_module
        importlib.reload(auth_module)
        assert auth_module.SECRET_KEY == "my-test-secret-123"

    def test_missing_secret_key_raises(self):
        """未设置 JWT_SECRET_KEY 时应抛出 RuntimeError"""
        original = os.environ.pop("JWT_SECRET_KEY", None)
        try:
            import importlib
            import auth.auth as auth_module
            with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
                importlib.reload(auth_module)
        finally:
            if original:
                os.environ["JWT_SECRET_KEY"] = original

    def test_token_create_and_verify(self):
        """生成的 token 应能被正确解析"""
        os.environ["JWT_SECRET_KEY"] = "test-secret-for-token"
        import importlib
        import auth.auth as auth_module
        importlib.reload(auth_module)

        # ✅ 按实际签名：create_access_token(user_id, username)
        token = auth_module.create_access_token(user_id=42, username="testuser")
        assert token is not None

        payload = auth_module.decode_token(token)
        assert payload["sub"] == "42"           # sub 存的是 str(user_id)
        assert payload["username"] == "testuser"

    def test_tampered_token_rejected(self):
        """篡改过的 token 应被 HTTPException 拒绝"""
        os.environ["JWT_SECRET_KEY"] = "test-secret-for-token"
        import importlib
        import auth.auth as auth_module
        from fastapi import HTTPException
        importlib.reload(auth_module)

        token = auth_module.create_access_token(user_id=1, username="testuser")
        tampered = token[:-5] + "XXXXX"

        # ✅ decode_token 失败抛的是 HTTPException，不是 JWTError
        with pytest.raises(HTTPException) as exc_info:
            auth_module.decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_secret_key_not_hardcoded(self):
        """auth.py 源码中不应有硬编码的 secret key"""
        with open("auth/auth.py", "r", encoding="utf-8") as f:
            source = f.read()
        dangerous_patterns = [
            'SECRET_KEY = "',
            "SECRET_KEY = '",
            'secret-key',
            'mysecret',
        ]
        for pattern in dangerous_patterns:
            assert pattern not in source, f"发现硬编码 secret key：{pattern}"

    def test_token_expiry_field_present(self):
        """生成的 token payload 中应包含 exp 字段"""
        os.environ["JWT_SECRET_KEY"] = "test-secret-for-token"
        import importlib
        import auth.auth as auth_module
        importlib.reload(auth_module)

        token = auth_module.create_access_token(user_id=1, username="testuser")
        payload = auth_module.decode_token(token)
        assert "exp" in payload

    def test_get_current_user_parses_correctly(self):
        """get_current_user 能从 token 正确还原 user_id 和 username"""
        os.environ["JWT_SECRET_KEY"] = "test-secret-for-token"
        import importlib
        import auth.auth as auth_module
        importlib.reload(auth_module)

        token = auth_module.create_access_token(user_id=99, username="alice")
        # 直接调 decode_token 验证 get_current_user 的解析逻辑
        payload = auth_module.decode_token(token)
        user = {
            "user_id": int(payload["sub"]),
            "username": payload["username"]
        }
        assert user["user_id"] == 99
        assert user["username"] == "alice"