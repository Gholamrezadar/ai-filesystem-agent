import asyncio
from dotenv import load_dotenv
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import logfire

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()

agent = Agent(
    OpenAIModel(
        model_name="llama3.2:1b",
        provider=OpenAIProvider(base_url='http://localhost:11434/v1')
    ),
    instructions="You are a helpful assistant that answers questions based on the provided context."
)


@agent.tool
async def calculator(ctx: RunContext[None], expression: str) -> float:
    '''Calculates the result of an expression using Python's eval() function.
    
    Args:
        expression (str): The expression to evaluate.
    
    Returns:
        float: The result of the expression.
    '''
    # safety checks
    # TODO
    return float(eval(expression))


response = agent.run_sync("What is the result of 2 + 2?")
print(response.output)
