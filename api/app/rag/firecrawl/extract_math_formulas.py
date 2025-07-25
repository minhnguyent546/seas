#!/usr/bin/env python3
"""
Extract mathematical formulas from images in markdown files using OCR with Gemini

Example usage:

```bash
python extract_math_formulas.py \
    --prompt_template ../../templates/prompts/math_formula_extraction.j2 \
    --gemini_model gemini-2.5-flash \
    --file_paths ./ctu-admission-docs/
```
"""

import argparse
import base64
import io
import os
import re
import time

import jinja2
import PIL.Image as Image
import requests
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger


def image_to_base64(image: Image.Image) -> str | None:
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def download_image(url: str):
    """Download image from URL and return PIL Image object"""
    try:
        logger.info(f"Downloading image: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading image {url}: {e}")
        return None


def load_template_from_path(template_path: str) -> jinja2.Template:
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir)
    )

    return jinja_env.get_template(template_name)


def extract_math(
    llm: ChatGoogleGenerativeAI, image: Image.Image, prompt_text: str
) -> str | None:
    try:
        # Convert image to base64
        image_base64 = image_to_base64(image)

        # Create the message with text and image
        system_message = SystemMessage(
            content="You are a helpful assistant that extracts mathematical formulas from images."
        )
        human_message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    },
                },
            ]
        )
        messages = [system_message, human_message]

        response = llm.invoke(messages)
        if hasattr(response, "content"):
            result = str(response.content).strip()
        else:
            result = str(response).strip()

        logger.info(f"Gemini response: {result}")
        return result

    except Exception as e:
        logger.error(f"Error with Gemini OCR: {e}")
        return None


def find_image_urls_in_file(file_path: str) -> list[str]:
    """Find all image URLs in a markdown file"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find markdown image syntax ![alt text](url) - handles both empty and non-empty alt text
    image_pattern = (
        r"!\[[^\]]*\]\((https://[^)]+\.(?:png|jpg|jpeg|PNG|JPG|JPEG))\)"
    )
    matches = re.findall(image_pattern, content)
    return matches


def replace_image_with_formula(
    file_path: str, image_url: str, formula_markdown: str
) -> bool:
    """Replace image reference with extracted formula in markdown file"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create the image markdown pattern to replace - handles both empty and non-empty alt text
    image_pattern = f"!\\[[^\\]]*\\]\\({re.escape(image_url)}\\)"

    # Replace with the formula (or keep original if no formula found)
    if formula_markdown and formula_markdown != "NO_MATH_FORMULAS":
        replacement = f"\n{formula_markdown}\n"
        logger.info(f"Replacing image with formula: {formula_markdown}")
    else:
        logger.info(
            "No mathematical formulas found in image, keeping original reference"
        )
        return False

    # Perform the replacement using lambda to avoid regex escape issues with LaTeX backslashes
    new_content = re.sub(pattern=image_pattern, repl=lambda m: replacement, string=content)

    # Write back to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def process_markdown_files(args: argparse.Namespace) -> None:
    """Process all markdown files and extract formulas from images"""
    if not os.path.isfile(args.prompt_template):
        logger.error(f"Prompt template file not found: {args.prompt_template}")
        exit(1)

    # llm
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        logger.error("Please set your GOOGLE_API_KEY environment variable")
        exit(1)
    llm = ChatGoogleGenerativeAI(
        model=args.gemini_model,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.1,
    )

    # file all files
    file_paths: list[str] = []
    for file_path in args.file_paths:
        if os.path.isdir(file_path):
            for file in os.listdir(file_path):
                if file.endswith('.md'):
                    file_paths.append(os.path.join(file_path, file))
        elif os.path.isfile(file_path) and file_path.endswith('.md'):
            file_paths.append(file_path)

    logger.info(f"Found {len(file_paths)} files to process")

    # prompt template
    prompt_template = load_template_from_path(args.prompt_template)
    prompt = prompt_template.render()

    total_processed = 0
    total_replaced = 0

    for file_path in file_paths:
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            continue

        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing file: {file_path}")
        logger.info(f"{'=' * 60}")

        # Find all image URLs in the file
        image_urls = find_image_urls_in_file(file_path)
        logger.info(f"Found {len(image_urls)} images in {file_path}")

        for url in image_urls:
            logger.info(f"\nProcessing image: {url}")
            total_processed += 1

            # Download the image
            image = download_image(url)
            if image is None:
                continue

            # Extract formulas using Gemini via LangChain
            formula = extract_math(llm=llm, image=image, prompt_text=prompt)
            if formula:
                # Replace in the markdown file
                logger.info(f"Formula: {formula}")
                if args.dry_run:
                    continue
                if not args.dry_run and replace_image_with_formula(file_path, url, formula):
                    total_replaced += 1

            time.sleep(10)  # avoid rate limit

    logger.info(f"\n{'=' * 60}")
    logger.info("SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Total images processed: {total_processed}")
    logger.info(f"Total images replaced with formulas: {total_replaced}")
    logger.info(
        f"Images with no math formulas: {total_processed - total_replaced}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract mathematical formulas using OCR with Gemini"
    )
    parser.add_argument(
        "--file_paths",
        type=str,
        nargs="+",
        required=True,
        help="Path to the markdown files to process, if a directory is provided, all files in the directory will be processed",
    )
    parser.add_argument(
        "--gemini_model",
        type=str,
        help="Which Gemini model to use",
        default="gemini-2.5-flash",
    )
    parser.add_argument(
        "--prompt_template",
        type=str,
        required=True,
        help="Path to the prompt template (.j2 file)",
    )
    parser.add_argument(
        "--dry_run",
        action='store_true',
        help="Do not replace the image with the formula, just print the formula",
    )
    args = parser.parse_args()

    process_markdown_files(args)


if __name__ == "__main__":
    main()
