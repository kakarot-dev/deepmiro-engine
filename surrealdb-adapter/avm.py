# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 kakarot-dev
# GraphStorage interface originally from MiroShark (https://github.com/aaronjmars/MiroShark)

"""
AVM (Agent Virtual Memory) -- SurrealDB-backed agent state management.

Provides CRUD for agent profiles, action persistence, feed generation,
and cross-simulation agent queries.  All methods are synchronous (matches
the Flask backend used by MiroFish).
"""

import logging
from typing import Dict, Any, List, Optional

from surrealdb import Surreal

from .embedding_service import EmbeddingService

logger = logging.getLogger("mirofish.avm")


class AgentVirtualMemory:
    """Agent state management backed by SurrealDB (sync)."""

    def __init__(self, db: Surreal, embedding: EmbeddingService):
        self._db = db
        self._embedding = embedding

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _query(self, surql: str, params: Optional[Dict[str, Any]] = None) -> list:
        """Execute a SurrealQL query, returning the raw result list."""
        if params:
            return self._db.query(surql, params)
        return self._db.query(surql)

    @staticmethod
    def _rows(result: list, index: int = 0) -> list:
        """Safely extract rows from a SurrealDB query response."""
        if not result:
            return []
        item = result[index] if index < len(result) else None
        if item is None:
            return []
        if isinstance(item, dict):
            return item.get("result", []) or []
        if isinstance(item, list):
            return item
        return []

    # ================================================================
    # Agent CRUD
    # ================================================================

    def create_agents_batch(
        self,
        simulation_id: str,
        graph_id: str,
        profiles: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Bulk-insert agent profiles from OasisProfileGenerator output.

        Embeds each agent's persona for vector similarity search.
        Returns list of SurrealDB record IDs.
        """
        if not profiles:
            return []

        # Batch embed all personas
        persona_texts = [
            p.get("persona", p.get("bio", "")) for p in profiles
        ]
        try:
            persona_embeddings = self._embedding.embed_batch(persona_texts)
        except Exception as exc:
            logger.warning(
                "Persona batch embedding failed, using empty vectors: %s", exc
            )
            persona_embeddings = [[] for _ in profiles]

        record_ids: List[str] = []
        for idx, profile in enumerate(profiles):
            embedding = (
                persona_embeddings[idx]
                if idx < len(persona_embeddings)
                else []
            )
            result = self._query(
                """
                CREATE agent CONTENT {
                    simulation_id: $simulation_id,
                    graph_id: $graph_id,
                    agent_id: $agent_id,
                    user_name: $user_name,
                    name: $name,
                    bio: $bio,
                    persona: $persona,
                    persona_embedding: $persona_embedding,
                    age: $age,
                    gender: $gender,
                    mbti: $mbti,
                    country: $country,
                    profession: $profession,
                    interested_topics: $interested_topics,
                    karma: $karma,
                    friend_count: $friend_count,
                    follower_count: $follower_count,
                    statuses_count: $statuses_count,
                    source_entity_uuid: $source_entity_uuid,
                    source_entity_type: $source_entity_type,
                    active: true,
                    mood: "neutral",
                    memory_summary: "",
                    created_at: time::now(),
                    updated_at: time::now()
                };
                """,
                {
                    "simulation_id": simulation_id,
                    "graph_id": graph_id,
                    "agent_id": profile.get("user_id", idx),
                    "user_name": profile.get(
                        "user_name", profile.get("username", "")
                    ),
                    "name": profile.get("name", ""),
                    "bio": profile.get("bio", ""),
                    "persona": profile.get("persona", ""),
                    "persona_embedding": embedding,
                    "age": profile.get("age"),
                    "gender": profile.get("gender"),
                    "mbti": profile.get("mbti"),
                    "country": profile.get("country"),
                    "profession": profile.get("profession"),
                    "interested_topics": profile.get("interested_topics", []),
                    "karma": profile.get("karma", 1000),
                    "friend_count": profile.get("friend_count", 100),
                    "follower_count": profile.get("follower_count", 150),
                    "statuses_count": profile.get("statuses_count", 500),
                    "source_entity_uuid": profile.get("source_entity_uuid"),
                    "source_entity_type": profile.get("source_entity_type"),
                },
            )
            rows = self._rows(result)
            if rows:
                record_ids.append(str(rows[0].get("id", "")))

        logger.info(
            "Created %d agents for simulation %s",
            len(record_ids),
            simulation_id,
        )
        return record_ids

    def get_active_agents(
        self, simulation_id: str
    ) -> List[Dict[str, Any]]:
        """Load all active agents for a simulation (indexed query)."""
        result = self._query(
            """
            SELECT * FROM agent
            WHERE simulation_id = $sid AND active = true
            ORDER BY agent_id;
            """,
            {"sid": simulation_id},
        )
        return self._rows(result)

    def get_agent(
        self, simulation_id: str, agent_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get a single agent by simulation + agent_id."""
        result = self._query(
            """
            SELECT * FROM agent
            WHERE simulation_id = $sid AND agent_id = $aid
            LIMIT 1;
            """,
            {"sid": simulation_id, "aid": agent_id},
        )
        rows = self._rows(result)
        return rows[0] if rows else None

    def update_agent_state(
        self,
        simulation_id: str,
        agent_id: int,
        updates: Dict[str, Any],
    ) -> None:
        """Update agent mood, memory, stats after an action.

        ``updates`` is a dict of field-name -> new-value pairs.
        Only fields present in the dict are updated.
        """
        if not updates:
            return

        # Build SET clause dynamically
        set_parts = ["updated_at = time::now()"]
        params: Dict[str, Any] = {"sid": simulation_id, "aid": agent_id}
        for key, value in updates.items():
            param_name = f"val_{key}"
            set_parts.append(f"{key} = ${param_name}")
            params[param_name] = value

        set_clause = ", ".join(set_parts)
        self._query(
            f"""
            UPDATE agent SET {set_clause}
            WHERE simulation_id = $sid AND agent_id = $aid;
            """,
            params,
        )

    def deactivate_agent(
        self, simulation_id: str, agent_id: int
    ) -> None:
        """Mark an agent as inactive (left the simulation)."""
        self._query(
            """
            UPDATE agent SET active = false, updated_at = time::now()
            WHERE simulation_id = $sid AND agent_id = $aid;
            """,
            {"sid": simulation_id, "aid": agent_id},
        )

    # ================================================================
    # Actions
    # ================================================================

    def record_action(
        self,
        simulation_id: str,
        action: Dict[str, Any],
    ) -> str:
        """Persist a simulation action. Returns record ID."""
        result = self._query(
            """
            CREATE simulation_action CONTENT {
                simulation_id: $sid,
                round_num: $round,
                timestamp: time::now(),
                platform: $platform,
                agent_id: $aid,
                agent_name: $aname,
                action_type: $atype,
                action_args: $args,
                result: $result,
                success: $success
            };
            """,
            {
                "sid": simulation_id,
                "round": action.get("round_num", 0),
                "platform": action.get("platform", "twitter"),
                "aid": action["agent_id"],
                "aname": action.get("agent_name", ""),
                "atype": action["action_type"],
                "args": action.get("action_args", {}),
                "result": action.get("result"),
                "success": action.get("success", True),
            },
        )
        rows = self._rows(result)
        return str(rows[0]["id"]) if rows else ""

    def get_agent_actions(
        self,
        simulation_id: str,
        agent_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent actions by an agent."""
        result = self._query(
            """
            SELECT * FROM simulation_action
            WHERE simulation_id = $sid AND agent_id = $aid
            ORDER BY timestamp DESC
            LIMIT $limit;
            """,
            {"sid": simulation_id, "aid": agent_id, "limit": limit},
        )
        return self._rows(result)

    def get_round_actions(
        self,
        simulation_id: str,
        round_num: int,
    ) -> List[Dict[str, Any]]:
        """Get all actions from a specific simulation round."""
        result = self._query(
            """
            SELECT * FROM simulation_action
            WHERE simulation_id = $sid AND round_num = $round
            ORDER BY timestamp;
            """,
            {"sid": simulation_id, "round": round_num},
        )
        return self._rows(result)

    # ================================================================
    # Feed generation
    # ================================================================

    def get_agent_feed(
        self,
        simulation_id: str,
        graph_id: str,
        agent_id: int,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Generate a contextual feed for an agent by combining:
        1. Vector search: facts similar to agent persona
        2. Graph traversal: facts connected to previously interacted entities

        Returns deduplicated list of relevant facts.
        """
        # Get agent's persona embedding
        agent = self.get_agent(simulation_id, agent_id)
        if not agent or not agent.get("persona_embedding"):
            logger.warning(
                "Agent %d in sim %s has no persona embedding, returning empty feed",
                agent_id,
                simulation_id,
            )
            return []

        persona_embedding = agent["persona_embedding"]

        # Vector feed: facts semantically similar to agent persona
        vec_feed: List[Dict[str, Any]] = []
        try:
            result = self._query(
                f"""
                SELECT
                    fact,
                    name AS relation_type,
                    in.name AS source_name,
                    out.name AS target_name,
                    vector::similarity::cosine(
                        fact_embedding, $persona_vec
                    ) AS relevance
                FROM relation
                WHERE graph_id = $gid
                    AND fact_embedding <|{limit}|> $persona_vec
                ORDER BY relevance DESC;
                """,
                {
                    "gid": graph_id,
                    "persona_vec": persona_embedding,
                },
            )
            vec_feed = self._rows(result)
        except Exception as exc:
            logger.warning("Vector feed query failed: %s", exc)

        # Graph feed: facts connected to entities the agent interacted with
        graph_feed: List[Dict[str, Any]] = []
        try:
            result = self._query(
                """
                LET $interacted = (
                    SELECT DISTINCT action_args.entity_id AS eid
                    FROM simulation_action
                    WHERE simulation_id = $sid AND agent_id = $aid
                    AND action_args.entity_id != NONE
                );

                SELECT
                    fact,
                    name AS relation_type,
                    in.name AS source_name,
                    out.name AS target_name
                FROM relation
                WHERE in IN $interacted.*.eid OR out IN $interacted.*.eid
                LIMIT $limit;
                """,
                {
                    "sid": simulation_id,
                    "aid": agent_id,
                    "limit": limit,
                },
            )
            # Graph feed is in the second result set (after the LET)
            graph_feed = self._rows(result, index=1)
        except Exception as exc:
            logger.warning("Graph feed query failed: %s", exc)

        # Deduplicate by fact text
        seen_facts: set = set()
        combined: List[Dict[str, Any]] = []
        for item in vec_feed + graph_feed:
            fact = item.get("fact", "")
            if fact and fact not in seen_facts:
                seen_facts.add(fact)
                combined.append(item)

        return combined[:limit]

    # ================================================================
    # Cross-simulation queries
    # ================================================================

    def find_similar_agents(
        self,
        simulation_id: str,
        agent_id: int,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find agents with similar personas (for interaction matching)."""
        agent = self.get_agent(simulation_id, agent_id)
        if not agent or not agent.get("persona_embedding"):
            return []

        persona_vec = agent["persona_embedding"]
        result = self._query(
            f"""
            SELECT
                name,
                persona,
                agent_id,
                vector::similarity::cosine(
                    persona_embedding, $qvec
                ) AS similarity
            FROM agent
            WHERE simulation_id = $sid
                AND active = true
                AND agent_id != $aid
                AND persona_embedding <|{limit}|> $qvec
            ORDER BY similarity DESC;
            """,
            {
                "sid": simulation_id,
                "aid": agent_id,
                "qvec": persona_vec,
            },
        )
        return self._rows(result)

    def get_simulation_stats(
        self, simulation_id: str
    ) -> Dict[str, Any]:
        """Get aggregate statistics for a simulation."""
        # Agent counts
        agent_result = self._query(
            """
            SELECT
                count() AS total,
                count(active = true) AS active_count
            FROM agent
            WHERE simulation_id = $sid
            GROUP ALL;
            """,
            {"sid": simulation_id},
        )
        agent_rows = self._rows(agent_result)
        agent_stats = agent_rows[0] if agent_rows else {}

        # Action counts by type
        action_result = self._query(
            """
            SELECT action_type, count() AS cnt
            FROM simulation_action
            WHERE simulation_id = $sid
            GROUP BY action_type
            ORDER BY cnt DESC;
            """,
            {"sid": simulation_id},
        )
        action_rows = self._rows(action_result)

        # Round count
        round_result = self._query(
            """
            SELECT math::max(round_num) AS max_round
            FROM simulation_action
            WHERE simulation_id = $sid
            GROUP ALL;
            """,
            {"sid": simulation_id},
        )
        round_rows = self._rows(round_result)
        max_round = round_rows[0].get("max_round", 0) if round_rows else 0

        return {
            "simulation_id": simulation_id,
            "total_agents": agent_stats.get("total", 0),
            "active_agents": agent_stats.get("active_count", 0),
            "total_rounds": max_round,
            "actions_by_type": {
                r["action_type"]: r["cnt"] for r in action_rows
            },
        }
