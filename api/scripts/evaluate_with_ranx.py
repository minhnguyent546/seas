#!/usr/bin/env python3
"""
Advanced evaluation script using ranx for ranking metrics.

Example of usage:
    python scripts/evaluate_with_ranx.py
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Optional

import httpx
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field
from ranx import Qrels, Run, evaluate

load_dotenv()


# Copied from ~app/rag/schemas.py
class QueryParams(BaseModel):
    query: Annotated[
        str,
        Field(
            min_length=1,
            max_length=2048,
            description="The user's chat query",
            examples=[
                "Thời gian đăng ký xét tuyển đại học chính quy năm 2025 là khi nào?"
            ],
        ),
    ]
    limit: Annotated[
        int, Field(ge=1, le=100, description="Number of chunks to retrieve")
    ] = 10
    threshold: Annotated[
        float,
        Field(ge=0.0, le=1.0, description="Threshold for similarity search"),
    ] = 0.4
    num_new_queries: Annotated[
        int,
        Field(
            description="Number of new queries to expand the query. Less than 1 means no expansion."
        ),
    ] = 3
    rerank: Annotated[
        bool, Field(description="Whether to rerank the retrieved chunks")
    ] = True


class RanxEvaluator:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=180.0)

    async def authenticate(self) -> bool:
        """Authenticate with the system and get access token."""
        try:
            login_data = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                # Extract access token from cookie
                if "access_token" in response.cookies:
                    self.access_token = response.cookies["access_token"]
                    logger.success("Authentication successful")
                    return True
                else:
                    logger.error("No access token found in response")
                    return False
            else:
                logger.error(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )

                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def send_eval_query(
        self, query_params: QueryParams
    ) -> dict[str, Any]:
        """Send query to evaluation endpoint and get complete response with metadata."""
        start_time = time.perf_counter()

        try:
            headers = {
                "Content-Type": "application/json",
            }

            # Add auth cookie if available
            cookies = {}
            if self.access_token:
                cookies["access_token"] = self.access_token

            json_data = query_params.model_dump()
            response = await self.client.post(
                f"{self.base_url}/api/v1/chatbot/query-eval",
                json=json_data,
                headers=headers,
                cookies=cookies,
            )

            end_time = time.perf_counter()
            response_time = end_time - start_time

            if response.status_code == 200:
                result = response.json()
                result["response_time"] = response_time
                return result
            else:
                logger.error(
                    f"Query failed: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time,
                    "query": query_params.query,
                    "response": "",
                    "retrieved_chunks": [],
                    "num_chunks_retrieved": 0,
                    "reranked": False,
                }

        except Exception as e:
            end_time = time.perf_counter()
            logger.error(f"Query error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": end_time - start_time,
                "query": query_params.query,
                "response": "",
                "retrieved_chunks": [],
                "num_chunks_retrieved": 0,
                "reranked": False,
            }

    def build_ranx_data(
        self,
        questions_data: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> tuple[Qrels, Run]:
        """Build qrels and run data for ranx evaluation."""

        qrels_dict: dict[str, dict[str, int]] = {}
        run_dict: dict[str, dict[str, float]] = {}

        for i, (question_data, result) in enumerate(
            zip(questions_data, results, strict=False)
        ):
            query_id = f"q_{i + 1}"

            # Build qrels (relevance judgments)
            # All referenced chunks are considered relevant with score 1
            qrels_dict[query_id] = {}
            for chunk_id in question_data.get("referenced_chunk_ids", []):
                qrels_dict[query_id][chunk_id] = 1  # Binary relevance

            # Build run (system results)
            # Use retrieved chunks with their similarity scores
            run_dict[query_id] = {}
            if result.get("success", False):
                for chunk in result.get("retrieved_chunks", []):
                    chunk_id = chunk[
                        "id"
                    ]  # Use 'id' field from DocumentSectionChunkPublic
                    similarity_score = chunk.get("similarity_score", 0.0)
                    if similarity_score is not None:
                        run_dict[query_id][chunk_id] = similarity_score

        # Filter out queries with no relevant documents
        filtered_qrels = {qid: rel for qid, rel in qrels_dict.items() if rel}
        filtered_run = {
            qid: run_dict[qid]
            for qid in filtered_qrels.keys()
            if qid in run_dict
        }

        logger.info(
            f"Built ranx data: {len(filtered_qrels)} queries with relevance judgments"
        )

        return Qrels(filtered_qrels), Run(filtered_run)

    async def evaluate_with_ranx(
        self,
        questions_file: str,
        output_dir: str = "evaluation_results",
        sample_size: Optional[int] = None,
        sim_search_limit: int = 10,
        sim_search_threshold: float = 0.4,
        query_expansion_num_new_queries: int = 3,
        rerank: bool = True,
    ) -> dict[str, Any]:
        """Run evaluation using ranx metrics."""

        # Load questions
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions_data_raw = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load questions file: {e}")
            return {}

        # Extract questions with metadata
        all_questions = []
        for section in questions_data_raw.get("generated_questions", []):
            section_id = section.get("section_id", "unknown")
            for q in section.get("generated_questions", []):
                all_questions.append({
                    "section_id": section_id,
                    "question": q["question"],
                    "referenced_chunk_ids": q.get("referenced_chunk_ids", []),
                    "num_referenced_chunks": q.get("num_referenced_chunks", 0),
                })

        if not all_questions:
            logger.error("No questions found in file")
            return {}

        logger.info(f"Found {len(all_questions)} questions to evaluate")

        # Apply sample size limit if specified
        if sample_size and sample_size > 0:
            all_questions = all_questions[:sample_size]
            logger.info(
                f"Limited to {len(all_questions)} questions due to --sample-size parameter"
            )

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Run evaluation
        results = []
        successful = 0
        total_time = 0

        logger.info("Starting ranx-based evaluation...")

        for i, question_data in enumerate(all_questions, 1):
            question = question_data["question"]
            logger.info(
                f"Question {i}/{len(all_questions)}: {question[:100]}..."
            )

            result = await self.send_eval_query(
                QueryParams(
                    query=question,
                    limit=sim_search_limit,
                    threshold=sim_search_threshold,
                    num_new_queries=query_expansion_num_new_queries,
                    rerank=rerank,
                )
            )
            # Add question metadata
            result.update({
                "question_id": i,
                "section_id": question_data["section_id"],
                "question": question,
                "referenced_chunk_ids": question_data["referenced_chunk_ids"],
                "num_referenced_chunks": question_data[
                    "num_referenced_chunks"
                ],
            })

            results.append(result)

            if result.get("success", False):
                successful += 1
                total_time += result["response_time"]

                # Log timing metrics for successful responses
                timing_info = []
                if result.get("time_to_first_chunk"):
                    timing_info.append(
                        f"first_chunk={result['time_to_first_chunk']:.2f}s"
                    )
                if result.get("query_expansion_time"):
                    timing_info.append(
                        f"query_expansion={result['query_expansion_time']:.2f}s"
                    )
                if result.get("embedding_time"):
                    timing_info.append(
                        f"embedding={result['embedding_time']:.2f}s"
                    )
                if result.get("similarity_search_time"):
                    timing_info.append(
                        f"search={result['similarity_search_time']:.2f}s"
                    )
                if result.get("chunk_retrieval_time"):
                    timing_info.append(
                        f"retrieval={result['chunk_retrieval_time']:.2f}s"
                    )
                if result.get("rerank_time"):
                    timing_info.append(f"rerank={result['rerank_time']:.2f}s")

                timing_str = (
                    ", ".join(timing_info) if timing_info else "no timing data"
                )
                logger.success(
                    f"Response received ({result['response_time']:.2f}s total, {timing_str})"
                )
            else:
                logger.error(f"Failed: {result.get('error', 'Unknown error')}")

        # Calculate basic metrics
        success_rate = (
            (successful / len(all_questions)) * 100 if all_questions else 0
        )
        avg_response_time = total_time / successful if successful > 0 else 0

        # Calculate timing metrics averages
        timing_metrics = {
            "avg_time_to_first_chunk": 0.0,
            "avg_query_expansion_time": 0.0,
            "avg_embedding_time": 0.0,
            "avg_similarity_search_time": 0.0,
            "avg_chunk_retrieval_time": 0.0,
            "avg_rerank_time": 0.0,
        }

        if successful > 0:
            successful_results = [
                r for r in results if r.get("success", False)
            ]

            # Calculate averages for each timing metric
            for metric in timing_metrics.keys():
                field_name = metric.replace("avg_", "")
                values = [
                    r.get(field_name, 0)
                    for r in successful_results
                    if r.get(field_name) is not None
                ]
                if values:
                    timing_metrics[metric] = sum(values) / len(values)

        logger.info(
            f"Basic Results: {success_rate:.1f}% success rate, {avg_response_time:.2f}s avg time"
        )
        logger.info(f"Timing Averages: {timing_metrics}")

        # Build ranx data and calculate ranking metrics
        ranx_metrics = {}
        qrels = None  # Initialize qrels variable
        if successful > 0:
            try:
                qrels, run = self.build_ranx_data(all_questions, results)

                if len(qrels.qrels) > 0:
                    # Calculate various ranking metrics
                    metrics_to_calculate = [
                        "map@1",
                        "map@3",
                        "map@5",
                        "map@10",
                        "mrr@1",
                        "mrr@3",
                        "mrr@5",
                        "mrr@10",
                        "recall@1",
                        "recall@3",
                        "recall@5",
                        "recall@10",
                        "ndcg@1",
                        "ndcg@3",
                        "ndcg@5",
                        "ndcg@10",
                        "precision@1",
                        "precision@3",
                        "precision@5",
                        "precision@10",
                    ]

                    ranx_metrics = evaluate(qrels, run, metrics_to_calculate)

                    logger.success("Ranx metrics calculated successfully:")
                    # Handle both dict and float return types from evaluate
                    if isinstance(ranx_metrics, dict):
                        for metric, score in ranx_metrics.items():
                            logger.info(f"  {metric}: {score:.4f}")
                    else:
                        # If it's a single float, log it as a generic metric
                        logger.info(f"  metric: {ranx_metrics:.4f}")
                        # Convert to dict for consistency
                        ranx_metrics = {"metric": ranx_metrics}
                else:
                    logger.warning(
                        "No queries with relevance judgments found for ranx evaluation"
                    )
            except Exception as e:
                logger.error(f"Failed to calculate ranx metrics: {e}")

        # Prepare detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        detailed_results = {
            "metadata": {
                "evaluation_type": "ranx_evaluation",
                "questions_file": questions_file,
                "base_url": self.base_url,
                "evaluation_date": datetime.now().isoformat(),
                "total_questions": len(all_questions),
                "sample_size": sample_size,
            },
            "statistics": {
                "total_questions": len(all_questions),
                "successful_responses": successful,
                "failed_responses": len(all_questions) - successful,
                "success_rate": success_rate,
                "average_response_time": avg_response_time,
                "queries_with_relevance_judgments": len(qrels.qrels)
                if qrels
                else 0,
                **timing_metrics,  # Include all timing metrics
            },
            "ranx_metrics": ranx_metrics,
            "results": results,
        }

        # Save results
        json_file = output_path / f"ranx_evaluation_results_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)

        # Generate summary report
        summary_file = output_path / f"ranx_evaluation_summary_{timestamp}.txt"
        self.generate_summary_report(detailed_results, summary_file)

        logger.success(f"Evaluation complete! Results saved to {output_path}")
        logger.info(f"JSON results: {json_file}")
        logger.info(f"Summary report: {summary_file}")

        return detailed_results

    def generate_summary_report(
        self, results: dict[str, Any], output_file: Path
    ):
        """Generate a human-readable summary report."""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("SEAS Chatbot Ranx Evaluation Summary\n")
            f.write("=" * 50 + "\n\n")

            # Metadata
            metadata = results["metadata"]
            f.write(f"Evaluation Date: {metadata['evaluation_date']}\n")
            f.write(f"Questions File: {metadata['questions_file']}\n")
            f.write(f"Base URL: {metadata['base_url']}\n")
            f.write(f"Total Questions: {metadata['total_questions']}\n")
            if metadata.get("sample_size"):
                f.write(f"Sample Size: {metadata['sample_size']}\n")
            f.write("\n")

            # Basic Statistics
            stats = results["statistics"]
            f.write("Basic Statistics:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Success Rate: {stats['success_rate']:.1f}%\n")
            f.write(f"Successful Responses: {stats['successful_responses']}\n")
            f.write(f"Failed Responses: {stats['failed_responses']}\n")
            f.write(
                f"Average Response Time: {stats['average_response_time']:.2f}s\n"
            )
            f.write(
                f"Queries with Relevance Judgments: {stats['queries_with_relevance_judgments']}\n"
            )
            f.write("\n")

            # Timing Metrics
            f.write("Timing Metrics (Averages):\n")
            f.write("-" * 25 + "\n")
            f.write(
                f"Time to First Chunk: {stats.get('avg_time_to_first_chunk', 0):.3f}s\n"
            )
            f.write(
                f"Query Expansion Time: {stats.get('avg_query_expansion_time', 0):.3f}s\n"
            )
            f.write(
                f"Embedding Time: {stats.get('avg_embedding_time', 0):.3f}s\n"
            )
            f.write(
                f"Similarity Search Time: {stats.get('avg_similarity_search_time', 0):.3f}s\n"
            )
            f.write(
                f"Chunk Retrieval Time: {stats.get('avg_chunk_retrieval_time', 0):.3f}s\n"
            )
            f.write(f"Rerank Time: {stats.get('avg_rerank_time', 0):.3f}s\n")
            f.write("\n")

            # Ranx Metrics
            ranx_metrics = results.get("ranx_metrics", {})
            if ranx_metrics:
                f.write("Ranking Metrics (Ranx):\n")
                f.write("-" * 25 + "\n")

                # Group metrics by type
                map_metrics = {
                    k: v
                    for k, v in ranx_metrics.items()
                    if k.startswith("map")
                }
                mrr_metrics = {
                    k: v
                    for k, v in ranx_metrics.items()
                    if k.startswith("mrr")
                }
                recall_metrics = {
                    k: v
                    for k, v in ranx_metrics.items()
                    if k.startswith("recall")
                }
                ndcg_metrics = {
                    k: v
                    for k, v in ranx_metrics.items()
                    if k.startswith("ndcg")
                }
                precision_metrics = {
                    k: v
                    for k, v in ranx_metrics.items()
                    if k.startswith("precision")
                }

                if map_metrics:
                    f.write("Mean Average Precision (MAP):\n")
                    for metric, score in map_metrics.items():
                        f.write(f"  {metric}: {score:.4f}\n")
                    f.write("\n")

                if mrr_metrics:
                    f.write("Mean Reciprocal Rank (MRR):\n")
                    for metric, score in mrr_metrics.items():
                        f.write(f"  {metric}: {score:.4f}\n")
                    f.write("\n")

                if recall_metrics:
                    f.write("Recall:\n")
                    for metric, score in recall_metrics.items():
                        f.write(f"  {metric}: {score:.4f}\n")
                    f.write("\n")

                if ndcg_metrics:
                    f.write("Normalized Discounted Cumulative Gain (NDCG):\n")
                    for metric, score in ndcg_metrics.items():
                        f.write(f"  {metric}: {score:.4f}\n")
                    f.write("\n")

                if precision_metrics:
                    f.write("Precision:\n")
                    for metric, score in precision_metrics.items():
                        f.write(f"  {metric}: {score:.4f}\n")
                    f.write("\n")
            else:
                f.write(
                    "No ranking metrics calculated (insufficient data)\n\n"
                )

            # Failed queries analysis
            failed_results = [
                r for r in results["results"] if not r.get("success", False)
            ]
            if failed_results:
                f.write(
                    f"Failed Queries Analysis ({len(failed_results)} failures):\n"
                )
                f.write("-" * 30 + "\n")
                for result in failed_results[:5]:  # Show first 5 failures
                    f.write(
                        f"Question {result.get('question_id', 'N/A')}: {result.get('error', 'Unknown error')}\n"
                    )
                if len(failed_results) > 5:
                    f.write(
                        f"... and {len(failed_results) - 5} more failures\n"
                    )
                f.write("\n")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ranx-based evaluation script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_opts(parser)
    args = parser.parse_args()

    username = os.getenv("FIRST_USER_USERNAME")
    password = os.getenv("FIRST_USER_PASSWORD")

    if not username or not password:
        logger.error(
            "Missing username or password (FIRST_USER_USERNAME and FIRST_USER_PASSWORD environment variables)"
        )
        return 1

    evaluator = RanxEvaluator(args.base_url, username, password)

    try:
        # Authenticate
        if not await evaluator.authenticate():
            logger.error("Authentication failed")
            return 1

        # Run evaluation
        results = await evaluator.evaluate_with_ranx(
            questions_file=args.questions_file,
            output_dir=args.output_dir,
            sample_size=args.sample_size,
            sim_search_limit=args.sim_search_limit,
            sim_search_threshold=args.sim_search_threshold,
            query_expansion_num_new_queries=args.query_expansion_num_new_queries,
            rerank=args.rerank,
        )

        if not results:
            logger.error("Evaluation failed")
            return 1

        logger.success("Evaluation completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1
    finally:
        await evaluator.close()


def add_opts(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base_url",
        type=str,
        default="http://localhost:8444",
        help="API base URL",
    )
    parser.add_argument(
        "--questions_file",
        type=str,
        default="app/rag/synthesized-questions-with-refs/generated_questions.json",
        help="Path to questions JSON file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="evaluation_results",
        help="Output directory",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        help="Limit evaluation to N questions",
        default=None,
    )

    # query params
    parser.add_argument(
        "--sim_search_limit",
        type=int,
        default=10,
        help="Limit for similarity search",
    )
    parser.add_argument(
        "--sim_search_threshold",
        type=float,
        help="Threshold for similarity search",
        default=0.4,
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Whether to rerank the results",
    )
    parser.add_argument(
        "--query_expansion_num_new_queries",
        type=int,
        help="Number of new queries to expand the query. Less than 1 means no expansion.",
        default=3,
    )


if __name__ == "__main__":
    exit(asyncio.run(main()))
