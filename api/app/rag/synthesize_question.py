#!/usr/bin/env python3

"""Synthesize questions from document sections chunks.

Example usage:

```bash
# from the root of the api directory (i.e. seas/api)
OPENAI_API_KEY=<your-openai-api-key> python -m app.rag.synthesize_question \
    --document_sections_chunks_file app/rag/document_sections_chunks_export_20250728_162327.json \
    --model openai/gpt-4o \
    --num_questions 5 \
    --retries 3
```

"""

import argparse
import json
import os
from datetime import datetime
from operator import itemgetter
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


def generate_question(
    args: argparse.Namespace,
) -> None:
    if os.path.isdir(args.output_dir) and len(os.listdir(args.output_dir)) > 0:
        raise ValueError(
            f"Output directory {args.output_dir} already exists and is not empty"
        )

    if not os.path.isfile(
        args.document_sections_chunks_file
    ) or not args.document_sections_chunks_file.endswith(".json"):
        raise ValueError(
            f"File {args.document_sections_chunks_file} is not a valid JSON file"
        )

    os.makedirs(args.output_dir, exist_ok=True)

    df = pd.read_json(args.document_sections_chunks_file)
    sections = df["sections"]
    if (
        args.max_sections is not None
        and args.max_sections > 0
        and args.max_sections < len(sections)
    ):
        logger.info(
            f"Max sections is set to {args.max_sections}, will process only {args.max_sections} sections out of {len(sections)}"
        )
        sections = sections.sample(n=args.max_sections, random_state=42)

    logger.info(f"Total sections: {len(sections)} | total chunks: {len(df)}")

    llm = get_langchain_llm(model_name=args.model, temperature=0.6)

    system_prompt = get_prompt(
        template_name="synthesize_questions_system_prompt.j2",
        numQuestions=args.num_questions,
        currentYear=datetime.now().year,
    )

    failed_sections: list[
        str
    ] = []  # list of section ids that failed to generate questions
    output_data: list[dict[str, Any]] = []

    for section in tqdm(sections, desc="Generating questions", unit="section"):
        section_id = section["id"]
        section_chunks = section["chunks"]
        section_chunks = sorted(section_chunks, key=itemgetter("chunk_index"))
        section_chunks_content = [
            {
                "chunk_index": section_chunk["chunk_index"],
                "content": section_chunk["content"],
            }
            for section_chunk in section_chunks
        ]

        human_prompt = get_prompt(
            template_name="synthesize_questions_human_prompt.j2",
            contexts=section_chunks_content,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        retries_remaining = max(args.retries, 0)
        while retries_remaining >= 0:
            try:
                response = llm.invoke(input=messages)

                content = response.content
                assert isinstance(content, str), (  # actually it should be!
                    "Expected response.content to be a string"
                )

                generated_questions = [
                    question.strip()
                    for question in content.split("\n")
                    if question.strip()
                ]
                question_data = []
                for question in generated_questions:
                    try:
                        question_text, referenced_chunk_indices = (
                            question.rsplit("[", 1)
                        )
                        referenced_chunk_indices = [
                            int(index)
                            for index in referenced_chunk_indices.strip(
                                "[]"
                            ).split(",")
                        ]
                    except ValueError:
                        logger.error(
                            f"Failed to parse referenced chunk indices in question: {question}. This question will be ignored."
                        )
                        continue

                    referenced_chunk_ids = [
                        section_chunks[i]["id"]
                        for i in referenced_chunk_indices
                    ]
                    question_data.append({
                        "question": question_text.strip(),
                        "num_referenced_chunks": len(referenced_chunk_indices),
                        "referenced_chunk_indices": referenced_chunk_indices,
                        "referenced_chunk_ids": referenced_chunk_ids,
                    })

                output_data.append({
                    "section_id": section_id,
                    "generated_questions": question_data,
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
                    failed_sections.append(section_id)

    logger.info("*** Summary ***")
    logger.info(f"  Total sections: {len(sections)}")
    logger.info(f"  Total failed sections: {len(failed_sections)}")
    logger.info(
        f"  Total successful sections: {len(sections) - len(failed_sections)}"
    )

    output_file_path = os.path.join(
        args.output_dir, "generated_questions.json"
    )
    failed_sections_file_path = os.path.join(
        args.output_dir, "failed_sections.json"
    )
    with open(output_file_path, "w") as f:
        json.dump(
            {
                "model": args.model,
                "num_questions": args.num_questions,
                "generated_questions": output_data,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    with open(failed_sections_file_path, "w") as f:
        json.dump(
            {
                "model": args.model,
                "num_questions": args.num_questions,
                "failed_sections": failed_sections,
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
        "--document_sections_chunks_file",
        type=str,
        required=True,
        help="The file containing the document sections chunks (.json file). Get this file by exporting data from `api/v1/rag/private/export-document-sections-chunks`",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o",
        help="The model to use for generating questions in the format <provider>/<model_name>. Supported providers are: [openai, google]",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="synthesize_questions_outputs",
        help="The directory to save the generated questions",
    )
    parser.add_argument(
        "--max_sections",
        type=int,
        default=None,
        help="The maximum number of sections to process",
    )
    parser.add_argument(
        "--num_questions",
        type=int,
        default=3,
        help="The number of questions to generate per turn",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="The number of retries if the LLM fails to generate questions",
    )

    args = parser.parse_args()

    generate_question(args)


if __name__ == "__main__":
    main()
