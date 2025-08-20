#!/usr/bin/env python3
"""
Script to get retrieved context and model responses for questions in refined_messages.json for further evaluation with ragas.

Example of usage:
    python scripts/get_responses_for_refined_messages.py
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


class ContextResponseCollector:
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

    async def send_query(self, query_params: QueryParams) -> dict[str, Any]:
        """Send query to API and get response with retrieved chunks."""
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

    async def collect_responses(
        self,
        refined_messages_file: str,
        output_dir: str = "refined_messages_responses",
        sample_size: Optional[int] = None,
        sim_search_limit: int = 10,
        sim_search_threshold: float = 0.4,
        query_expansion_num_new_queries: int = 3,
        rerank: bool = True,
    ) -> dict[str, Any]:
        """Collect responses for all questions in refined_messages.json."""

        # Load refined messages
        try:
            with open(refined_messages_file, "r", encoding="utf-8") as f:
                refined_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load refined messages file: {e}")
            return {}

        # Extract all questions from refined messages
        all_questions = []
        for section in refined_data.get("refined_messages", []):
            section_questions = section.get("refined_messages", [])
            for i, question in enumerate(section_questions):
                all_questions.append({
                    "question": question,
                    "section_start": section.get("start_idx", 0),
                    "section_end": section.get("end_idx", 0),
                    "question_index": i,
                })

        if not all_questions:
            logger.error("No questions found in refined messages file")
            return {}

        logger.info(f"Found {len(all_questions)} questions to process")

        # Apply sample size limit if specified
        if sample_size and sample_size > 0:
            all_questions = all_questions[:sample_size]
            logger.info(
                f"Limited to {len(all_questions)} questions due to --sample-size parameter"
            )

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Process questions
        results = []
        successful = 0
        total_time = 0

        logger.info("Starting to collect responses...")

        for i, question_data in enumerate(all_questions, 1):
            question = question_data["question"]
            logger.info(
                f"Question {i}/{len(all_questions)}: {question[:100]}..."
            )

            result = await self.send_query(
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
                "question": question,
                "section_start": question_data["section_start"],
                "section_end": question_data["section_end"],
                "question_index": question_data["question_index"],
            })

            results.append(result)

            if result.get("success", False):
                successful += 1
                total_time += result["response_time"]
                logger.success(
                    f"Response received ({result['response_time']:.2f}s total)"
                )
            else:
                logger.error(f"Failed: {result.get('error', 'Unknown error')}")

        # Calculate basic metrics
        success_rate = (
            (successful / len(all_questions)) * 100 if all_questions else 0
        )
        avg_response_time = total_time / successful if successful > 0 else 0

        logger.info(
            f"Basic Results: {success_rate:.1f}% success rate, {avg_response_time:.2f}s avg time"
        )

        # Prepare detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        detailed_results = {
            "metadata": {
                "evaluation_type": "context_response_collection",
                "refined_messages_file": refined_messages_file,
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
            },
            "results": results,
        }

        # Save results
        json_file = output_path / f"context_response_results_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)

        # Generate summary report
        summary_file = (
            output_path / f"context_response_summary_{timestamp}.txt"
        )
        self.generate_summary_report(detailed_results, summary_file)

        logger.success(f"Collection complete! Results saved to {output_path}")
        logger.info(f"JSON results: {json_file}")
        logger.info(f"Summary report: {summary_file}")

        return detailed_results

    def generate_summary_report(
        self, results: dict[str, Any], output_file: Path
    ):
        """Generate a human-readable summary report."""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("SEAS Chatbot Context Response Collection Summary\n")
            f.write("=" * 55 + "\n\n")

            # Metadata
            metadata = results["metadata"]
            f.write(f"Collection Date: {metadata['evaluation_date']}\n")
            f.write(
                f"Refined Messages File: {metadata['refined_messages_file']}\n"
            )
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
            f.write("\n")

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
        description="Get responses for questions in refined_messages.json for further evaluation with ragas",
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

    collector = ContextResponseCollector(args.base_url, username, password)

    try:
        # Authenticate
        if not await collector.authenticate():
            logger.error("Authentication failed")
            return 1

        # Collect responses
        results = await collector.collect_responses(
            refined_messages_file=args.refined_messages_file,
            output_dir=args.output_dir,
            sample_size=args.sample_size,
            sim_search_limit=args.sim_search_limit,
            sim_search_threshold=args.sim_search_threshold,
            query_expansion_num_new_queries=args.query_expansion_num_new_queries,
            rerank=args.rerank,
        )

        if not results:
            logger.error("Collection failed")
            return 1

        logger.success("Collection completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return 1
    finally:
        await collector.close()


def add_opts(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base_url",
        type=str,
        default="http://localhost:8444",
        help="API base URL",
    )
    parser.add_argument(
        "--refined_messages_file",
        type=str,
        default="app/rag/chat-data/refined_messages.json",
        help="Path to refined messages JSON file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="refined_messages_responses",
        help="Output directory",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        help="Limit collection to N questions",
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
