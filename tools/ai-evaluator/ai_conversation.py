#!/usr/bin/env python3
"""
Script to facilitate a conversation between two AI agents until they converge
on a final document.
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

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
    from openai import OpenAI
    from anthropic import Anthropic
    from google import genai
    from google.genai import types
except ImportError:
    logger.error("Required packages not installed.")
    logger.error("Run: pip install -r ai_conversation_requirements.txt")
    sys.exit(1)


class AIAgent:
    """Represents an AI agent with a specific role and personality."""

    def __init__(self, name: str, provider: str, model: str,
                 system_prompt: str, api_key: str):
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
            else:
                raise ValueError(f"Unsupported provider in respond(): {self.provider}")

        except Exception as e:
            return f"Error generating response: {str(e)}"


class ConversationManager:
    """Manages the conversation between two AI agents."""

    def __init__(self, agent1: AIAgent, agent2: AIAgent,
                 initial_prompt: str, max_rounds: int = 10,
                 convergence_threshold: float = 0.85):
        self.agent1 = agent1
        self.agent2 = agent2
        self.initial_prompt = initial_prompt
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold
        self.conversation_history: List[Dict] = []

    def check_convergence(self, response1: str, response2: str) -> bool:
        """
        Check if the two responses have converged (are similar enough).
        Uses agreement phrase detection only to avoid premature convergence
        based on length similarity alone.
        """
        response1_lower = response1.lower()
        response2_lower = response2.lower()

        # Check for explicit agreement
        agreement_phrases = [
            "i agree", "agreed", "looks good", "that works",
            "perfect", "approved", "accepted", "final version",
            "no changes needed", "we have consensus"
        ]

        agreement_count = sum(
            1 for phrase in agreement_phrases
            if phrase in response1_lower or phrase in response2_lower
        )

        # Require strong agreement signal (at least 2 agreement phrases)
        # Removed length-ratio heuristic to prevent premature convergence
        return agreement_count >= 2

    def run_conversation(self) -> Dict:
        """Run the conversation loop between the two agents."""
        logger.info("="*80)
        logger.info(
            f"Starting conversation between {self.agent1.name} and "
            f"{self.agent2.name}")
        logger.info("="*80)

        current_message = self.initial_prompt
        current_speaker = self.agent1
        other_speaker = self.agent2

        converged = False
        round_num = 0

        while round_num < self.max_rounds and not converged:
            round_num += 1
            logger.info(f"--- Round {round_num} ---")
            logger.info(f"{current_speaker.name} is responding...")

            # Get response from current speaker
            response = current_speaker.respond(current_message)

            # Log the exchange
            self.conversation_history.append({
                "round": round_num,
                "speaker": current_speaker.name,
                "message": response,
                "timestamp": datetime.now().isoformat()
            })

            logger.info(f"{current_speaker.name}: {response[:200]}...")
            if len(response) > 200:
                logger.info(f"  ... ({len(response)} characters total)")

            # Check for convergence if we have at least 2 rounds
            if round_num >= 2:
                prev_response = self.conversation_history[-2]["message"]
                if self.check_convergence(prev_response, response):
                    converged = True
                    logger.info(
                        f"✓ Convergence detected after {round_num} rounds!")
                    break

            # Prepare next message and swap speakers
            current_message = (
                f"Here is the current version from {current_speaker.name}:\n\n"
                f"{response}\n\nPlease review, provide feedback, and suggest "
                f"improvements or confirm if this is ready."
            )
            current_speaker, other_speaker = other_speaker, current_speaker

            # Small delay to avoid rate limits
            time.sleep(1)

        if not converged:
            logger.warning(
                f"Reached maximum rounds ({self.max_rounds}) without full "
                f"convergence.")

        # Extract final document (last response)
        final_document = (
            self.conversation_history[-1]["message"]
            if self.conversation_history else ""
        )

        return {
            "converged": converged,
            "rounds": round_num,
            "final_document": final_document,
            "conversation_history": self.conversation_history
        }

    def save_results(self, results: Dict, output_dir: str = "ai_conversations"):
        """Save the conversation results to files."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save full conversation log
        log_file = os.path.join(output_dir, f"conversation_{timestamp}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Conversation log saved to: {log_file}")

        # Save final document
        doc_file = os.path.join(
            output_dir, f"final_document_{timestamp}.txt"
        )
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(results["final_document"])
        logger.info(f"✓ Final document saved to: {doc_file}")

        # Save readable transcript
        transcript_file = os.path.join(
            output_dir, f"transcript_{timestamp}.txt"
        )
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(
                f"Conversation between {self.agent1.name} and "
                f"{self.agent2.name}\n"
            )
            f.write(
                f"Started: {self.conversation_history[0]['timestamp']}\n"
            )
            f.write(f"Rounds: {results['rounds']}\n")
            f.write(f"Converged: {results['converged']}\n")
            f.write("="*80 + "\n\n")

            for entry in self.conversation_history:
                f.write(f"Round {entry['round']} - {entry['speaker']}:\n")
                f.write("-"*80 + "\n")
                f.write(f"{entry['message']}\n\n")

        logger.info(f"✓ Transcript saved to: {transcript_file}")


