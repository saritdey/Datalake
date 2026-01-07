#!/usr/bin/env python3.11

from strands import Agent
from strands_tools import calculator, python_repl, http_request

# Create an agent specialized for data lake operations
agent = Agent(
    tools=[calculator, python_repl, http_request],
    system_prompt="""You are a data lake expert assistant. You help with:
    - AWS data lake architecture and best practices
    - ETL pipeline optimization
    - Data processing with Glue, Lambda, and Athena
    - CloudFormation template analysis
    - Data ingestion and validation strategies
    
    You have access to tools for calculations, running Python code, and making HTTP requests.
    Always provide practical, actionable advice based on AWS best practices."""
)

def main():
    print("🏗️  Data Lake Agent initialized!")
    print("Ask me anything about your data lake architecture, ETL pipelines, or AWS services.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.strip():
                print("\n🤖 Agent:", end=" ")
                response = agent(user_input)
                print(response)
                print()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()