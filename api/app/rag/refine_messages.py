#!/usr/bin/env python3

"""This script is used for synthesizing questions by refining messages collected from a community chat.

Example usage:

```bash
# from the root of the api directory (i.e. seas/api)
OPENAI_API_KEY=<your-openai-api-key> python -m app.rag.refine_messages \
    --message_file app/rag/processed_messages.json \
    --model=openai/gpt-4o \
    --num_consecutive_messages=30
"""

import argparse
import json
import os
from time import sleep
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from tqdm.autonotebook import tqdm

prompt_templates = None


def get_prompt_template(template_name: str):
    """Copied from ~app/utils.py"""
    global prompt_templates
    if prompt_templates is None:
        prompt_templates = Environment(
            loader=FileSystemLoader("app/templates/prompts")
        )
    try:
        return prompt_templates.get_template(template_name)
    except Exception as err:
        logger.error(f"Failed to get prompt template: {err}")
        raise err


def get_prompt(*, template_name: str, **kwargs):
    """Copied from ~app/utils.py"""
    try:
        template = get_prompt_template(template_name)
        return template.render(kwargs)
    except Exception as err:
        logger.error(f"Failed to get prompt: {err}")
        raise err


def get_langchain_llm(model_name: str, **kwargs):
    """Copied from ~app/utils.py."""
    if "/" not in model_name:
        raise ValueError(
            f"Expected model name have the format <provider>/<model_name>, got {model_name}"
        )

    provider, model_name = model_name.split("/")
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY is not set")

        return ChatGoogleGenerativeAI(
            model=model_name, api_key=google_api_key, **kwargs
        )  # pyright: ignore[reportArgumentType]
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        return ChatOpenAI(model=model_name, api_key=openai_api_key, **kwargs)  # pyright: ignore[reportArgumentType]
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def refine_messages(
    args: argparse.Namespace,
) -> None:
    if os.path.isdir(args.output_dir) and len(os.listdir(args.output_dir)) > 0:
        raise ValueError(
            f"Output directory {args.output_dir} already exists and is not empty"
        )
    os.makedirs(args.output_dir, exist_ok=True)

    if not os.path.isfile(args.message_file) or not args.message_file.endswith(
        ".json"
    ):
        raise ValueError(f"File {args.message_file} is not a valid JSON file")

    if (
        args.num_consecutive_messages < 3
        or args.num_consecutive_messages > 100
    ):
        raise ValueError(
            f"num_consecutive_messages must be between 3 and 100, got {args.num_consecutive_messages}"
        )

    df = pd.read_json(args.message_file)
    messages = df["messages"]
    num_messages = len(messages)
    num_turns = (
        num_messages + args.num_consecutive_messages - 1
    ) // args.num_consecutive_messages
    logger.info(
        f"Total messages: {num_messages} | num_consecutive_messages: {args.num_consecutive_messages} | num_turns: {num_turns}"
    )

    llm = get_langchain_llm(model_name=args.model, temperature=0.6)

    system_prompt = get_prompt(
        template_name="refine_messages_system_prompt.j2",
    )

    output_data: list[dict[str, Any]] = []
    failed_turns: list[dict[str, Any]] = []

    for i in tqdm(range(num_turns), desc="Refining messages", unit="turn"):
        start_idx = i * args.num_consecutive_messages
        end_idx = min(start_idx + args.num_consecutive_messages, num_messages)
        messages_batch = messages[start_idx:end_idx]
        messages_batch_content = [
            message["content"] for message in messages_batch
        ]

        human_prompt = get_prompt(
            template_name="refine_messages_human_prompt.j2",
            messages=messages_batch_content,
        )

        input = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        retries_remaining = max(args.retries, 0)
        while retries_remaining >= 0:
            try:
                response = llm.invoke(input=input)

                content = response.content
                assert isinstance(content, str), (  # actually it should be!
                    "Expected response.content to be a string"
                )

                if "NO_QUESTIONS" in content:
                    logger.warning(f"No questions found for turn {i}")
                    break

                refined_messages = [
                    message.strip()
                    for message in content.split("\n")
                    if message.strip()
                ]

                # strip '-' from the beginning of each question
                refined_messages = [
                    question.strip("- ") for question in refined_messages
                ]

                if len(refined_messages) == 0:
                    logger.warning(f"No refined messages found for turn {i}")
                    break

                logger.debug(f"{refined_messages = }")

                output_data.append({
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "refined_messages": refined_messages,
                })
                sleep(0.5)  # a void rate limit
                break
            except Exception as err:
                retries_remaining -= 1
                if retries_remaining >= 0:
                    continue
                else:
                    logger.error(
                        f"Failed to generate questions after {args.retries} retries: {err}"
                    )
                    failed_turns.append({
                        "start_idx": start_idx,
                        "end_idx": end_idx,
                        "error": str(err),
                    })

    logger.info("*** Summary ***")
    logger.info(f"  Total turns: {num_turns}")
    logger.info(f"  Total failed turns: {len(failed_turns)}")
    logger.info(f"  Total successful turns: {num_turns - len(failed_turns)}")

    output_file_path = os.path.join(args.output_dir, "refined_messages.json")
    with open(output_file_path, "w") as f:
        json.dump(
            {
                "model": args.model,
                "num_consecutive_messages": args.num_consecutive_messages,
                "refined_messages": output_data,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    failed_turns_file_path = os.path.join(args.output_dir, "failed_turns.json")
    with open(failed_turns_file_path, "w") as f:
        json.dump(
            {
                "model": args.model,
                "num_consecutive_messages": args.num_consecutive_messages,
                "failed_turns": failed_turns,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate questions from contexts using LLM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--message_file",
        type=str,
        required=True,
        help="The file containing the (processed) messages (.json file).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o",
        help="The model to use for refining messages in the format <provider>/<model_name>. Supported providers are: [openai, google]",
    )
    parser.add_argument(
        "--num_consecutive_messages",
        type=int,
        help="The number of consecutive messages that will be fed to the LLM at a time",
        default=30,
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="refined_messages",
        help="The directory to save the refined messages",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="The number of retries if the LLM fails to generate questions",
    )

    args = parser.parse_args()

    refine_messages(args)


if __name__ == "__main__":
    main()
