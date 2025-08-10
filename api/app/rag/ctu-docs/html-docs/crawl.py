import argparse
import os
import time

from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from loguru import logger

load_dotenv()


def crawl(args: argparse.Namespace):
    if "FIRECRAWL_API_KEY" not in os.environ:
        raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

    if os.path.isdir(args.output_dir):
        raise ValueError(f"Output directory {args.output_dir} already exists")

    if not os.path.isfile(args.urls_file):
        raise ValueError(f"URLs file {args.urls_file} does not exist")

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    # config log file
    log_file_path = os.path.join(args.output_dir, args.log_file)
    logger.add(log_file_path, level="DEBUG")

    logger.info(f"Found {len(urls)} URLs to scrape")
    failed_urls: list[str] = []
    ignored_urls: list[str] = []

    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    cnt = 0
    for i, url in enumerate(urls):
        if url.lower().endswith(".pdf"):
            logger.warning(f"Ignoring pdf file: {url}")
            ignored_urls.append(url)
            continue

        retry_remaining = max(args.retries, 0)

        output_file = os.path.join(args.output_dir, f"scraped_{cnt + 1}.md")
        while retry_remaining >= 0:
            try:
                logger.info(f"Scraping URL {i + 1}/{len(urls)}: {url}")

                response = app.scrape_url(
                    url,
                    formats=["markdown"],
                    headers=None,
                    include_tags=None,
                    exclude_tags=[
                        'div[id="top1"]',  # top header
                        "video",  # video
                        'div[class="hits"]',  # views
                        'header[class*="header"]',  # header
                        'div[class*="header"]',  # header
                        'footer[class*="footer"]',  # footer
                        'div[class*="footer"]',  # footer
                        'span[style*="Wingdings"]',  # Wingdings icon
                        'div[class="user3_4"]',  # contact information, header, footer, etc
                        'section[class*="copyright"]',  # copyright information
                    ],
                    only_main_content=True,
                    timeout=60_000,
                    parse_pdf=False,
                )
                data = response

                markdown_content = data.markdown
                assert markdown_content is not None
                metadata = data.metadata
                assert metadata is not None
                title = metadata["title"]

                with open(output_file, "a") as f:
                    # Write YAML frontmatter
                    f.write("---\n")
                    for key, value in metadata.items():
                        f.write(f'{key}: "{value}"\n')
                    f.write("---\n\n")

                    # Write main content
                    f.write(f"# {title}\n\n")
                    f.write(markdown_content)
                    f.write("\n\n")

                cnt += 1
                time.sleep(0.5)  # avoid rate limiting
                break
            except Exception as err:
                if retry_remaining > 0:
                    logger.warning(
                        f"Failed to scrape {url}, retrying... ({retry_remaining} retries left)"
                    )
                    retry_remaining -= 1
                    time.sleep(1)
                else:
                    logger.error(f"Failed to scrape {url}: {err}")
                    failed_urls.append(url)
                    break

    if failed_urls:
        logger.error(f"Failed to scrape {len(failed_urls)} URLs:")
        for url in failed_urls:
            logger.error(f"  {url}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--urls_file",
        type=str,
        required=True,
        help="Path to the file containing URLs to scrape",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory to save the output files",
        default="scraped_data",
    )
    parser.add_argument(
        "--log_file",
        type=str,
        help="Log file",
        default="scrape.log",
    )
    parser.add_argument(
        "--retries",
        type=int,
        help="Number of retries for failed URLs",
        default=5,
    )
    args = parser.parse_args()
    crawl(args)


if __name__ == "__main__":
    main()