def main():
    """Main entry point for the AI conversation script."""

    # Parse command line arguments
    description = """
AI Conversation Agent - Iterative Multi-Agent Refinement System

Two AI agents (Technical Evaluator and Strategic Analyst) converse and iterate
on content until they reach consensus. Supports OpenAI, Google Gemini, and
Anthropic Claude with automatic multi-provider diversity.

The system automatically selects different AI providers when multiple API keys
are configured to ensure diverse perspectives. Agent 1 (Technical Evaluator)
analyzes technical accuracy, innovation, and patentability. Agent 2 (Strategic
Analyst) evaluates market opportunity, IP strategy, and business value.
"""

    epilog = """
SETUP:
  1. Install dependencies:
     pip install -r ai_conversation_requirements.txt

  2. Set at least one API key (in .env file or environment):
     OPENAI_API_KEY=your-key      # https://platform.openai.com/api-keys
     GEMINI_API_KEY=your-key      # https://aistudio.google.com/app/apikey
     ANTHROPIC_API_KEY=your-key   # https://console.anthropic.com/

EXAMPLES:
  # Use default template (warning shown):
  python ai_conversation.py

  # Provide inline prompt:
  python ai_conversation.py --prompt "Evaluate this invention: [description]"

  # Load prompt from file:
  python ai_conversation.py --prompt tech_brief.md

  # Load knowledge base context and limit rounds:
  python ai_conversation.py --prompt brief.md --context knowledge-base/ip-context --rounds 5

  # Custom output directory:
  python ai_conversation.py --prompt brief.md --output results/

OUTPUT:
  Creates timestamped files in output directory (default: output/):
    - conversation_YYYYMMDD_HHMMSS.json  (Full conversation log)
    - final_document_YYYYMMDD_HHMMSS.txt (Final agreed document)
    - transcript_YYYYMMDD_HHMMSS.txt     (Human-readable transcript)

SUPPORTED MODELS:
  OpenAI:    gpt-4o, gpt-4-turbo, gpt-3.5-turbo
  Gemini:    models/gemini-3-flash-preview, gemini-1.5-pro, gemini-1.5-flash
  Anthropic: claude-3-5-sonnet-20241022, claude-3-opus-20240229

CONVERGENCE:
  Conversation ends when:
    - Both agents use agreement phrases (e.g., "I agree", "Looks good")
    - Maximum rounds reached (configurable with --rounds)

USE CASES:
  - Tech brief evaluation for patents
  - Document refinement and iteration
  - Content creation with diverse perspectives
  - Strategic analysis and validation
  - Code review and improvement
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
        default=10,
        metavar='N',
        help='Maximum conversation rounds before stopping (default: 10). '
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
    args = parser.parse_args()

    # Configuration - modify these as needed
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

    # Check which providers are available for multi-AI diversity
    if not GEMINI_API_KEY and not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        logger.error(
            "At least one API key is required (GEMINI, OPENAI, or ANTHROPIC)."
        )
        logger.error(
            "Set API keys in your .env file or as environment variables."
        )
        sys.exit(1)

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
                    with open(md_file, 'r', encoding='utf-8') as f:
                        kb_content.append(
                            f"## {md_file.stem.replace('-', ' ').title()}"
                            f"\n\n{f.read()}\n"
                        )

                kb_context = f"""

