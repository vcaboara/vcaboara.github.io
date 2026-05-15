#!/usr/bin/env python3
"""
Script to facilitate a conversation between two AI agents until they converge on a final document.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

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
    print("Error: Required packages not installed.")
    print("Run: pip install -r ai_conversation_requirements.txt")
    sys.exit(1)


class AIAgent:
    """Represents an AI agent with a specific role and personality."""

    def __init__(self, name: str, provider: str, model: str, system_prompt: str, api_key: str):
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
        print(f"\n{'='*80}")
        print(
            f"Starting conversation between {self.agent1.name} and {self.agent2.name}")
        print(f"{'='*80}\n")

        current_message = self.initial_prompt
        current_speaker = self.agent1
        other_speaker = self.agent2

        converged = False
        round_num = 0

        while round_num < self.max_rounds and not converged:
            round_num += 1
            print(f"\n--- Round {round_num} ---")
            print(f"{current_speaker.name} is responding...\n")

            # Get response from current speaker
            response = current_speaker.respond(current_message)

            # Log the exchange
            self.conversation_history.append({
                "round": round_num,
                "speaker": current_speaker.name,
                "message": response,
                "timestamp": datetime.now().isoformat()
            })

            print(f"{current_speaker.name}: {response[:200]}...")
            if len(response) > 200:
                print(f"  ... ({len(response)} characters total)")

            # Check for convergence if we have at least 2 rounds
            if round_num >= 2:
                prev_response = self.conversation_history[-2]["message"]
                if self.check_convergence(prev_response, response):
                    converged = True
                    print(
                        f"\n✓ Convergence detected after {round_num} rounds!")
                    break

            # Prepare next message and swap speakers
            current_message = f"Here is the current version from {current_speaker.name}:\n\n{response}\n\nPlease review, provide feedback, and suggest improvements or confirm if this is ready."
            current_speaker, other_speaker = other_speaker, current_speaker

            # Small delay to avoid rate limits
            time.sleep(1)

        if not converged:
            print(
                f"\n⚠ Reached maximum rounds ({self.max_rounds}) without full convergence.")

        # Extract final document (last response)
        final_document = self.conversation_history[-1]["message"] if self.conversation_history else ""

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
        print(f"\n✓ Conversation log saved to: {log_file}")

        # Save final document
        doc_file = os.path.join(output_dir, f"final_document_{timestamp}.txt")
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(results["final_document"])
        print(f"✓ Final document saved to: {doc_file}")

        # Save readable transcript
        transcript_file = os.path.join(
            output_dir, f"transcript_{timestamp}.txt")
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(
                f"Conversation between {self.agent1.name} and {self.agent2.name}\n")
            f.write(f"Started: {self.conversation_history[0]['timestamp']}\n")
            f.write(f"Rounds: {results['rounds']}\n")
            f.write(f"Converged: {results['converged']}\n")
            f.write("="*80 + "\n\n")

            for entry in self.conversation_history:
                f.write(f"Round {entry['round']} - {entry['speaker']}:\n")
                f.write("-"*80 + "\n")
                f.write(f"{entry['message']}\n\n")

        print(f"✓ Transcript saved to: {transcript_file}")


def main():
    """Main entry point for the AI conversation script."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Run a conversation between two AI agents to evaluate/refine content'
    )
    parser.add_argument(
        '--prompt', '-p',
        help='Initial prompt text (or path to .txt/.md file containing the prompt)'
    )
    parser.add_argument(
        '--rounds', '-r',
        type=int,
        default=10,
        help='Maximum number of conversation rounds (default: 10)'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory for results (default: output/)'
    )
    parser.add_argument(
        '--context', '-c',
        help='Path to knowledge base directory for persistent IP context (e.g., knowledge-base/ip-context)'
    )
    args = parser.parse_args()

    # Configuration - modify these as needed
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

    # Check which providers are available for multi-AI diversity
    if not GEMINI_API_KEY and not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        print("Error: At least one API key is required (GEMINI, OPENAI, or ANTHROPIC).")
        print("Set API keys in your .env file or as environment variables.")
        sys.exit(1)

    # Load knowledge base context if specified
    kb_context = ""
    if args.context:
        kb_dir = Path(args.context)
        if kb_dir.exists():
            print(f"Loading knowledge base from: {kb_dir}")
            kb_files = list(kb_dir.glob("*.md"))
            if kb_files:
                kb_content = []
                for md_file in kb_files:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        kb_content.append(
                            f"## {md_file.stem.replace('-', ' ').title()}\n\n{f.read()}\n")

                kb_context = f"""

---

# PERSISTENT IP & BUSINESS CONTEXT

You have access to pre-loaded knowledge base context. Reference this without requiring re-explanation:

{''.join(kb_content)}

---

Integrate this knowledge naturally when relevant.

"""
                print(
                    f"✓ Loaded {len(kb_files)} context files ({sum(len(c) for c in kb_content)} characters)")
            else:
                print(f"⚠ No .md files found in {kb_dir}")
        else:
            print(f"⚠ Knowledge base directory not found: {kb_dir}")

    # Define the two AI agents with different roles and providers for diverse perspectives
    # Prefer multi-provider diversity when keys are configured
    
    # Agent 1: Primary provider (prefer Gemini if available)
    if GEMINI_API_KEY:
        agent1_config = {"provider": "gemini", "model": "models/gemini-3-flash-preview", "api_key": GEMINI_API_KEY}
    elif OPENAI_API_KEY:
        agent1_config = {"provider": "openai", "model": "gpt-4", "api_key": OPENAI_API_KEY}
    else:
        agent1_config = {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "api_key": ANTHROPIC_API_KEY}
    
    agent1 = AIAgent(
        name="Technical Evaluator",
        **agent1_config,
        system_prompt=(
            "You are a technical evaluator specializing in intellectual property and technology assessment. "
            "Your role is to analyze tech briefs for technical accuracy, innovation potential, "
            "patentability, prior art concerns, and commercial viability. "
            "Provide detailed technical critique and identify strengths, weaknesses, and areas needing clarification. "
            "When you believe the brief is comprehensive and accurate, clearly state your approval."
        ) + kb_context
    )

    # Agent 2: Secondary provider (prefer diversity - use different provider than agent1)
    if agent1_config["provider"] != "anthropic" and ANTHROPIC_API_KEY:
        agent2_config = {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "api_key": ANTHROPIC_API_KEY}
    elif agent1_config["provider"] != "openai" and OPENAI_API_KEY:
        agent2_config = {"provider": "openai", "model": "gpt-4", "api_key": OPENAI_API_KEY}
    else:
        # Fall back to same provider if no diversity possible
        agent2_config = agent1_config.copy()
        print(f"⚠ Using {agent1_config['provider']} for both agents (configure additional API keys for diversity)")
    
    agent2 = AIAgent(
        name="Strategic Analyst",
        **agent2_config,
        system_prompt=(
            "You are a strategic analyst focused on IP strategy, market positioning, and business value. "
            "Your role is to evaluate tech briefs for market opportunity, competitive advantage, "
            "strategic alignment, and implementation feasibility. "
            "Ensure the brief clearly articulates the invention's value proposition and differentiation. "
            "When the brief meets strategic requirements, explicitly confirm your approval."
        ) + kb_context
    )

    # Get initial prompt from command line, file, or use default
    initial_topic = None

    # Get initial prompt from command line, file, or use default
    initial_topic = None

    if args.prompt:
        # Check if it's a file path
        prompt_path = Path(args.prompt)
        if prompt_path.exists() and prompt_path.suffix in ['.txt', '.md']:
            print(f"Loading prompt from file: {prompt_path}")
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
        print("\n⚠ WARNING: Using default template prompt.")
        print("For better results, provide your tech brief:")
        print("  python ai_conversation.py --prompt 'your prompt here'")
        print("  python ai_conversation.py --prompt path/to/your_brief.md")
        print("")

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

    print(f"\n{'='*80}")
    print("Conversation complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
