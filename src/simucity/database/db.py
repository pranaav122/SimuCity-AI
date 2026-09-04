"""Database schema and persistence layer for experiments and simulation histories."""

import json
import sqlite3
from typing import Any, Dict, List, Optional
from simucity.experiments.experiment_runner import ExperimentResult


class SimulationDatabase:
    """Lightweight and robust SQL database repository for storing experiments, snapshots, and telemetry."""

    def __init__(self, db_path: str = "simucity.db") -> None:
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Experiments table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                model TEXT NOT NULL,
                number_of_agents INTEGER NOT NULL,
                simulation_days INTEGER NOT NULL,
                seed INTEGER NOT NULL,
                duration_seconds REAL,
                total_ticks INTEGER,
                total_tokens INTEGER,
                total_cost_usd REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Metrics snapshots table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                tick INTEGER NOT NULL,
                day INTEGER NOT NULL,
                time_str TEXT NOT NULL,
                gini_wealth REAL,
                average_money REAL,
                average_gpa REAL,
                average_stress REAL,
                cooperation_rate REAL,
                active_groups INTEGER,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
            """)

            # Emergent patterns table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergent_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL,
                tick_detected INTEGER,
                evidence_json TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
            """)

            # Agents summary table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                name TEXT NOT NULL,
                data_json TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
            )
            """)
            conn.commit()

    def save_experiment_result(self, result: ExperimentResult) -> None:
        """Persists a complete experiment result into the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cfg = result.config
            cursor.execute("""
            INSERT OR REPLACE INTO experiments (
                experiment_id, name, model, number_of_agents, simulation_days, seed,
                duration_seconds, total_ticks, total_tokens, total_cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cfg.experiment_id, cfg.name, cfg.model, cfg.number_of_agents, cfg.simulation_days, cfg.seed,
                result.duration_seconds, result.total_ticks, result.total_tokens, result.total_cost_usd
            ))

            # Insert metrics snapshots
            for m in result.all_metrics:
                cursor.execute("""
                INSERT INTO metrics_snapshots (
                    experiment_id, tick, day, time_str, gini_wealth, average_money,
                    average_gpa, average_stress, cooperation_rate, active_groups
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cfg.experiment_id, m.tick, m.day, m.time_str, m.gini_wealth, m.average_money,
                    m.average_gpa, m.average_stress, m.cooperation_rate, m.active_groups_count
                ))

            # Insert emergent patterns
            for p in result.detected_patterns:
                cursor.execute("""
                INSERT INTO emergent_patterns (
                    experiment_id, pattern_type, title, description, confidence, tick_detected, evidence_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    cfg.experiment_id, p.pattern_type.value, p.title, p.description,
                    p.confidence, p.tick_detected, json.dumps(p.evidence)
                ))

            # Insert agent summaries
            for a in result.agent_summaries:
                cursor.execute("""
                INSERT INTO agent_summaries (experiment_id, agent_id, name, data_json)
                VALUES (?, ?, ?, ?)
                """, (cfg.experiment_id, a["id"], a["name"], json.dumps(a)))

            conn.commit()

    def list_experiments(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,))
            row = cursor.fetchone()
            if not row:
                return None
            exp_data = dict(row)

            # Get metrics
            cursor.execute("SELECT * FROM metrics_snapshots WHERE experiment_id = ? ORDER BY tick ASC", (experiment_id,))
            exp_data["metrics"] = [dict(r) for r in cursor.fetchall()]

            # Get patterns
            cursor.execute("SELECT * FROM emergent_patterns WHERE experiment_id = ?", (experiment_id,))
            exp_data["patterns"] = [
                {**dict(r), "evidence": json.loads(r["evidence_json"])} for r in cursor.fetchall()
            ]

            # Get agents
            cursor.execute("SELECT * FROM agent_summaries WHERE experiment_id = ?", (experiment_id,))
            exp_data["agents"] = [json.loads(r["data_json"]) for r in cursor.fetchall()]

            return exp_data
        finally:
            conn.close()

