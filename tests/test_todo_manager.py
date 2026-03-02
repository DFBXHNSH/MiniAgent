"""
Tests for TodoManager module.
"""

import pytest
from src.tools.todo_manager import TodoManager


class TestTodoManager:
    """Test cases for TodoManager."""

    def test_init(self):
        """Test TodoManager initialization."""
        manager = TodoManager()
        assert manager.items == []

    def test_update_valid_items(self):
        """Test updating with valid todo items."""
        manager = TodoManager()
        items = [
            {
                "content": "Task 1",
                "status": "pending",
                "activeForm": "Doing task 1..."
            },
            {
                "content": "Task 2",
                "status": "in_progress",
                "activeForm": "Doing task 2..."
            }
        ]
        result = manager.update(items)
        assert "Task 1" in result
        assert "Task 2" in result
        assert len(manager.items) == 2

    def test_update_missing_content(self):
        """Test that missing content raises ValueError."""
        manager = TodoManager()
        items = [{"status": "pending", "activeForm": "Doing..."}]
        with pytest.raises(ValueError, match="content required"):
            manager.update(items)

    def test_update_invalid_status(self):
        """Test that invalid status raises ValueError."""
        manager = TodoManager()
        items = [
            {"content": "Task", "status": "invalid", "activeForm": "Doing..."}
        ]
        with pytest.raises(ValueError, match="invalid status"):
            manager.update(items)

    def test_update_missing_active_form(self):
        """Test that missing activeForm raises ValueError."""
        manager = TodoManager()
        items = [{"content": "Task", "status": "pending"}]
        with pytest.raises(ValueError, match="activeForm required"):
            manager.update(items)

    def test_max_items_constraint(self):
        """Test that more than 20 items raises ValueError."""
        manager = TodoManager()
        items = [
            {
                "content": f"Task {i}",
                "status": "pending",
                "activeForm": f"Doing task {i}..."
            }
            for i in range(21)
        ]
        with pytest.raises(ValueError, match="Max 20 todos allowed"):
            manager.update(items)

    def test_one_in_progress_constraint(self):
        """Test that only one item can be in_progress at a time."""
        manager = TodoManager()
        items = [
            {
                "content": "Task 1",
                "status": "in_progress",
                "activeForm": "Doing task 1..."
            },
            {
                "content": "Task 2",
                "status": "in_progress",
                "activeForm": "Doing task 2..."
            }
        ]
        with pytest.raises(ValueError, match="Only one task can be in_progress"):
            manager.update(items)

    def test_render_empty(self):
        """Test rendering empty todo list."""
        manager = TodoManager()
        assert manager.render() == "No todos."

    def test_render_with_items(self):
        """Test rendering with various item statuses."""
        manager = TodoManager()
        items = [
            {"content": "Done task", "status": "completed", "activeForm": "Doing..."},
            {"content": "Current task", "status": "in_progress", "activeForm": "Doing current task..."},
            {"content": "Pending task", "status": "pending", "activeForm": "Doing pending..."}
        ]
        manager.update(items)
        result = manager.render()
        assert "[x] Done task" in result
        assert "[>] Current task <- Doing current task..." in result
        assert "[ ] Pending task" in result
        assert "(1/3 completed)" in result

    def test_render_completed_count(self):
        """Test that completed count is correct."""
        manager = TodoManager()
        items = [
            {"content": "Task 1", "status": "completed", "activeForm": "..."},
            {"content": "Task 2", "status": "completed", "activeForm": "..."},
            {"content": "Task 3", "status": "pending", "activeForm": "..."}
        ]
        manager.update(items)
        result = manager.render()
        assert "(2/3 completed)" in result

    def test_update_replaces_previous(self):
        """Test that update replaces previous items."""
        manager = TodoManager()
        items = [
            {"content": "Old task", "status": "pending", "activeForm": "..."}
        ]
        manager.update(items)
        assert len(manager.items) == 1

        new_items = [
            {"content": "New task", "status": "in_progress", "activeForm": "..."}
        ]
        manager.update(new_items)
        assert len(manager.items) == 1
        assert manager.items[0]["content"] == "New task"
