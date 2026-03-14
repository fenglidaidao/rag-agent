# tests/conftest.py
import pytest
import os
import sys

# 确保能找到项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(autouse=True)
def set_env():
    """每个测试前设置必要的环境变量"""
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    os.environ.setdefault("OPENAI_BASE_URL", "https://api.openai.com/v1")
    os.environ.setdefault("MODEL_NAME", "gpt-4o-mini")
    yield