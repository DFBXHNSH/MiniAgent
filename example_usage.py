"""
Example usage of the refactored mini_agent framework.

This demonstrates how to use the modular components.
"""

from src import BaseAgent


def example_basic():
    """Basic agent usage."""
    print("=== Basic Agent Example ===\n")

    agent = BaseAgent(model="dashscope/qwen-turbo")

    response = agent.run("List all Python files in the current directory", verbose=True)
    print(f"Agent: {response}\n")


def example_verbose():
    """Agent with verbose output."""
    print("=== Verbose Agent Example ===\n")

    agent = BaseAgent(model="dashscope/qwen-turbo")

    response = agent.run("Read the first 20 lines of src/base_agent.py", verbose=True)
    print(f"Agent: {response}\n")


def example_compression():
    """Agent with compression enabled."""
    print("=== Compression Example ===\n")

    agent = BaseAgent(
        model="dashscope/qwen-turbo",
        enable_compression=True,
        compression_type="sliding",
        compression_interval=5,
    )

    # Simulate many turns
    for i in range(3):
        response = agent.run(f"This is turn {i+1}", verbose=True)
        print(f"Turn {i+1}: {response[:50]}...\n")

    stats = agent.get_compression_stats()
    print(f"Compression stats: {stats}\n")


def example_subagent():
    """Agent with subagent capability."""
    print("=== Subagent Example ===\n")

    agent = BaseAgent(
        model="dashscope/qwen-turbo",
        enable_subagent=True,
    )

    response = agent.run(
        "Use a subagent to find all Python files in the src directory",
        verbose=True
    )
    print(f"Agent: {response}\n")


def example_chat():
    """Interactive chat mode."""
    print("=== Chat Mode Example ===\n")

    agent = BaseAgent(model="dashscope/qwen-turbo")
    agent.chat(verbose=True)


def example_skill():
    """Agent using skills for domain knowledge."""
    print("=== Skill Example ===\n")

    agent = BaseAgent(model="dashscope/qwen-turbo")

    # Example: Use code-review skill to review some code
    response = agent.run(
        "Review this function for bugs and best practices:\n\n"
        "def calculate_average(numbers):\n"
        "    total = 0\n"
        "    for n in numbers:\n"
        "        total += n\n"
        "    return total / len(numbers)"
        "<important>use code-review skill</important>",
        verbose=True
    )
    print(f"Agent: {response}\n")

    # Check skill usage
    print(f"Skills used: {agent.get_skill_count()}")


def example_modular_components():
    """Example of using individual components."""
    print("=== Modular Components Example ===\n")

    # Use LLM client directly
    from src.llm import LLMClient

    llm = LLMClient(model="dashscope/qwen-turbo")
    messages = [{"role": "user", "content": "Say hello in 3 words"}]
    response = llm.call(messages)
    print(f"LLM response: {response.content}\n")

    # Use message builder
    from src.messages import MessageBuilder

    builder = MessageBuilder()
    messages = [{"role": "system", "content": "You are helpful"}]
    new_messages = builder.build_copy(
        messages, "Test message", first_call=True, initial_reminder="Reminder"
    )
    print(f"Built {len(new_messages)} messages\n")

    # Use todo manager
    from src.tools import TodoManager

    todo_manager = TodoManager()
    todos = [
        {"content": "Task 1", "status": "pending", "activeForm": "Doing task 1..."},
        {"content": "Task 2", "status": "in_progress", "activeForm": "Doing task 2..."},
    ]
    print(todo_manager.update(todos))

    # Use compression strategy
    from src.compression import SlidingWindowCompression

    strategy = SlidingWindowCompression()
    # ... apply compression
    print("\nModular components can be used independently!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        example = sys.argv[1]
        examples = {
            "basic": example_basic,
            "verbose": example_verbose,
            "compression": example_compression,
            "subagent": example_subagent,
            "chat": example_chat,
            "skill": example_skill,
            "modular": example_modular_components,
        }

        if example in examples:
            examples[example]()
        else:
            print(f"Unknown example: {example}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        print("Available examples:")
        print("  python example_usage.py basic")
        print("  python example_usage.py verbose")
        print("  python example_usage.py compression")
        print("  python example_usage.py subagent")
        print("  python example_usage.py chat")
        print("  python example_usage.py skill")
        print("  python example_usage.py modular")
