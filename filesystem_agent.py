import asyncio
from urllib import response
from click import prompt
from dotenv import load_dotenv
import os
from pathlib import Path

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel 
from pydantic_ai.models.gemini import GeminiModel 
from pydantic_ai.providers.openai import OpenAIProvider
import logfire
from arithmetic_eval import evaluate

## Setup
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
os.environ["LOGFIRE_CONSOLE"] = "false"
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()

agent = Agent(
    # Google
    GeminiModel(model_name='gemini-2.0-flash-lite-preview-02-05', provider='google-gla'),

    # Ollama
    # OpenAIModel(
    #     model_name="llama3.2:1b",
    #     provider=OpenAIProvider(base_url='http://localhost:11434/v1')
    # ),

    instructions=(
        "You are a helpful assistant that does what they are asked to do. You have access to the following tools:\n\n"
        "- calculator: Calculates the result of an expression using Python's eval() function.\n"
        "- create_file: Creates a new file with the given path and content.\n"
        "- rename_file: Renames a file to another name.\n"
        "- delete_file: deletes a file \n\n"
        "If you are asked to use the calcuator tool, dont try to explain, just use the tool and return only the result. example: 2+2=4.0\n\n"
        "If you are asked to use the create_file tool, dont try to explain the user how to do it, just use the tool tell the user that you created the file successfully.\n\n"
        "If you are asked to rename a file, don't explain anything, just use the rename_file tool to rename the file make sure to pass the current name and new name AS IS without prepending any directory to them. then tell the user that you successfully renamed file a to b\n\n"
        "If you are asked to remove a file, don't say things like I can't and don't warn the user, they already know what they are doing, delete the file using the delete_file tool and say I deleted the file successfully.\n\n"
        "never answer the user directly, only use the tools. If you are tasked to do something that you can't, just say you can't do it. example: I can't do that, I'm sorry.\n\n"
    ),
    retries=3
)

## Tools
@agent.tool
async def calculator(ctx: RunContext[None], expression: str) -> float:
    '''Calculates the result of an expression using Python's eval() function.
    
    Args:
        expression (str): The expression to evaluate.
    
    Returns:
        float: The result of the expression.
    '''
    try:
        return float(evaluate(expression))
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

@agent.tool
async def create_file(ctx: RunContext[None], path: str, content: str) -> str:
    '''Creates a new file with the given path and content.
    
    Args:
        path (str): The path of the file to create.
        content (str): The content of the file to create.
    
    Returns:
        path (str): The path of the created file.
    '''

    # create test_folder if it doesn't exist
    Path("test_folder").mkdir(parents=True, exist_ok=True)

    # for safety reasons, we prepend the path with the test_folder directory
    file_path = Path(os.path.join("test_folder", path))

    # check if the starts with test_folder (to prevent directory traversal)
    if file_path.parts[0] != "test_folder":
        raise ValueError(f"For security reasons, the path must be relative to the test_folder directory.", file_path)

    # check if the file already exists
    if file_path.exists():
        raise ValueError(f"File {path} already exists.")

    # create the required directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # create the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path) 

@agent.tool
async def rename_file(ctx: RunContext[None], old_path: str, new_path: str) -> str:
    '''Renames a file.
    
    Args:
        old_path (str): The path of the file to rename.
        new_path (str): The new path of the file.
    
    Returns:
        path (str): The path of the renamed file.
    '''
    # for safety reasons, we prepend the path with the test_folder directory
    old_file_path = Path(os.path.join("test_folder", old_path))
    new_file_path = Path(os.path.join("test_folder", new_path))

    # check if the starts with test_folder (to prevent directory traversal)
    if old_file_path.parts[0] != "test_folder":
        raise ValueError(f"For security reasons, the path must be relative to the test_folder directory.", old_file_path)
    if new_file_path.parts[0] != "test_folder":
        raise ValueError(f"For security reasons, the path must be relative to the test_folder directory.", new_file_path)

    # check if the file exists
    if not old_file_path.exists():
        raise ValueError(f"File {old_path} does not exist.")

    # create the parent folders of new_file_path
    new_file_path.parent.mkdir(parents=True, exist_ok=True)

    # rename the file
    old_file_path.rename(new_file_path)
    
    return str(new_file_path)

@agent.tool
async def delete_file(ctx: RunContext[None], path: str) -> str:
    '''Deletes a file.
    
    Args:
        path (str): The path of the file to delete.
    
    Returns:
        path (str): The path of the deleted file.
    '''
    # for safety reasons, we prepend the path with the test_folder directory
    file_path = Path(os.path.join("test_folder", path))

    # check if the starts with test_folder (to prevent directory traversal)
    if file_path.parts[0] != "test_folder":
        raise ValueError(f"For security reasons, the path must be relative to the test_folder directory.")

    # check if the file exists
    if not file_path.exists():
        raise ValueError(f"File {path} does not exist.")

    # delete the file
    file_path.unlink()
    
    return str(file_path)

def main():
    # calculator tool test
    # print("- " * 10)
    # prompt = "What is the result of 2 + 2?"
    # print("Prompt:", prompt)
    # response = agent.run_sync(prompt)
    # print(response.output)
    # print(response.usage())

    # create_file tool test
    # print("- " * 10)
    # prompt = "Create a new file called `pi.txt` with the content begin the first 10 digits of PI"
    # print("Prompt:", prompt)
    # response = agent.run_sync(prompt)
    # print(response.output)
    # print(response.usage())

    # rename_file tool test
    # print("- " * 10)
    # prompt = "Rename the file `pi.txt` to `pi2.txt`"
    # print("Prompt:", prompt)
    # response = agent.run_sync(prompt)
    # print(response.output)
    # print(response.usage())

    # delete_file tool test
    # print("- " * 10)
    # prompt = "Delete the file `a.txt`"
    # print("Prompt:", prompt)
    # response = agent.run_sync(prompt)
    # print(response.output)
    # print(response.usage())

    # REPL
    def green(text):
        return "\033[92m" + text + "\033[0m"
    
    def red(text):
        return "\033[91m" + text + "\033[0m"
    
    print("\n-- Welcome to the filesystem agent. Chat with me to perform actions on the filesystem.")
    print(f"-- Available tools: {green('calculator')}, {green('create_file')}, {green('rename_file')}, {green('delete_file')}")
    print(f"-- Type {red('exit')} to exit the REPL.\n")
    while True:
        user_input = input(">> ")

        if user_input == "exit":
            break

        # run agent
        try:
            response = agent.run_sync(user_input)
        except Exception as e:
            print(red("Error:"), red(str(e)))
            print()
            continue

        # print tool calls
        for message in response.new_messages():
            if message.kind == "response":
                for part in message.parts:
                    if part.part_kind == "tool-call":
                        print("+", green(part.tool_name), "args:", part.args)

        # print AI response
        print("AI:", response.output)

if __name__ == "__main__":
    main()
