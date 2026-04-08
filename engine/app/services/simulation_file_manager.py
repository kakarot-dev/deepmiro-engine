"""
Centralized file I/O for simulation data.

Owns all file paths and provides typed methods for every file operation.
All services call this instead of doing direct filesystem I/O.

Does NOT change OASIS subprocess behavior — it still writes files the same
way. This class only consolidates how the Flask backend reads/writes.
"""

import csv
import json
import os
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger("deepmiro.file_manager")


class SimulationFileManager:
    """Centralized file I/O for a single simulation."""

    def __init__(self, simulation_id: str, base_dir: Optional[str] = None):
        self.simulation_id = simulation_id
        self.base_dir = base_dir or Config.OASIS_SIMULATION_DATA_DIR
        self.sim_dir = os.path.join(self.base_dir, simulation_id)

    # ── Path resolution ──────────────────────────────────────────

    @property
    def state_path(self) -> str:
        return os.path.join(self.sim_dir, "state.json")

    @property
    def run_state_path(self) -> str:
        return os.path.join(self.sim_dir, "run_state.json")

    @property
    def config_path(self) -> str:
        return os.path.join(self.sim_dir, "simulation_config.json")

    @property
    def env_status_path(self) -> str:
        return os.path.join(self.sim_dir, "env_status.json")

    @property
    def simulation_log_path(self) -> str:
        return os.path.join(self.sim_dir, "simulation.log")

    @property
    def ipc_commands_dir(self) -> str:
        return os.path.join(self.sim_dir, "ipc_commands")

    @property
    def ipc_responses_dir(self) -> str:
        return os.path.join(self.sim_dir, "ipc_responses")

    def profile_path(self, platform: str) -> str:
        if platform == "reddit":
            return os.path.join(self.sim_dir, "reddit_profiles.json")
        return os.path.join(self.sim_dir, "twitter_profiles.csv")

    def actions_log_path(self, platform: str) -> str:
        return os.path.join(self.sim_dir, platform, "actions.jsonl")

    def db_path(self, platform: str) -> str:
        return os.path.join(self.sim_dir, f"{platform}_simulation.db")

    def ipc_command_path(self, command_id: str) -> str:
        return os.path.join(self.ipc_commands_dir, f"{command_id}.json")

    def ipc_response_path(self, command_id: str) -> str:
        return os.path.join(self.ipc_responses_dir, f"{command_id}.json")

    # ── Directory setup ──────────────────────────────────────────

    def ensure_dirs(self) -> None:
        """Create simulation directory and IPC subdirectories."""
        os.makedirs(self.sim_dir, exist_ok=True)
        os.makedirs(self.ipc_commands_dir, exist_ok=True)
        os.makedirs(self.ipc_responses_dir, exist_ok=True)
        for platform in ("twitter", "reddit"):
            os.makedirs(os.path.join(self.sim_dir, platform), exist_ok=True)

    def exists(self) -> bool:
        return os.path.isdir(self.sim_dir)

    # ── State files ──────────────────────────────────────────────

    def read_state(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.state_path)

    def write_state(self, data: Dict[str, Any]) -> bool:
        return self._write_json(self.state_path, data)

    def read_run_state(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.run_state_path)

    def write_run_state(self, data: Dict[str, Any]) -> bool:
        return self._write_json(self.run_state_path, data)

    def read_env_status(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.env_status_path)

    def write_env_status(self, status: str) -> bool:
        from datetime import datetime
        return self._write_json(self.env_status_path, {
            "status": status,
            "timestamp": datetime.now().isoformat(),
        })

    def is_env_alive(self) -> bool:
        data = self.read_env_status()
        if data is None:
            return False
        return data.get("status") == "alive"

    # ── Config ───────────────────────────────────────────────────

    def read_config(self) -> Optional[Dict[str, Any]]:
        return self._read_json(self.config_path)

    def write_config(self, config_json: str) -> bool:
        os.makedirs(self.sim_dir, exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(config_json)
            return True
        except OSError as exc:
            logger.error("Failed to write config %s: %s", self.config_path, exc)
            return False

    # ── Profiles ─────────────────────────────────────────────────

    def read_profiles(self, platform: str = "reddit") -> List[Dict[str, Any]]:
        """Read agent profiles. Handles JSON (reddit) and CSV (twitter)."""
        path = self.profile_path(platform)
        if not os.path.exists(path):
            return []

        try:
            if platform == "reddit":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []

            # Twitter CSV
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                profiles = []
                for row in reader:
                    profiles.append({
                        "realname": row.get("name", ""),
                        "username": row.get("username", ""),
                        "bio": row.get("description", ""),
                        "persona": row.get("user_char", ""),
                        **{k: v for k, v in row.items()
                           if k not in ("name", "username", "description", "user_char")},
                    })
                return profiles
        except (json.JSONDecodeError, OSError, csv.Error) as exc:
            logger.warning("Failed to read profiles %s: %s", path, exc)
            return []

    # ── Action logs (JSONL) ──────────────────────────────────────

    def read_actions_streaming(
        self, platform: str, position: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Read new action log entries from the given file position.

        Returns (actions, new_position) for position-tracked polling.
        """
        path = self.actions_log_path(platform)
        if not os.path.exists(path):
            return [], position

        actions: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                f.seek(position)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if "platform" not in entry:
                            entry["platform"] = platform
                        actions.append(entry)
                    except json.JSONDecodeError:
                        continue
                new_position = f.tell()
            return actions, new_position
        except OSError as exc:
            logger.warning("Failed to stream actions %s: %s", path, exc)
            return [], position

    def read_all_actions(
        self,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Read all actions with optional filters. Reads both platforms if none specified."""
        platforms = [platform] if platform else ["twitter", "reddit"]
        actions: List[Dict[str, Any]] = []

        for plat in platforms:
            path = self.actions_log_path(plat)
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        # Skip event markers
                        if "event_type" in entry:
                            continue
                        if "platform" not in entry:
                            entry["platform"] = plat
                        if agent_id is not None and entry.get("agent_id") != agent_id:
                            continue
                        if round_num is not None and entry.get("round_num") != round_num:
                            continue
                        actions.append(entry)
            except OSError as exc:
                logger.warning("Failed to read actions %s: %s", path, exc)

        # Legacy fallback: single actions.jsonl at sim root
        if not actions:
            legacy = os.path.join(self.sim_dir, "actions.jsonl")
            if os.path.exists(legacy):
                try:
                    with open(legacy, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if "event_type" in entry:
                                continue
                            if agent_id is not None and entry.get("agent_id") != agent_id:
                                continue
                            if round_num is not None and entry.get("round_num") != round_num:
                                continue
                            actions.append(entry)
                except OSError:
                    pass

        return actions

    def actions_file_exists(self, platform: str) -> bool:
        return os.path.exists(self.actions_log_path(platform))

    # ── SQLite database access ───────────────────────────────────

    def _connect_db(self, platform: str) -> Optional[sqlite3.Connection]:
        path = self.db_path(platform)
        if not os.path.exists(path):
            return None
        try:
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as exc:
            logger.warning("Failed to connect to %s: %s", path, exc)
            return None

    def query_posts(
        self,
        platform: str = "reddit",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query posts from the OASIS SQLite DB. Returns (posts, total_count)."""
        conn = self._connect_db(platform)
        if conn is None:
            return [], 0
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM post"
            )
            total = cursor.fetchone()[0]
            cursor = conn.execute(
                "SELECT * FROM post ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            posts = [dict(row) for row in cursor.fetchall()]
            return posts, total
        except sqlite3.OperationalError as exc:
            logger.warning("query_posts failed (%s): %s", platform, exc)
            return [], 0
        finally:
            conn.close()

    def query_comments(
        self,
        post_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query comments from the Reddit OASIS SQLite DB."""
        conn = self._connect_db("reddit")
        if conn is None:
            return []
        try:
            if post_id is not None:
                cursor = conn.execute(
                    "SELECT * FROM comment WHERE post_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (post_id, limit, offset),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM comment ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as exc:
            logger.warning("query_comments failed: %s", exc)
            return []
        finally:
            conn.close()

    def query_agent_posts(
        self, agent_id: int, platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all posts by a specific agent across platforms."""
        platforms = [platform] if platform else ["twitter", "reddit"]
        posts: List[Dict[str, Any]] = []
        for plat in platforms:
            conn = self._connect_db(plat)
            if conn is None:
                continue
            try:
                # Map agent_id to user_id via user table
                cursor = conn.execute(
                    "SELECT user_id FROM user WHERE agent_id = ?", (agent_id,)
                )
                row = cursor.fetchone()
                if row is None:
                    continue
                user_id = row[0]
                cursor = conn.execute(
                    "SELECT * FROM post WHERE user_id = ? ORDER BY created_at",
                    (user_id,),
                )
                for r in cursor.fetchall():
                    d = dict(r)
                    d["platform"] = plat
                    posts.append(d)
            except sqlite3.OperationalError as exc:
                logger.warning("query_agent_posts failed (%s): %s", plat, exc)
            finally:
                conn.close()
        return posts

    def query_interview_history(
        self, agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get interview records from the OASIS trace table."""
        results: List[Dict[str, Any]] = []
        for plat in ("twitter", "reddit"):
            conn = self._connect_db(plat)
            if conn is None:
                continue
            try:
                if agent_id is not None:
                    cursor = conn.execute(
                        "SELECT * FROM trace WHERE action = 'interview' AND user_id = ? ORDER BY created_at",
                        (agent_id,),
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM trace WHERE action = 'interview' ORDER BY created_at"
                    )
                for row in cursor.fetchall():
                    d = dict(row)
                    d["platform"] = plat
                    # Parse info field if it's JSON
                    info = d.get("info", "")
                    if isinstance(info, str):
                        try:
                            d["info"] = json.loads(info)
                        except json.JSONDecodeError:
                            pass
                    results.append(d)
            except sqlite3.OperationalError as exc:
                logger.warning("query_interview_history failed (%s): %s", plat, exc)
            finally:
                conn.close()
        return results

    # ── IPC files ────────────────────────────────────────────────

    def write_ipc_command(self, command: Dict[str, Any]) -> str:
        """Write IPC command file. Returns the command file path."""
        os.makedirs(self.ipc_commands_dir, exist_ok=True)
        command_id = command.get("command_id", "")
        path = self.ipc_command_path(command_id)
        self._write_json(path, command)
        return path

    def read_ipc_response(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Read IPC response file. Returns None if not ready."""
        path = self.ipc_response_path(command_id)
        if not os.path.exists(path):
            return None
        return self._read_json(path)

    def delete_ipc_files(self, command_id: str) -> None:
        """Clean up both command and response files."""
        for path in (
            self.ipc_command_path(command_id),
            self.ipc_response_path(command_id),
        ):
            try:
                os.remove(path)
            except OSError:
                pass

    def poll_ipc_commands(self) -> Optional[Dict[str, Any]]:
        """Scan ipc_commands dir, return the oldest pending command."""
        if not os.path.exists(self.ipc_commands_dir):
            return None

        command_files = []
        for filename in os.listdir(self.ipc_commands_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.ipc_commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))

        command_files.sort(key=lambda x: x[1])

        for filepath, _ in command_files:
            data = self._read_json(filepath)
            if data is not None:
                return data
        return None

    # ── Report files ─────────────────────────────────────────────

    @staticmethod
    def report_dir(report_id: str) -> str:
        return os.path.join(Config.UPLOAD_FOLDER, "reports", report_id)

    @classmethod
    def is_report_generating(cls, simulation_id: str) -> bool:
        """Check if any report for this simulation is currently generating."""
        reports_dir = os.path.join(Config.UPLOAD_FOLDER, "reports")
        if not os.path.exists(reports_dir):
            return False
        for folder in os.listdir(reports_dir):
            meta_path = os.path.join(reports_dir, folder, "meta.json")
            if not os.path.exists(meta_path):
                continue
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if (
                    meta.get("simulation_id") == simulation_id
                    and meta.get("status") in ("pending", "planning", "generating")
                ):
                    return True
            except (json.JSONDecodeError, OSError):
                continue
        return False

    # ── Private helpers ──────────────────────────────────────────

    def _read_json(self, path: str) -> Optional[Dict[str, Any]]:
        """Read a JSON file with consistent error handling."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read %s: %s", path, exc)
            return None

    def _write_json(self, path: str, data: Any) -> bool:
        """Write JSON atomically via tempfile + os.replace."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            fd, tmp = tempfile.mkstemp(
                dir=os.path.dirname(path), suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, path)
                return True
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except (OSError, TypeError, ValueError) as exc:
            logger.error("Failed to write %s: %s", path, exc)
            return False
