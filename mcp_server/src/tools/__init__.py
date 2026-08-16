"""Research, Writing, and Builder tools package - Business logic for MCP server."""

# URL and file extraction tools
from .create_research_file_tool import create_research_file_tool
from .extract_guidelines_urls_tool import extract_guidelines_urls_tool

# Research query and analysis tools
from .generate_next_queries_tool import generate_next_queries_tool
from .process_github_urls_tool import process_github_urls_tool
from .process_local_files_tool import process_local_files_tool
from .run_perplexity_research_tool import run_perplexity_research_tool
from .run_web_research_tool import run_web_research_tool

# Web scraping and content processing tools
from .scrape_and_clean_other_urls_tool import scrape_and_clean_other_urls_tool
from .scrape_research_urls_tool import scrape_research_urls_tool

# Source selection and curation tools
from .select_research_sources_to_keep_tool import select_research_sources_to_keep_tool
from .select_research_sources_to_scrape_tool import select_research_sources_to_scrape_tool
from .transcribe_youtube_videos_tool import transcribe_youtube_videos_tool

# Writer and Critic tools
from .writer_tools import (
    critic_evaluate_article_tool,
    draft_article_section_tool,
    generate_article_outline_tool,
    read_research_summary_tool,
    refine_and_save_article_tool,
)

# Builder and Publisher tools
from .builder_tools import (
    execute_sandbox_tests_tool,
    export_publication_bundle_tool,
    extract_and_validate_code_tool,
    fix_code_snippets_tool,
)

# Export all functions for easy importing
__all__ = [
    # URL and file extraction
    "extract_guidelines_urls_tool",
    "process_local_files_tool",
    # Web scraping and content processing
    "scrape_and_clean_other_urls_tool",
    "scrape_research_urls_tool",
    "process_github_urls_tool",
    "transcribe_youtube_videos_tool",
    # Research query and analysis
    "generate_next_queries_tool",
    "run_perplexity_research_tool",
    "run_web_research_tool",
    # Source selection and curation
    "select_research_sources_to_keep_tool",
    "select_research_sources_to_scrape_tool",
    # Final research compilation
    "create_research_file_tool",
    # Writer and Critic tools
    "read_research_summary_tool",
    "generate_article_outline_tool",
    "draft_article_section_tool",
    "critic_evaluate_article_tool",
    "refine_and_save_article_tool",
    # Builder and Publisher tools
    "extract_and_validate_code_tool",
    "execute_sandbox_tests_tool",
    "fix_code_snippets_tool",
    "export_publication_bundle_tool",
]
