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

# Requires: pip install openai anthropic google-generativeai
try:
    from openai import OpenAI
    from anthropic import Anthropic
    import google.generativeai as genai
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install openai anthropic google-generativeai")
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
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
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
                response = self.client.generate_content(message)
                return response.text

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
        Simple heuristic: check if they contain similar key phrases or agreement markers.
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

        # Check for similarity in length (converged documents tend to be similar length)
        length_ratio = min(len(response1), len(response2)) / \
            max(len(response1), len(response2))

        # Simple convergence: both mention agreement or length is very similar
        return agreement_count >= 2 or length_ratio > self.convergence_threshold

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
        default='ai_conversations',
        help='Output directory for results (default: ai_conversations)'
    )
    args = parser.parse_args()

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

    if not any([OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY]):
        print("Error: No API keys found.")
        print("Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY environment variables.")
        sys.exit(1)

    # Define the two AI agents with different roles - optimized for tech brief evaluation
    # Agent 1: ChatGPT (OpenAI) - Technical Evaluator
    agent1 = AIAgent(
        name="Technical Evaluator",
        provider="openai" if OPENAI_API_KEY else "gemini",
        model="gpt-4o" if OPENAI_API_KEY else "gemini-1.5-pro",
        system_prompt=(
            "You are a technical evaluator specializing in intellectual property and technology assessment. "
            "Your role is to analyze tech briefs for technical accuracy, innovation potential, "
            "patentability, prior art concerns, and commercial viability. "
            "Provide detailed technical critique and identify strengths, weaknesses, and areas needing clarification. "
            "When you believe the brief is comprehensive and accurate, clearly state your approval."
        ),
      Get initial prompt from command line, file, or use default
    initial_topic=None

    if args.prompt:
        # Check if it's a file path
        prompt_path=Path(args.prompt)
        if prompt_path.exists() and prompt_path.suffix in ['.txt', '.md']:
            print(f"Loading prompt from file: {prompt_path}")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                initial_topic=f.read()
        else:
            # Treat as direct prompt text
            initial_topic=args.prompt

    # Use default template if no prompt provided
    if not initial_topic:
        initial_topic="""
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
        print("")scribe your technical approach and innovation]

    Key Features:
    - [Feature 1]
    - [Feature 2]
        max_rounds = args.rounds,
        convergence_threshold = 0.85
    )

    # Run the conversation
    results = manager.run_conversation()

    # Save results
    manager.save_results(results, output_dir=args.output)    """

    # Create conversation manager
    manager = ConversationManager(
        agent1=agent1,
        agent2=agent2,
        initial_prompt=initial_topic,
        max_rounds=10,
        convergence_threshold=0.85
    )

    # Run the conversation
    results = manager.run_conversation()

    # Save results
    manager.save_results(results)

    print(f"\n{'='*80}")
    print("Conversation complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
