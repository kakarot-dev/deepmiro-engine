# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 kakarot-dev
#
# Dual-model routing: Regular LLM for bulk calls, Boost LLM for quality-sensitive calls.
# Inspired by MiroFish's LLM_BOOST_* config and MiroShark's smart model routing.

"""
Boost LLM Patch

Routes LLM calls to two different models:
- Regular (LLM_MODEL_NAME): cheap/fast model for agent actions, config, ontology
- Boost (LLM_BOOST_MODEL_NAME): better model for reports, profiles, complex generation

The patch wraps MiroFish's LLMClient to check which module is calling it
and routes to the appropriate model.
"""

import os
import logging
import inspect

logger = logging.getLogger("mirofish.boost_patch")

# Modules that should use the boost model
BOOST_MODULES = {
    "app.services.report_agent",
    "app.services.oasis_profile_generator",
}


def apply_boost_patch():
    """Patch LLMClient to route calls to regular or boost model based on caller."""
    boost_api_key = os.environ.get("LLM_BOOST_API_KEY", "")
    boost_base_url = os.environ.get("LLM_BOOST_BASE_URL", "")
    boost_model = os.environ.get("LLM_BOOST_MODEL_NAME", "")

    if not boost_api_key or not boost_model:
        logger.info("No boost LLM configured, skipping boost patch")
        return

    regular_model = os.environ.get("LLM_MODEL_NAME", "")
    logger.info(f"Boost patch: regular={regular_model}, boost={boost_model}")

    try:
        from app.utils.llm_client import LLMClient
        from openai import OpenAI

        # Create a separate OpenAI client for the boost model
        boost_client = OpenAI(
            api_key=boost_api_key,
            base_url=boost_base_url or os.environ.get("LLM_BASE_URL", ""),
        )

        original_chat = LLMClient.chat

        def patched_chat(self, messages, **kwargs):
            # Check caller stack — look through multiple frames since
            # monkey-patches add wrapper layers between caller and us
            use_boost = False
            for frame_info in inspect.stack()[1:6]:
                caller_module = frame_info.frame.f_globals.get("__name__", "")
                if any(caller_module.startswith(m) for m in BOOST_MODULES):
                    use_boost = True
                    break

            if use_boost:
                # Swap to boost model for this call
                original_model = self.model
                original_client = self.client
                self.model = boost_model
                self.client = boost_client
                try:
                    result = original_chat(self, messages, **kwargs)
                    return result
                finally:
                    self.model = original_model
                    self.client = original_client
            else:
                return original_chat(self, messages, **kwargs)

        LLMClient.chat = patched_chat
        logger.info("LLMClient patched: dual-model routing active")

    except ImportError:
        logger.warning("Could not apply boost patch — app.utils.llm_client not found")
