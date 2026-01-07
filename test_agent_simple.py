#!/usr/bin/env python3.11

# Simple test to verify Strands installation
try:
    from strands import Agent
    from strands_tools import calculator
    print("✅ Strands SDK imported successfully!")
    print("✅ Community tools imported successfully!")
    
    # Test creating an agent (won't run without credentials)
    agent = Agent(
        tools=[calculator],
        system_prompt="You are a helpful assistant."
    )
    print("✅ Agent created successfully!")
    print("\n🎉 Everything is set up correctly!")
    print("\nNext steps:")
    print("1. Set up AWS Bedrock credentials")
    print("2. Run your agent with: python3.11 data_lake_agent.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")