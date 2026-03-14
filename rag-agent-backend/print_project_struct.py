import os
from pathlib import Path
import fnmatch


def print_dir_tree(
        root_path: Path,
        parent_prefix: str = "",
        is_last: bool = False,
        show_hidden: bool = False,
        ignore_dirs: list = None,
        ignore_files: list = None,
        is_root: bool = True
):
    """
    递归打印目录树结构，修复根目录下多一层缩进的问题

    Args:
        root_path: 要遍历的根目录 Path 对象
        parent_prefix: 父级前缀字符串（内部递归使用）
        is_last: 是否是当前层级的最后一个条目（内部递归使用）
        show_hidden: 是否显示隐藏文件/文件夹（以 . 开头）
        ignore_dirs: 要忽略的目录列表
        ignore_files: 要忽略的文件列表（支持通配符）
        is_root: 是否是根目录（核心修复点）
    """
    # 设置默认忽略项
    if ignore_dirs is None:
        ignore_dirs = [".git", "__pycache__", ".venv", "venv", ".idea", ".vscode"]
    if ignore_files is None:
        ignore_files = [".gitignore", "*.pyc", "*.pyo", "*.pyd"]

    # 跳过需要忽略的目录/文件
    if root_path.is_dir() and root_path.name in ignore_dirs:
        return
    if root_path.is_file():
        for pattern in ignore_files:
            if fnmatch.fnmatch(root_path.name, pattern):
                return
    if not show_hidden and root_path.name.startswith("."):
        return

    # 核心修复：根目录直接打印，子条目根据层级生成前缀
    if is_root:
        # 根目录无任何前缀
        print(root_path.name)
    else:
        # 子条目生成正确的连接符
        connector = "└── " if is_last else "├── "
        print(f"{parent_prefix}{connector}{root_path.name}")

    # 文件直接返回（递归终止）
    if root_path.is_file():
        return

    # 处理目录的子条目
    try:
        # 排序：文件夹在前，文件在后，按名称字母序
        entries = sorted(
            [entry for entry in root_path.iterdir()],
            key=lambda x: (not x.is_dir(), x.name.lower())
        )

        # 遍历子条目
        for idx, entry in enumerate(entries):
            entry_is_last = idx == len(entries) - 1

            # 生成子条目前缀（核心修复：根目录的子条目前缀为空）
            if is_root:
                # 根目录的子节点，父前缀为空
                new_parent_prefix = ""
            else:
                # 非根目录的子节点，根据是否最后一个生成前缀
                new_parent_prefix = parent_prefix + ("    " if is_last else "│   ")

            # 递归处理子条目（根目录的子节点不再是根）
            print_dir_tree(
                entry,
                new_parent_prefix,
                entry_is_last,
                show_hidden,
                ignore_dirs,
                ignore_files,
                is_root=False  # 子节点都不是根目录
            )

    except PermissionError:
        print(f"{parent_prefix}│   [权限不足，无法访问]")


if __name__ == "__main__":
    # 以当前脚本运行目录为根目录
    current_dir = Path.cwd()

    # 打印目录树
    print_dir_tree(
        current_dir,
        show_hidden=False
    )