---

# PERSISTENT IP & BUSINESS CONTEXT

You have access to pre-loaded knowledge base context. Reference this without requiring re-explanation:

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

    # Define the two AI agents with different roles and providers for
    # diverse perspectives. Prefer multi-provider diversity when keys are
    # configured

    # Agent 1: Primary provider (prefer Gemini if available)
    if GEMINI_API_KEY:
        agent1_config = {
            "provider": "gemini",
            "model": "models/gemini-3-flash-preview",
            "api_key": GEMINI_API_KEY
        }
    elif OPENAI_API_KEY:
        agent1_config = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": OPENAI_API_KEY
        }
    else:
        agent1_config = {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": ANTHROPIC_API_KEY
        }
    
    agent1 = AIAgent(
        name="Technical Evaluator",
        **agent1_config,
        system_prompt=(
            "You are a technical evaluator specializing in intellectual "
            "property and technology assessment. Your role is to analyze "
            "tech briefs for technical accuracy, innovation potential, "
            "patentability, prior art concerns, and commercial viability. "
            "Provide detailed technical critique and identify strengths, "
            "weaknesses, and areas needing clarification. When you believe "
            "the brief is comprehensive and accurate, clearly state your "
            "approval."
        ) + kb_context
    )

    # Agent 2: Secondary provider (prefer diversity - use different
    # provider than agent1)
    if agent1_config["provider"] != "anthropic" and ANTHROPIC_API_KEY:
        agent2_config = {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": ANTHROPIC_API_KEY
        }
    elif agent1_config["provider"] != "openai" and OPENAI_API_KEY:
        agent2_config = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": OPENAI_API_KEY
        }
    else:
        # Fall back to same provider if no diversity possible
        agent2_config = agent1_config.copy()
        logger.warning(
            f"Using {agent1_config['provider']} for both agents (configure "
            f"additional API keys for diversity)"
        )
    
    agent2 = AIAgent(
        name="Strategic Analyst",
        **agent2_config,
        system_prompt=(
            "You are a strategic analyst focused on IP strategy, market "
            "positioning, and business value. Your role is to evaluate tech "
            "briefs for market opportunity, competitive advantage, strategic "
            "alignment, and implementation feasibility. Ensure the brief "
            "clearly articulates the invention's value proposition and "
            "differentiation. When the brief meets strategic requirements, "
            "explicitly confirm your approval."
        ) + kb_context
    )

    # Get initial prompt from command line, file, or use default
    initial_topic = None

    if args.prompt:
        # Check if it's a file path
        prompt_path = Path(args.prompt)
        if prompt_path.exists() and prompt_path.suffix in ['.txt', '.md']:
            logger.info(f"Loading prompt from file: {prompt_path}")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                initial_topic = f.read()
        else:
            # Treat as direct prompt text
            initial_topic = args.prompt

    # Use default template if no prompt provided
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

Please review this brief for technical accuracy, completeness, patentability considerations,
and business value. Identify gaps, suggest improvements, and help refine it into a
comprehensive document ready for IP protection.
"""
        logger.warning("Using default template prompt.")
        logger.info("For better results, provide your tech brief:")
        logger.info("  python ai_conversation.py --prompt 'your prompt here'")
        logger.info(
            "  python ai_conversation.py --prompt path/to/your_brief.md"
        )

    # Create conversation manager
    manager = ConversationManager(
        agent1=agent1,
        agent2=agent2,
        initial_prompt=initial_topic,
        max_rounds=args.rounds,
        convergence_threshold=0.85
    )

    # Run the conversation
    results = manager.run_conversation()

    # Save results
    manager.save_results(results, output_dir=args.output)

    logger.info("="*80)
    logger.info("Conversation complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
