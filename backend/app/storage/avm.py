"""
Agent Virtual Memory (AVM) -- smart paging for simulation agents.

Keeps persona data (small, static) in SurrealDB permanently, while
agent context (large, growing conversation history / observed posts)
is loaded on-demand before each round and evicted afterward.

Memory budget:  500 agents x persona only + 20 active x full context
              = ~1-2 GB  (vs 7-10 GB without paging)
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("mirofish.avm")


class AgentVirtualMemory:
    """
    Manages agent lifecycle in SurrealDB for a single simulation.

    The constructor accepts a SurrealDBStorage instance (obtained via
    ``get_storage()``) so the caller controls connection reuse.
    """

    def __init__(self, storage):
        """
        Args:
            storage: A connected SurrealDBStorage instance.
        """
        self._storage = storage

    # ----------------------------------------------------------------
    # Bulk agent creation
    # ----------------------------------------------------------------

    def create_agents_batch(
        self,
        simulation_id: str,
        graph_id: str,
        profiles: List[Dict[str, Any]],
    ) -> int:
        """
        Bulk-insert agent profiles with optional persona embeddings.

        Args:
            simulation_id: Owning simulation.
            graph_id:      Knowledge-graph id used to enrich personas.
            profiles:      List of profile dicts (from OasisProfileGenerator).

        Returns:
            Number of agents created.
        """
        enriched = []
        for p in profiles:
            p_copy = dict(p)
            p_copy["graph_id"] = graph_id

            # Generate persona embedding if the storage has an embedding service
            if not p_copy.get("persona_embedding") and p_copy.get("persona"):
                try:
                    embedding = self._storage._embedding.embed_batch(
                        [p_copy["persona"]]
                    )
                    p_copy["persona_embedding"] = embedding[0] if embedding else []
                except Exception as exc:
                    logger.warning("Persona embedding failed for agent %s: %s",
                                   p_copy.get("name", "?"), exc)
                    p_copy["persona_embedding"] = []
            enriched.append(p_copy)

        try:
            self._storage.save_agent_profiles(simulation_id, enriched)
            logger.info(
                "AVM: created %d agents for sim=%s graph=%s",
                len(enriched), simulation_id, graph_id,
            )
        except Exception as exc:
            logger.error("AVM: bulk agent creation failed: %s", exc)
            raise
        return len(enriched)

    # ----------------------------------------------------------------
    # Active agent queries
    # ----------------------------------------------------------------

    def get_active_agents(self, simulation_id: str) -> List[Dict[str, Any]]:
        """SELECT active agents for a simulation (lightweight rows)."""
        try:
            result = self._storage._query(
                """
                SELECT agent_id, user_name, name, persona, mood, active
                FROM agent
                WHERE simulation_id = $sid AND active = true
                ORDER BY agent_id ASC;
                """,
                {"sid": simulation_id},
            )
            return self._storage._rows(result)
        except Exception as exc:
            logger.warning("AVM: get_active_agents failed: %s", exc)
            return []

    # ----------------------------------------------------------------
    # Context load / save / evict  (the core paging mechanism)
    # ----------------------------------------------------------------

    def load_agent_context(
        self,
        simulation_id: str,
        agent_id: int,
        recent_actions_limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Load recent actions + feed for an agent to build an LLM prompt.

        Returns a dict with keys: persona, mood, memory_summary,
        recent_actions, feed_items.
        """
        context: Dict[str, Any] = {
            "persona": "",
            "mood": "neutral",
            "memory_summary": "",
            "recent_actions": [],
            "feed_items": [],
        }

        try:
            # 1. Load agent record (persona, mood, memory)
            agent_result = self._storage._query(
                """
                SELECT persona, mood, memory_summary, bio, name
                FROM agent
                WHERE simulation_id = $sid AND agent_id = $aid
                LIMIT 1;
                """,
                {"sid": simulation_id, "aid": agent_id},
            )
            rows = self._storage._rows(agent_result)
            if rows:
                agent = rows[0]
                context["persona"] = agent.get("persona", "")
                context["mood"] = agent.get("mood", "neutral")
                context["memory_summary"] = agent.get("memory_summary", "")

            # 2. Load recent actions by this agent
            action_result = self._storage._query(
                """
                SELECT round_num, action_type, action_args, platform, timestamp
                FROM simulation_action
                WHERE simulation_id = $sid AND agent_id = $aid
                ORDER BY timestamp DESC
                LIMIT $lim;
                """,
                {"sid": simulation_id, "aid": agent_id, "lim": recent_actions_limit},
            )
            context["recent_actions"] = self._storage._rows(action_result)

        except Exception as exc:
            logger.warning(
                "AVM: load_agent_context failed (sim=%s, agent=%d): %s",
                simulation_id, agent_id, exc,
            )
        return context

    def save_agent_state(
        self,
        simulation_id: str,
        agent_id: int,
        state: Dict[str, Any],
    ) -> None:
        """
        Persist mood / memory_summary after a round completes.

        Args:
            state: Dict with optional keys ``mood``, ``memory_summary``.
        """
        set_clauses = ["updated_at = time::now()"]
        params: Dict[str, Any] = {"sid": simulation_id, "aid": agent_id}

        if "mood" in state:
            set_clauses.append("mood = $mood")
            params["mood"] = state["mood"]
        if "memory_summary" in state:
            set_clauses.append("memory_summary = $mem")
            params["mem"] = state["memory_summary"]
        if "active" in state:
            set_clauses.append("active = $active")
            params["active"] = state["active"]

        try:
            self._storage._query(
                f"UPDATE agent SET {', '.join(set_clauses)} "
                f"WHERE simulation_id = $sid AND agent_id = $aid;",
                params,
            )
        except Exception as exc:
            logger.warning(
                "AVM: save_agent_state failed (sim=%s, agent=%d): %s",
                simulation_id, agent_id, exc,
            )

    def evict_agent_context(self, agent_id: int) -> None:
        """
        Clear in-memory context for an agent.

        Currently a no-op because context lives in SurrealDB, not in
        Python memory.  Reserved for future in-process LRU cache.
        """
        logger.debug("AVM: evict context for agent %d (no-op)", agent_id)

    # ----------------------------------------------------------------
    # Feed generation (vector + graph query)
    # ----------------------------------------------------------------

    def get_agent_feed(
        self,
        simulation_id: str,
        agent_id: int,
        graph_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Build a personalised feed for an agent using:
          1. Vector similarity on persona_embedding vs recent posts
          2. Graph neighbourhood in the knowledge graph

        Falls back to recent global actions when vector search is
        unavailable.
        """
        feed: List[Dict[str, Any]] = []

        try:
            # Strategy 1: vector similarity -- find posts by agents
            # whose persona is close to this agent's persona
            persona_result = self._storage._query(
                "SELECT persona_embedding FROM agent "
                "WHERE simulation_id = $sid AND agent_id = $aid LIMIT 1;",
                {"sid": simulation_id, "aid": agent_id},
            )
            persona_rows = self._storage._rows(persona_result)
            embedding = (
                persona_rows[0].get("persona_embedding", [])
                if persona_rows
                else []
            )

            if embedding and len(embedding) > 0:
                # Find similar agents
                similar_result = self._storage._query(
                    """
                    SELECT agent_id, name, vector::similarity::cosine(persona_embedding, $emb) AS score
                    FROM agent
                    WHERE simulation_id = $sid AND agent_id != $aid AND active = true
                    ORDER BY score DESC
                    LIMIT 5;
                    """,
                    {"sid": simulation_id, "aid": agent_id, "emb": embedding},
                )
                similar_agents = self._storage._rows(similar_result)
                similar_ids = [a.get("agent_id") for a in similar_agents if a.get("agent_id") is not None]

                if similar_ids:
                    # Get recent actions from similar agents
                    feed_result = self._storage._query(
                        """
                        SELECT *
                        FROM simulation_action
                        WHERE simulation_id = $sid
                          AND agent_id IN $aids
                          AND action_type IN ['CREATE_POST', 'CREATE_COMMENT', 'QUOTE_POST']
                        ORDER BY timestamp DESC
                        LIMIT $lim;
                        """,
                        {"sid": simulation_id, "aids": similar_ids, "lim": limit},
                    )
                    feed = self._storage._rows(feed_result)

            # Strategy 2: fallback to recent global content actions
            if not feed:
                fallback_result = self._storage._query(
                    """
                    SELECT *
                    FROM simulation_action
                    WHERE simulation_id = $sid
                      AND agent_id != $aid
                      AND action_type IN ['CREATE_POST', 'CREATE_COMMENT', 'QUOTE_POST']
                    ORDER BY timestamp DESC
                    LIMIT $lim;
                    """,
                    {"sid": simulation_id, "aid": agent_id, "lim": limit},
                )
                feed = self._storage._rows(fallback_result)

        except Exception as exc:
            logger.warning(
                "AVM: get_agent_feed failed (sim=%s, agent=%d): %s",
                simulation_id, agent_id, exc,
            )
        return feed
