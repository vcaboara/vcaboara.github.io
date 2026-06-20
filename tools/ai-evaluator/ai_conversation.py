#!/usr/bin/env python3
"""Multi-AI agent conversation system for evaluating and refining documents.

Supports two conversation modes:

  roundrobin (default)
    Agents take turns in sequence: A → B → C → A → B → C …
    Each agent sees the previous agent's response and builds on it.
    Best for iterative document refinement where each perspective adds
    friction and successive critique improves quality.

  vote
    Round 1: All agents respond independently in parallel (no anchoring).
    Rounds 2+: All agents receive the original prompt AND every response from
    the previous round, then synthesise in parallel — every agent evaluates
    every peer position before producing their own synthesis. There is no
    single judge; convergence is declared when all agents independently signal
    agreement. Best for strategic/factual questions where surfacing genuine
    disagreement matters before forcing consensus.

QUICK START
-----------
    # Two-agent round-robin (default behaviour, unchanged)
    python ai_conversation.py --prompt "your prompt"

    # Three-agent round-robin: Gemini optimist → GPT-4o skeptic → Claude synthesiser
    python ai_conversation.py --prompt brief.md --agents gemini,openai,anthropic

    # Three-agent vote (independent responses, then consensus)
    python ai_conversation.py --prompt question.md --agents gemini,openai,anthropic --mode vote

    # With knowledge base context
    python ai_conversation.py --prompt input.md --context ../../knowledge-base/ip-context

SETUP
-----
    1. Install dependencies:
       pip install -r ai_conversation_requirements.txt

    2. Create .env file with API keys:
       GEMINI_API_KEY=your-key-here       # FREE tier available
       OPENAI_API_KEY=your-key-here       # Optional
       ANTHROPIC_API_KEY=your-key-here    # Optional

    Set GEMINI_API_KEY, OPENAI_API_KEY, and/or ANTHROPIC_API_KEY in .env.
    Copy .env.example to .env to get started.

HOW IT WORKS — ROUND-ROBIN
---------------------------
    Agent roles (assigned in provider order):
      1. Technical Evaluator  — accuracy, innovation, patent risk
      2. Critical Reviewer    — adversarial skeptic, flags overclaims
      3. Strategic Analyst    — market, IP strategy, synthesis (3-agent only)

    Each agent receives the previous agent's full response and iterates.
    Convergence is detected when agreement phrases appear across consecutive
    responses. With 3 agents, all three must signal agreement before stopping.

HOW IT WORKS — VOTE
--------------------
    Round 1: All agents receive the original prompt simultaneously (independent).
    Round 2: A designated judge agent receives all Round 1 responses and
             produces a synthesised consensus document.
    Output: The judge's synthesis is the final document.

OUTPUT
------
    Results saved to output/ directory:
      - final_document_*.txt     Converged final document
      - transcript_*.txt         Full conversation between agents
      - conversation_*.json      Complete data log with metadata

CONFIGURATION
-------------
    --agents   Comma-separated provider list in role order.
               Valid values: gemini, openai, anthropic
               Default: auto-select two providers from available API keys
               Example: --agents gemini,openai,anthropic

    --mode     Conversation mode. Default: roundrobin
               roundrobin  — sequential critique loop
               vote        — independent responses then judge synthesis

    Model overrides (env vars or --model flag for primary agent):
      - GEMINI_MODEL    / --model  (primary agent only)
      - OPENAI_MODEL    (env var only)
      - ANTHROPIC_MODEL (env var only)

EXAMPLES
--------
    # Default two-agent run (auto-selects providers)
    python ai_conversation.py --prompt "Analyze patent US 19/424,106"

    # Three-agent round-robin (Gemini optimist, GPT-4o skeptic, Claude synthesiser)
    python ai_conversation.py --prompt brief.md --agents gemini,openai,anthropic --rounds 6

    # Three-agent vote on a strategic question
    python ai_conversation.py --prompt strategy.md --agents gemini,openai,anthropic --mode vote

    # With knowledge base context and custom output directory
    python ai_conversation.py \\
        --prompt brief.md \\
        --context ../../knowledge-base/ip-context \\
        --agents gemini,openai,anthropic \\
        --mode roundrobin \\
        --rounds 6 \\
        --output results/

REQUIREMENTS
------------
    - openai>=1.0.0
    - anthropic>=0.21.0
    - google-genai>=0.2.0
    - python-dotenv>=1.0.0

See ai_conversation_requirements.txt for complete list.
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load .env file if present
try:
    from dotenv import load_dotenv
    # Load .env from the script's directory for deterministic behavior
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    pass  # python-dotenv not installed, will use environment variables only

# Requires: pip install openai anthropic google-genai python-dotenv
try:
    from anthropic import Anthropic
    from google import genai
    from google.genai import types
    from openai import OpenAI
except ImportError:
    logger.error("Required packages not installed.")
    logger.error("Run: pip install -r ai_conversation_requirements.txt")
    sys.exit(1)

# Default model identifiers — override via env var (GEMINI_MODEL, OPENAI_MODEL,
# ANTHROPIC_MODEL), --model CLI flag, or by editing these constants.
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"


class AIAgent:
    """Represents an AI agent with a specific role and personality."""

    def __init__(self, name: str, provider: str, model: str,
                 system_prompt: str, api_key: str,
                 base_url: str | None = None):
        self.name = name
        self.provider = provider.lower()
        self.model = model
        self.system_prompt = system_prompt

        if self.provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=api_key)
        elif self.provider == "gemini":
            self.client = genai.Client(api_key=api_key)
            self.model_name = model
        elif self.provider == "ollama":
            self.client = OpenAI(
                base_url=(base_url or DEFAULT_OLLAMA_BASE_URL),
                api_key=(api_key or "ollama")
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def respond(self, message: str) -> str:
        """Generate a response to the given message."""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text

            elif self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        temperature=0.7,
                        max_output_tokens=2000
                    )
                )
                return response.text

            elif self.provider == "ollama":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            else:
                raise ValueError(
                    f"Unsupported provider in respond(): {self.provider}")

        except Exception as e:
            return f"Error generating response: {str(e)}"


class ConversationManager:
    """Manages a round-robin conversation between two or more AI agents.

    Agents take turns in sequence: A → B → C → A → B → C …
    Each agent sees the previous agent's full response before replying.
    Convergence is detected when agreement phrases appear across consecutive
    responses from the last two speakers.

    With 3+ agents the minimum number of rounds before convergence can be
    detected is n+1 (one full cycle plus one), preventing premature agreement
    between the first two agents before the third has had a chance to object.
    """

    def __init__(self, agents: list, initial_prompt: str,
                 max_rounds: int = 10, round_delay: int = 15):
        if len(agents) < 2:
            raise ValueError(
                "ConversationManager requires at least 2 agents."
            )
        self.agents = agents
        # Preserve legacy attributes for backward compatibility
        self.agent1 = agents[0]
        self.agent2 = agents[1]
        self.initial_prompt = initial_prompt
        self.max_rounds = max_rounds
        self.round_delay = round_delay
        self.conversation_history: list[dict] = []

    def check_convergence(self, response1: str, response2: str) -> bool:
        """Check whether two consecutive responses signal mutual agreement.

        Requires at least 2 agreement phrases to avoid premature convergence
        on incidental phrasing.
        """
        r1 = response1.lower()
        r2 = response2.lower()

        agreement_phrases = [
            "i agree", "agreed", "looks good", "that works",
            "perfect", "approved", "accepted", "final version",
            "no changes needed", "we have consensus",
        ]

        agreement_count = sum(
            1 for phrase in agreement_phrases
            if phrase in r1 or phrase in r2
        )

        return agreement_count >= 2

    def run_conversation(self) -> dict:
        """Run the round-robin conversation loop.

        Returns a result dict with keys:
          mode ('roundrobin'), converged (bool), rounds (int),
          final_document (str), conversation_history (list[dict])
        """
        agent_names = " → ".join(a.name for a in self.agents)
        logger.info("=" * 80)
        logger.info(f"Starting round-robin: {agent_names}")
        logger.info("=" * 80)

        current_message = self.initial_prompt
        converged = False
        round_num = 0
        n = len(self.agents)

        while round_num < self.max_rounds and not converged:
            round_num += 1
            current_agent = self.agents[(round_num - 1) % n]

            logger.info(f"--- Round {round_num} ---")
            logger.info(f"{current_agent.name} is responding...")

            response = current_agent.respond(current_message)

            self.conversation_history.append({
                "round": round_num,
                "speaker": current_agent.name,
                "message": response,
                "timestamp": datetime.now().isoformat(),
            })

            logger.info(f"{current_agent.name}: {response[:200]}...")
            if len(response) > 200:
                logger.info(f"  ... ({len(response)} characters total)")

            # Require at least one full cycle (n rounds) before checking
            # convergence so every agent has contributed at least once.
            if round_num > n:
                prev_response = self.conversation_history[-2]["message"]
                if self.check_convergence(prev_response, response):
                    converged = True
                    logger.info(
                        f"✓ Convergence detected after {round_num} rounds!"
                    )
                    break

            current_message = (
                f"Here is the current version from {current_agent.name}:\n\n"
                f"{response}\n\nPlease review, provide feedback, and suggest "
                f"improvements or confirm if this is ready."
            )

            if self.round_delay > 0:
                logger.info(
                    f"Waiting {self.round_delay}s before next round..."
                )
                time.sleep(self.round_delay)

        if not converged:
            logger.warning(
                f"Reached maximum rounds ({self.max_rounds}) without "
                f"full convergence."
            )

        final_document = (
            self.conversation_history[-1]["message"]
            if self.conversation_history else ""
        )

        return {
            "mode": "roundrobin",
            "converged": converged,
            "rounds": round_num,
            "final_document": final_document,
            "conversation_history": self.conversation_history,
        }

    def save_results(self, results: dict, output_dir: str = "ai_conversations"):
        """Save conversation results to timestamped files in output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        log_file = os.path.join(output_dir, f"conversation_{timestamp}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Conversation log saved to: {log_file}")

        doc_file = os.path.join(
            output_dir, f"final_document_{timestamp}.txt"
        )
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(results["final_document"])
        logger.info(f"✓ Final document saved to: {doc_file}")

        transcript_file = os.path.join(
            output_dir, f"transcript_{timestamp}.txt"
        )
        agent_names = " and ".join(a.name for a in self.agents)
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(f"Conversation between {agent_names}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("Mode: roundrobin\n")
            f.write(f"Rounds: {results['rounds']}\n")
            f.write(f"Converged: {results['converged']}\n")
            f.write("=" * 80 + "\n\n")

            for entry in self.conversation_history:
                f.write(f"Round {entry['round']} - {entry['speaker']}:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{entry['message']}\n\n")

        logger.info(f"✓ Transcript saved to: {transcript_file}")


class VoteConversationManager:
    """Manages a vote-mode conversation between two or more AI agents.

    All agents respond independently to the original prompt (Round 1),
    preventing anchoring from earlier responses. A designated judge agent
    (the last agent in the list) then reads all independent responses and
    synthesises a consensus document (Round 2).

    Best for strategic or factual questions where you want to surface genuine
    disagreement before forcing convergence. The judge explicitly notes where
    agents disagreed and explains the tiebreak logic.
    """

    def __init__(self, agents: list, initial_prompt: str,
                 max_rounds: int = 10):
        if len(agents) < 2:
            raise ValueError(
                "VoteConversationManager requires at least 2 agents."
            )
        self.agents = agents
        self.initial_prompt = initial_prompt
        self.max_rounds = max_rounds
        self.conversation_history: list[dict] = []

    def run_conversation(self) -> dict:
        """Run fully-parallel iterative vote rounds.

        Every round all agents respond in parallel.  From Round 2 onward each
        agent receives the original prompt PLUS every response from the
        previous round so they can evaluate *all* perspectives before
        synthesising.  There is no single judge — every agent is an equal
        evaluator in every round.

        Convergence is declared when all agents in a round include at least
        one agreement phrase, meaning they have each independently signalled
        satisfaction with the current synthesis.  The final document is the
        last agent's response from the converging round (conventionally the
        Strategic Analyst / most synthesis-oriented role).

        Returns a result dict with keys:
          mode ('vote'), converged (bool), rounds (int),
          final_document (str), conversation_history (list[dict])
        """
        agent_names = ", ".join(a.name for a in self.agents)
        logger.info("=" * 80)
        logger.info(f"Starting vote mode with agents: {agent_names}")
        logger.info("=" * 80)

        agreement_phrases = [
            "i agree", "agreed", "looks good", "that works",
            "perfect", "approved", "accepted", "final version",
            "no changes needed", "we have consensus",
        ]

        def _has_agreement(text: str) -> bool:
            t = text.lower()
            return any(p in t for p in agreement_phrases)

        def _parallel_round(
            round_num: int,
            prompts: dict,  # {agent.name: prompt_text}
            phase: str,
        ) -> list[dict]:
            """Dispatch one parallel round; returns ordered list of entries."""

            def _call(agent: AIAgent) -> tuple:
                logger.info(
                    f"[Round {round_num}] {agent.name} is responding..."
                )
                response = agent.respond(prompts[agent.name])
                return agent, response, datetime.now().isoformat()

            with ThreadPoolExecutor(
                max_workers=len(self.agents),
                thread_name_prefix=f"vote-r{round_num}",
            ) as executor:
                futures = {
                    executor.submit(_call, agent): agent.name
                    for agent in self.agents
                }
                raw: dict[str, tuple] = {}
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        raw[name] = future.result()
                    except Exception as exc:
                        logger.error(f"{name} raised: {exc}")
                        raw[name] = (
                            next(
                                a for a in self.agents if a.name == name
                            ),
                            f"Error generating response: {exc}",
                            datetime.now().isoformat(),
                        )

            entries = []
            for agent in self.agents:
                _, response, ts = raw[agent.name]
                entry = {
                    "round": round_num,
                    "speaker": agent.name,
                    "message": response,
                    "timestamp": ts,
                    "phase": phase,
                }
                self.conversation_history.append(entry)
                entries.append(entry)
                logger.info(f"{agent.name}: {response[:200]}...")
                if len(response) > 200:
                    logger.info(f"  ... ({len(response)} characters total)")
            return entries

        converged = False
        round_num = 0
        prev_entries: list[dict] = []

        while round_num < self.max_rounds and not converged:
            round_num += 1

            if round_num == 1:
                # Round 1: every agent answers the original prompt cold.
                logger.info(
                    f"--- Round 1: Parallel independent responses "
                    f"({len(self.agents)} agents) ---"
                )
                prompts = {
                    agent.name: self.initial_prompt
                    for agent in self.agents
                }
                phase = "independent"
            else:
                # Rounds 2+: every agent receives the original prompt PLUS
                # all responses from the previous round so they can evaluate
                # every peer's position before synthesising.
                logger.info(
                    f"--- Round {round_num}: Parallel synthesis "
                    f"(all agents see all Round {round_num - 1} responses) ---"
                )
                prev_text = "\n\n".join(
                    f"=== {e['speaker']} (Round {round_num - 1}) ===\n"
                    f"{e['message']}"
                    for e in prev_entries
                )
                synthesis_prompt = (
                    f"ORIGINAL PROMPT:\n{self.initial_prompt}\n\n"
                    f"RESPONSES FROM ROUND {round_num - 1} (all agents):\n"
                    f"{prev_text}\n\n"
                    f"Review the above responses. Identify where agents "
                    f"agreed and where they diverged. Then produce your own "
                    f"synthesised answer that incorporates the strongest "
                    f"elements. If you are satisfied that the synthesis is "
                    f"complete and accurate, state your approval explicitly."
                )
                prompts = {
                    agent.name: synthesis_prompt for agent in self.agents
                }
                phase = "synthesis"

            current_entries = _parallel_round(round_num, prompts, phase)
            prev_entries = current_entries

            # Convergence: every agent must signal agreement
            if round_num > 1:
                all_agree = all(
                    _has_agreement(e["message"]) for e in current_entries
                )
                if all_agree:
                    converged = True
                    logger.info(
                        f"✓ All agents converged after {round_num} rounds!"
                    )

        if not converged:
            logger.warning(
                f"Reached maximum rounds ({self.max_rounds}) without "
                f"full convergence."
            )

        logger.info("✓ Vote complete.")

        # Final document: last agent's response from the final round
        # (conventionally Strategic Analyst — the synthesis-oriented role).
        final_document = prev_entries[-1]["message"] if prev_entries else ""

        return {
            "mode": "vote",
            "converged": converged,
            "rounds": round_num,
            "final_document": final_document,
            "conversation_history": self.conversation_history,
        }

    def save_results(self, results: dict, output_dir: str = "ai_conversations"):
        """Save vote results to timestamped files in output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        log_file = os.path.join(output_dir, f"conversation_{timestamp}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Conversation log saved to: {log_file}")

        doc_file = os.path.join(
            output_dir, f"final_document_{timestamp}.txt"
        )
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(results["final_document"])
        logger.info(f"✓ Final document saved to: {doc_file}")

        transcript_file = os.path.join(
            output_dir, f"transcript_{timestamp}.txt"
        )
        agent_names = ", ".join(a.name for a in self.agents)
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(f"Vote conversation — agents: {agent_names}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("Mode: vote\n")
            f.write("=" * 80 + "\n\n")

            for entry in self.conversation_history:
                phase = entry.get("phase", "")
                f.write(
                    f"Round {entry['round']} - {entry['speaker']}"
                    f"{' [' + phase + ']' if phase else ''}:\n"
                )
                f.write("-" * 80 + "\n")
                f.write(f"{entry['message']}\n\n")

        logger.info(f"✓ Transcript saved to: {transcript_file}")


def main():
    """Main entry point for the AI conversation script."""

    description = "AI Conversation Agent - Multi-Agent Iterative Refinement"

    epilog = """
SETUP:
  1. Install dependencies:
     pip install -r ai_conversation_requirements.txt

  2. Set API keys in .env:
     OPENAI_API_KEY=your-key      # https://platform.openai.com/api-keys
     GEMINI_API_KEY=your-key      # https://aistudio.google.com/app/apikey
     ANTHROPIC_API_KEY=your-key   # https://console.anthropic.com/
      OLLAMA_MODEL=llama3.1:8b     # Optional (local Ollama)
      OLLAMA_BASE_URL=http://localhost:11434/v1

EXAMPLES:
  # Two-agent run (auto-selects providers, unchanged default):
  python ai_conversation.py --prompt brief.md

  # Three-agent round-robin (Gemini → GPT-4o → Claude → repeat):
  python ai_conversation.py --prompt brief.md --agents gemini,openai,anthropic

    # Local-first run with Ollama + cloud providers:
    python ai_conversation.py --prompt brief.md --agents ollama,openai,anthropic

  # Three-agent vote (independent responses, then Claude synthesises):
  python ai_conversation.py --prompt question.md --agents gemini,openai,anthropic --mode vote

  # With knowledge-base context and custom output dir:
  python ai_conversation.py \\
      --prompt brief.md \\
      --context knowledge-base/ip-context \\
      --agents gemini,openai,anthropic \\
      --rounds 6 \\
      --output results/

MODES:
  roundrobin (default)  Each agent critiques the previous; best for documents.
  vote                  Independent responses + judge synthesis; best for Q&A.

SUPPORTED MODELS:
  OpenAI:    gpt-4o, gpt-4-turbo, gpt-3.5-turbo
  Gemini:    gemini-3-flash-preview, gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash
  Anthropic: claude-opus-4-5, claude-3-5-sonnet-20241022
    Ollama:    any local tag (e.g. llama3.1:8b, qwen2.5:14b, mistral:7b)
"""

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--prompt', '-p',
        metavar='TEXT_OR_FILE',
        help='Initial prompt text, or path to .txt/.md file. If omitted, '
             'uses default template (with warning).'
    )
    parser.add_argument(
        '--rounds', '-r',
        type=int,
        default=5,
        metavar='N',
        help='Maximum conversation rounds before stopping (default: 5). '
             'Conversation may end earlier if agents converge.'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        metavar='DIR',
        help='Output directory for conversation results (default: output/). '
             'Creates timestamped .json, .txt files for logs, transcripts, '
             'and final documents.'
    )
    parser.add_argument(
        '--context', '-c',
        metavar='DIR',
        help='Path to knowledge base directory containing .md files with '
             'persistent context (e.g., knowledge-base/ip-context). Content '
             'is loaded into both agents\' system prompts for consistent '
             'reference across conversations.'
    )
    parser.add_argument(
        '--model',
        metavar='MODEL_ID',
        help='Override the default model for the primary agent (Agent 1) only. '
             'The model ID must match the provider that is auto-selected for '
             'Agent 1 (Gemini > OpenAI > Anthropic based on available API keys). '
             'Examples: gemini-2.0-flash-exp, gpt-4o, claude-3-5-sonnet-20241022. '
             'Use the GEMINI_MODEL / OPENAI_MODEL / ANTHROPIC_MODEL env vars to '
             'override individual provider models without this restriction.'
    )
    parser.add_argument(
        '--agents', '-a',
        metavar='PROVIDER_LIST',
        default=None,
        help='Ordered, comma-separated list of providers to use as agents. '
             'Valid values: gemini, openai, anthropic, ollama. '
             'Determines agent role order: first = Technical Evaluator, '
             'second = Critical Reviewer, third = Strategic Analyst. '
             'Example: --agents gemini,openai,anthropic. '
             'When omitted, auto-selects two providers from available API keys '
             '(legacy default behaviour).'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['roundrobin', 'vote'],
        default='roundrobin',
        help='Conversation mode (default: roundrobin). '
             'roundrobin: agents critique each other sequentially — best for '
             'iterative document refinement. '
             'vote: all agents respond independently then a judge (last agent) '
             'synthesises — best for strategic or factual questions.'
    )
    parser.add_argument(
        '--delay', '-d',
        type=int,
        default=15,
        metavar='SECONDS',
        help='Seconds to wait between rounds (default: 15). '
             'Increase to reduce 503/rate-limit errors from Gemini.'
    )
    args = parser.parse_args()

    # API keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "ollama")
    OLLAMA_BASE_URL = os.environ.get(
        "OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL

    # Model defaults: env var overrides the built-in constant.
    # --model is applied only to the provider that is actually selected
    # (after provider selection below) to avoid sending e.g. a Gemini model
    # ID to the OpenAI client.
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
    ANTHROPIC_MODEL = os.environ.get(
        "ANTHROPIC_MODEL") or DEFAULT_ANTHROPIC_MODEL
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL

    # Load knowledge base context if specified
    kb_context = ""
    if args.context:
        kb_dir = Path(args.context)
        if kb_dir.exists():
            logger.info(f"Loading knowledge base from: {kb_dir}")
            kb_files = list(kb_dir.glob("*.md"))
            if kb_files:
                kb_content = []
                for md_file in kb_files:
                    with open(md_file, encoding='utf-8') as f:
                        kb_content.append(
                            f"## {md_file.stem.replace('-', ' ').title()}"
                            f"\n\n{f.read()}\n"
                        )

                kb_context = f"""

---

# PERSISTENT IP & BUSINESS CONTEXT

You have access to pre-loaded knowledge base context. Reference this freely:  # noqa: E501

{''.join(kb_content)}

---

Integrate this knowledge naturally when relevant.

"""
                total_chars = sum(len(c) for c in kb_content)
                logger.info(
                    f"✓ Loaded {len(kb_files)} context files "
                    f"({total_chars} characters)"
                )
            else:
                logger.warning(f"No .md files found in {kb_dir}")
        else:
            logger.warning(f"Knowledge base directory not found: {kb_dir}")

    # Define the available provider configs keyed by provider name
    available_keys = {
        "gemini": GEMINI_API_KEY,
        "openai": OPENAI_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
        "ollama": OLLAMA_API_KEY,
    }
    available_models = {
        "gemini": GEMINI_MODEL,
        "openai": OPENAI_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "ollama": OLLAMA_MODEL,
    }
    available_base_urls = {
        "ollama": OLLAMA_BASE_URL,
    }
    requires_api_key = {
        "gemini": True,
        "openai": True,
        "anthropic": True,
        "ollama": False,
    }

    # Agent role names and system prompts for up to 3 agents.
    # Roles are assigned positionally from the ordered provider list.
    ROLE_NAMES = ["Technical Evaluator",
                  "Critical Reviewer", "Strategic Analyst"]
    ROLE_PROMPTS = [
        # Role 0 — Technical Evaluator
        (
            "You are a technical evaluator specializing in intellectual "
            "property and technology assessment. Your role is to analyze "
            "content for technical accuracy, innovation potential, "
            "patentability, prior art concerns, and commercial viability. "
            "Provide detailed technical critique and identify strengths, "
            "weaknesses, and areas needing clarification. When you believe "
            "the content is comprehensive and technically sound, clearly "
            "state your approval."
        ),
        # Role 1 — Critical Reviewer (adversarial skeptic)
        (
            "You are a critical reviewer and adversarial skeptic. Your role "
            "is to challenge every claim, surface hidden assumptions, flag "
            "overclaims or unsupported assertions, and identify logical gaps "
            "or risks the other agents may have missed. Do not accept "
            "premises at face value. Push back hard on anything that lacks "
            "evidence or rigour. When — and only when — you are satisfied "
            "that all your concerns have been addressed, explicitly state "
            "your approval."
        ),
        # Role 2 — Strategic Analyst
        (
            "You are a strategic analyst focused on IP strategy, market "
            "positioning, and business value. Your role is to evaluate "
            "content for market opportunity, competitive advantage, strategic "
            "alignment, and implementation feasibility. Ensure the content "
            "clearly articulates its value proposition and differentiation. "
            "When the content meets strategic requirements, explicitly "
            "confirm your approval."
        ),
    ]

    def _build_config(provider: str) -> dict:
        """Return provider config dict, applying --model override to agent 0."""
        model = available_models[provider]
        config = {
            "provider": provider,
            "model": model,
            "api_key": available_keys[provider],
        }
        if provider in available_base_urls:
            config["base_url"] = available_base_urls[provider]
        return config

    # --- Determine ordered provider list ---
    if args.agents:
        # Explicit --agents flag: validate and use as-is
        requested = [
            p.strip().lower() for p in args.agents.split(",") if p.strip()
        ]
        valid_providers = {"gemini", "openai", "anthropic", "ollama"}
        unknown = [p for p in requested if p not in valid_providers]
        if unknown:
            logger.error(f"Unknown provider(s): {', '.join(unknown)}")
            logger.error(
                f"Valid choices: {', '.join(sorted(valid_providers))}")
            sys.exit(1)
        missing_keys = [
            p for p in requested
            if requires_api_key[p] and not available_keys[p]
        ]
        if missing_keys:
            logger.error(
                f"No API key configured for: {', '.join(missing_keys)}. "
                f"Set the corresponding key in your .env file."
            )
            sys.exit(1)
        ordered_providers = requested
    else:
        # Auto-select two diverse providers (legacy default behaviour)
        if GEMINI_API_KEY:
            p1 = "gemini"
        elif OPENAI_API_KEY:
            p1 = "openai"
        elif ANTHROPIC_API_KEY:
            p1 = "anthropic"
        else:
            p1 = "ollama"
            logger.warning(
                "No cloud API keys configured; using local Ollama provider."
            )

        if p1 != "anthropic" and ANTHROPIC_API_KEY:
            p2 = "anthropic"
        elif p1 != "openai" and OPENAI_API_KEY:
            p2 = "openai"
        elif p1 != "gemini" and GEMINI_API_KEY:
            p2 = "gemini"
        elif p1 != "ollama":
            p2 = "ollama"
        else:
            p2 = p1
            logger.warning(
                f"Using {p1} for both agents (configure additional API keys "
                f"for provider diversity)."
            )
        ordered_providers = [p1, p2]

    # --- Build AIAgent objects ---
    agents: list[AIAgent] = []
    for idx, provider in enumerate(ordered_providers):
        cfg = _build_config(provider)
        # Apply --model override to the primary (first) agent only
        if idx == 0 and args.model:
            cfg["model"] = args.model
        # Wrap roles beyond the defined list back to the last defined role
        role_idx = min(idx, len(ROLE_NAMES) - 1)
        role_name = ROLE_NAMES[role_idx]
        # Disambiguate names when the same role repeats (>3 agents)
        if idx >= len(ROLE_NAMES):
            role_name = f"{role_name} {idx + 1}"
        agent = AIAgent(
            name=role_name,
            system_prompt=ROLE_PROMPTS[role_idx] + kb_context,
            **cfg,
        )
        agents.append(agent)
        logger.info(
            f"Agent {idx + 1}: {role_name} ({provider} / {cfg['model']})"
        )

    # Get initial prompt from CLI arg, file, or fall back to default template
    initial_topic = None

    if args.prompt:
        prompt_path = Path(args.prompt)
        if prompt_path.exists() and prompt_path.suffix in ['.txt', '.md']:
            logger.info(f"Loading prompt from file: {prompt_path}")
            with open(prompt_path, encoding='utf-8') as f:
                initial_topic = f.read()
        else:
            initial_topic = args.prompt

    if not initial_topic:
        initial_topic = """
Please evaluate and refine the following technology brief:

[TECHNOLOGY BRIEF]
Title: [Your invention title]

Problem Statement:
[Describe the problem your invention solves]

Technical Solution:
[Describe your technical approach and innovation]

Key Features:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Technical Advantages:
- [Advantage 1]
- [Advantage 2]

Potential Applications:
- [Application 1]
- [Application 2]

Please review this brief for technical accuracy, completeness, patentability,
and business value. Identify gaps, suggest improvements, and help refine it into a
comprehensive document ready for IP protection.
"""
        logger.warning("Using default template prompt.")
        logger.info("For better results, provide your tech brief:")
        logger.info("  python ai_conversation.py --prompt 'your prompt here'")
        logger.info(
            "  python ai_conversation.py --prompt path/to/your_brief.md"
        )

    # --- Instantiate the appropriate manager and run ---
    if args.mode == "vote":
        manager: VoteConversationManager | ConversationManager = (
            VoteConversationManager(
                agents=agents,
                initial_prompt=initial_topic,
                max_rounds=args.rounds,
            )
        )
    else:
        manager = ConversationManager(
            agents=agents,
            initial_prompt=initial_topic,
            max_rounds=args.rounds,
            round_delay=args.delay,
        )

    results = manager.run_conversation()
    manager.save_results(results, output_dir=args.output)

    logger.info("=" * 80)
    logger.info("Conversation complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
