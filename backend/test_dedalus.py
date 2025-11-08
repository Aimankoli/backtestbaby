import asyncio
import os
from dotenv import load_dotenv
from dedalus_labs import AsyncDedalus, DedalusRunner

load_dotenv()

async def main():
    print(f"DEDALUS_API_KEY set: {' YES' if os.getenv('DEDALUS_API_KEY') else 'NO'}")

    try:
        client = AsyncDedalus()
        runner = DedalusRunner(client)

        print("Sending test request to Dedalus...")
        result = await runner.run(
            input="Say hello in one word",
            model="openai/gpt-5-mini",
            stream=False
        )

        print(f"Response: {result.final_output}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
