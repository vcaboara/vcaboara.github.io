"""Context loader for AI conversations with knowledge base."""
import importlib.util
import logging
import os
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def _find_ai_conversation_path() -> Path:
    """Locate tools/ai-evaluator/ai_conversation.py from this file upward."""
    start_path = Path(__file__).resolve()
    for parent in start_path.parents:
        candidate = parent / "tools" / "ai-evaluator" / "ai_conversation.py"
        if candidate.exists():
            return candidate

    raise ImportError(
        "AIAgent module not found in any parent tools/ai-evaluator directory. "
        f"Search started from: {start_path}"
    )


def _load_ai_agent_class():
    """Load AIAgent from tools/ai-evaluator/ai_conversation.py."""
    module_path = _find_ai_conversation_path()

    spec = importlib.util.spec_from_file_location(
        "tools_ai_evaluator_ai_conversation", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not create a module spec for AIAgent from {module_path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AIAgent


class KnowledgeBase:
    """Load and manage persistent IP context for AI conversations."""

    def __init__(self, context_dir: str = "knowledge-base/ip-context"):
        self.context_dir = Path(context_dir)
        self.contexts = {}

    def load_all(self) -> Dict[str, str]:
        """Load all markdown files from context directory."""
        if not self.context_dir.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {self.context_dir}")

        for md_file in self.context_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                self.contexts[md_file.stem] = f.read()

        return self.contexts

    def get_context(self, name: str) -> str:
        """Get specific context by name."""
        if name not in self.contexts:
            self.load_all()
        return self.contexts.get(name, "")

    def build_system_prompt(self, base_prompt: str, include: List[str] = None) -> str:
        """Build enhanced system prompt with knowledge base context.

        Args:
            base_prompt: Original system prompt for the agent
            include: List of context names to include (None = all)

        Returns:
            Enhanced system prompt with IP context
        """
        if not self.contexts:
            self.load_all()

        context_sections = []

        # Determine which contexts to include
        if include is None:
            include = list(self.contexts.keys())

        for name in include:
            if name in self.contexts:
                context_sections.append(
                    f"## Knowledge Base: {name.replace('-', ' ').title()}\n\n{self.contexts[name]}\n")

        if not context_sections:
            return base_prompt

        # Build enhanced prompt
        enhanced = f"""{base_prompt}

---

# PERSISTENT IP & BUSINESS CONTEXT

You have access to the following pre-loaded knowledge base. Reference this information without requiring the user to re-explain:

{''.join(context_sections)}

---

When answering queries, integrate this knowledge base context naturally. You understand:
- The Arboreum technology (US 19/424,106)
- The AIF impact model (85% profit donation)
- Current strategic positioning and challenges
- Recent strategic consensus and recommendations

Refer to this context when relevant, and ask clarifying questions to build upon it rather than requesting basic re-explanations.
"""
        return enhanced

    def append_to_context(self, note: str, filename: str = "context.md"):
        """Append a note to the context file.

        Args:
            note: The note to append (should include date/topic header)
            filename: Context file to append to (default: context.md)
        """
        filepath = self.context_dir / filename

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"\n{note}\n")

        # Reload contexts
        self.contexts[filepath.stem] = (
            self.context_dir / filename).read_text(encoding='utf-8')

        logger.info(f"Appended to {filename}")


def create_context_aware_agent(name: str, provider: str, model: str,
                               base_system_prompt: str, api_key: str,
                               knowledge_base: KnowledgeBase = None,
                               include_contexts: List[str] = None):
    """Factory function to create an AIAgent with knowledge base context.

    Args:
        name, provider, model, base_system_prompt, api_key: Standard AIAgent params
        knowledge_base: KnowledgeBase instance (creates new if None)
        include_contexts: Which knowledge base files to include (None = all)

    Returns:
        AIAgent with enhanced system prompt
    """
    AIAgent = _load_ai_agent_class()

    if knowledge_base is None:
        knowledge_base = KnowledgeBase()

    # Build enhanced system prompt with knowledge base
    enhanced_prompt = knowledge_base.build_system_prompt(
        base_system_prompt,
        include=include_contexts
    )

    return AIAgent(
        name=name,
        provider=provider,
        model=model,
        system_prompt=enhanced_prompt,
        api_key=api_key
    )


if __name__ == "__main__":
    # Test knowledge base loading
    kb = KnowledgeBase()
    kb.load_all()

    logger.info("Loaded contexts:")
    for name, content in kb.contexts.items():
        logger.info(f"  - {name}: {len(content)} characters")

    logger.info("\nKnowledge base system ready")
