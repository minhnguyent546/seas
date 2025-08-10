#!/usr/bin/env python3
"""
Script for evaluation using ragas to evaluate LLM responses.
"""

import argparse
import json
import os
import random

import datasets
import ragas
import ragas.metrics as ragas_metrics
from dotenv import load_dotenv
from loguru import logger
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig

load_dotenv()


def get_langchain_llm(model_name: str, **kwargs):
    """Copied from ~app/utils.py."""
    try:
        provider, model_name = model_name.split("/", 1)
        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model=model_name, **kwargs)
        elif provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=model_name, **kwargs)
        elif provider == "openrouter":
            from langchain_openai import (
                ChatOpenAI,  # as OpenRouter uses an OpenAI-compatible API
            )

            kwargs["openai_api_base"] = os.environ.get("OPENAI_API_BASE")
            kwargs["openai_api_key"] = os.environ.get("OPENROUTER_API_KEY")

            return ChatOpenAI(model=model_name, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as err:
        logger.error(f"Failed to initialize langchain llm: {err}")
        raise err


def evaluate_with_ragas(args: argparse.Namespace) -> None:
    if os.path.isdir(args.output_dir) and len(os.listdir(args.output_dir)) > 0:
        raise ValueError(
            f"Output directory {args.output_dir} already exists and is not empty."
        )

    if not os.path.isfile(
        args.eval_result_file
    ) or not args.eval_result_file.endswith(".json"):
        raise ValueError(
            f"Evaluation result file {args.eval_result_file} does not exist or is not a JSON file."
        )

    os.makedirs(args.output_dir, exist_ok=True)

    log_file_path = os.path.join(args.output_dir, "ragas_evaluation.log")
    logger.add(log_file_path)

    logger.info(
        "Reading questions, answers, and contexts from evaluation result file..."
    )

    # llm and embeddings
    llm = get_langchain_llm(model_name=args.model_name)
    evaluator_llm = LangchainLLMWrapper(langchain_llm=llm)

    with open(args.eval_result_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    eval_results = json_data["results"]

    if args.sample_size is not None:
        logger.info(
            f"Sampling {args.sample_size} random samples from evaluation results..."
        )
        eval_results = random.sample(eval_results, args.sample_size)

    questions: list[str] = []
    answers: list[str] = []
    contexts: list[list[str]] = []

    for result in eval_results:
        questions.append(result["question"])
        answers.append(result["response"])

        # assume the retrieved chunks are already sorted by similarity score
        retrieved_chunks = [
            chunk["content"] for chunk in result["retrieved_chunks"][: args.k]
        ]

        contexts.append(retrieved_chunks)

    ds = datasets.Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
    })

    logger.info("Start evaluation...")
    regas_result = ragas.evaluate(
        dataset=ds,
        metrics=[
            ragas_metrics.ContextRelevance(),
            ragas_metrics.Faithfulness(),
            ragas_metrics.AnswerRelevancy(),
        ],
        llm=evaluator_llm,
        run_config=RunConfig(max_workers=2),  # avoid rate limit
    )

    df = regas_result.to_pandas()
    output_file_path = os.path.join(args.output_dir, "ragas_evaluation.json")
    eval_result = {}
    eval_result["llm"] = args.model_name
    eval_result["sample_size"] = args.sample_size
    eval_result["results"] = df.to_dict(orient="records")
    for k, v in regas_result._repr_dict.items():  # pyright: ignore[reportPrivateUsage]
        eval_result[k] = v

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Ragas evaluation results saved to {args.output_dir}/ragas_evaluation.json"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate LLM responses using ragas",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_opts(parser)
    args = parser.parse_args()

    evaluate_with_ragas(args)


def add_opts(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--eval_result_file",
        type=str,
        required=True,
        help="Path to the evaluation result file (.json file)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="ragas_evaluation_results",
        help="Output directory",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="openai/gpt-4o",
        help="LLM model used for evaluation",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Limit the number of retrieved chunks",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=None,
        help="Number of samples to evaluate (leave `None` for all)",
    )


if __name__ == "__main__":
    main()
