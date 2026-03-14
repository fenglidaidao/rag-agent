# tests/test_file_context.py
import pytest
from rag.ingest import (
    store_file_content_for_prompt,
    get_file_content_for_prompt,
    clear_file_content_for_prompt,
)

class TestFileContextIsolation:

    def setup_method(self):
        """每个测试前清空上下文"""
        for uid in [1, 2, 3]:
            clear_file_content_for_prompt(uid)

    def test_store_and_get_single_user(self):
        """单用户存取正常"""
        store_file_content_for_prompt("用户1的文件内容", user_id=1)
        result = get_file_content_for_prompt(user_id=1)
        assert result == "用户1的文件内容"

    def test_user_isolation(self):
        """不同用户的文件上下文互相隔离"""
        store_file_content_for_prompt("用户1的私有文件", user_id=1)
        store_file_content_for_prompt("用户2的私有文件", user_id=2)

        assert get_file_content_for_prompt(user_id=1) == "用户1的私有文件"
        assert get_file_content_for_prompt(user_id=2) == "用户2的私有文件"

        # 用户1的内容不会出现在用户2的上下文中
        assert "用户1" not in get_file_content_for_prompt(user_id=2)
        assert "用户2" not in get_file_content_for_prompt(user_id=1)

    def test_empty_context_returns_empty_string(self):
        """未上传文件时应返回空字符串"""
        result = get_file_content_for_prompt(user_id=99)
        assert result == ""

    def test_overwrite_same_user(self):
        """同一用户再次上传文件应覆盖旧内容"""
        store_file_content_for_prompt("第一个文件", user_id=1)
        store_file_content_for_prompt("第二个文件", user_id=1)
        assert get_file_content_for_prompt(user_id=1) == "第二个文件"

    def test_clear_only_affects_target_user(self):
        """清除某用户上下文不影响其他用户"""
        store_file_content_for_prompt("用户1内容", user_id=1)
        store_file_content_for_prompt("用户2内容", user_id=2)

        clear_file_content_for_prompt(user_id=1)

        assert get_file_content_for_prompt(user_id=1) == ""
        assert get_file_content_for_prompt(user_id=2) == "用户2内容"

    def test_concurrent_users(self):
        """并发场景下各用户上下文独立"""
        import threading

        results = {}

        def upload_and_read(user_id: int):
            store_file_content_for_prompt(f"用户{user_id}的内容", user_id=user_id)
            import time; time.sleep(0.05)  # 模拟异步
            results[user_id] = get_file_content_for_prompt(user_id=user_id)

        threads = [threading.Thread(target=upload_and_read, args=(i,)) for i in range(1, 6)]
        for t in threads: t.start()
        for t in threads: t.join()

        for user_id in range(1, 6):
            assert results[user_id] == f"用户{user_id}的内容"