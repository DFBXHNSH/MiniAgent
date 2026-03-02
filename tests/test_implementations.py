"""
Tests for the tool implementations module.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from tools.implementations import (
    _is_dangerous_command,
    _DANGEROUS_PATTERNS
)


class TestIsDangerousCommand:
    """Test cases for _is_dangerous_command function."""

    def test_safe_commands_pass(self):
        """Test that safe commands are not blocked."""
        safe_commands = [
            "ls -la",
            "cat file.txt",
            "echo hello",
            "grep pattern file",
            "python script.py",
            "git status",
            "npm install"
        ]
        for cmd in safe_commands:
            is_dangerous, _ = _is_dangerous_command(cmd)
            assert not is_dangerous, f"Command '{cmd}' should be safe"

    def test_rm_rf_root_blocked(self):
        """Test that rm -rf / is blocked."""
        is_dangerous, reason = _is_dangerous_command("rm -rf /")
        assert is_dangerous
        assert "rm" in reason.lower()

    def test_shutdown_blocked(self):
        """Test that shutdown command is blocked."""
        is_dangerous, _ = _is_dangerous_command("shutdown now")
        assert is_dangerous

    def test_sudo_shutdown_blocked(self):
        """Test that sudo shutdown is blocked."""
        is_dangerous, _ = _is_dangerous_command("sudo shutdown now")
        assert is_dangerous

    def test_reboot_blocked(self):
        """Test that reboot command is blocked."""
        is_dangerous, _ = _is_dangerous_command("reboot")
        assert is_dangerous

    def test_halt_blocked(self):
        """Test that halt command is blocked."""
        is_dangerous, _ = _is_dangerous_command("halt")
        assert is_dangerous

    def test_userdel_blocked(self):
        """Test that userdel is blocked."""
        is_dangerous, _ = _is_dangerous_command("sudo userdel testuser")
        assert is_dangerous

    def test_systemctl_stop_blocked(self):
        """Test that systemctl stop is blocked."""
        is_dangerous, _ = _is_dangerous_command("sudo systemctl stop nginx")
        assert is_dangerous

    def test_systemctl_disable_blocked(self):
        """Test that systemctl disable is blocked."""
        is_dangerous, _ = _is_dangerous_command("systemctl disable nginx")
        assert is_dangerous

    def test_systemctl_mask_blocked(self):
        """Test that systemctl mask is blocked."""
        is_dangerous, _ = _is_dangerous_command("systemctl mask nginx")
        assert is_dangerous

    def test_dd_to_dev_zero_blocked(self):
        """Test that dd to /dev/zero is blocked."""
        is_dangerous, _ = _is_dangerous_command("dd if=/dev/zero of=/dev/sda")
        assert is_dangerous

    def test_mkfs_blocked(self):
        """Test that mkfs is blocked."""
        is_dangerous, _ = _is_dangerous_command("mkfs.ext4 /dev/sda1")
        assert is_dangerous

    def test_redirect_to_dev_blocked(self):
        """Test that redirect to /dev/ is blocked."""
        is_dangerous, _ = _is_dangerous_command("echo test > /dev/null")
        assert is_dangerous

    def test_redirect_to_proc_blocked(self):
        """Test that redirect to /proc/ is blocked."""
        is_dangerous, _ = _is_dangerous_command("echo test > /proc/version")
        assert is_dangerous

    def test_redirect_to_sys_blocked(self):
        """Test that redirect to /sys/ is blocked."""
        is_dangerous, _ = _is_dangerous_command("echo test > /sys/kernel")
        assert is_dangerous

    def test_history_c_blocked(self):
        """Test that history -c is blocked."""
        is_dangerous, _ = _is_dangerous_command("history -c")
        assert is_dangerous

    def test_chmod_root_777_blocked(self):
        """Test that chmod 777 / is blocked."""
        is_dangerous, _ = _is_dangerous_command("chmod 777 /")
        assert is_dangerous

    def test_chmod_etc_777_blocked(self):
        """Test that chmod 777 /etc/ is blocked."""
        is_dangerous, _ = _is_dangerous_command("chmod 777 /etc/passwd")
        assert is_dangerous

    def test_apt_get_remove_blocked(self):
        """Test that apt-get remove is blocked."""
        is_dangerous, _ = _is_dangerous_command("sudo apt-get remove package")
        assert is_dangerous

    def test_yum_remove_blocked(self):
        """Test that yum remove is blocked."""
        is_dangerous, _ = _is_dangerous_command("sudo yum remove package")
        assert is_dangerous

    def test_dangerous_pattern_with_whitespace(self):
        """Test that patterns with leading whitespace are detected."""
        is_dangerous, _ = _is_dangerous_command("   rm -rf /")
        assert is_dangerous

    def test_multi_line_command(self):
        """Test that multi-line commands are checked."""
        is_dangerous, _ = _is_dangerous_command("echo safe\nshutdown now")
        assert is_dangerous

    def test_word_containing_sudo_not_blocked(self):
        """Test that words containing 'sudo' are not blocked."""
        # This tests that we're matching at the start of command, not substring
        is_dangerous, _ = _is_dangerous_command("echo pseudonym")
        assert not is_dangerous

    def test_word_containing_reboot_not_blocked(self):
        """Test that words containing 'reboot' are not blocked."""
        is_dangerous, _ = _is_dangerous_command("cat reboot.txt")
        assert not is_dangerous

    def test_safe_chmod(self):
        """Test that safe chmod is not blocked."""
        is_dangerous, _ = _is_dangerous_command("chmod +x script.sh")
        assert not is_dangerous

    def test_safe_systemctl_start(self):
        """Test that systemctl start is not blocked."""
        is_dangerous, _ = _is_dangerous_command("systemctl start nginx")
        assert not is_dangerous

    def test_safe_systemctl_status(self):
        """Test that systemctl status is not blocked."""
        is_dangerous, _ = _is_dangerous_command("systemctl status nginx")
        assert not is_dangerous

    def test_apt_get_install_not_blocked(self):
        """Test that apt-get install is not blocked."""
        is_dangerous, _ = _is_dangerous_command("sudo apt-get install package")
        assert not is_dangerous


class TestDangerousPatterns:
    """Test that dangerous patterns list is properly configured."""

    def test_patterns_are_strings(self):
        """Test that all patterns are strings."""
        for pattern in _DANGEROUS_PATTERNS:
            assert isinstance(pattern, str)

    def test_patterns_are_regex_valid(self):
        """Test that all patterns compile as valid regex."""
        import re
        for pattern in _DANGEROUS_PATTERNS:
            # This will raise re.error if pattern is invalid
            re.compile(pattern)

    def test_patterns_cover_critical_commands(self):
        """Test that critical dangerous commands are covered."""
        patterns_str = " ".join(_DANGEROUS_PATTERNS)
        assert "rm\\s+-rf" in patterns_str
        assert "shutdown" in patterns_str
        assert "reboot" in patterns_str
        assert "systemctl" in patterns_str
