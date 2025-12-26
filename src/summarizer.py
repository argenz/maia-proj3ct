"""AI-powered summarization using Claude API."""

import json
import logging
from typing import List, Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class Summarizer:
    """Summarize and categorize newsletter content using Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize Claude summarizer.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def summarize(
        self,
        newsletter_items: List[Dict],
        categories: List[str],
        max_items_per_category: int = 5
    ) -> Dict[str, List[Dict]]:
        """Summarize and categorize newsletter content.

        Args:
            newsletter_items: List of extracted newsletter content
            categories: List of category names
            max_items_per_category: Maximum items per category

        Returns:
            Dictionary mapping categories to lists of summarized items
        """
        if not newsletter_items:
            return {category: [] for category in categories}

        logger.info(f"Summarizing {len(newsletter_items)} newsletter items with Claude...")

        # Prepare content for Claude
        newsletters_text = self._format_newsletters(newsletter_items)

        # Create prompt
        prompt = self._build_prompt(newsletters_text, categories, max_items_per_category)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            result_text = response.content[0].text

            # Extract JSON from response
            digest = self._parse_response(result_text, categories)

            logger.info("Summarization complete")
            return digest

        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            raise RuntimeError(f"Failed to summarize content: {e}")

    def _format_newsletters(self, items: List[Dict]) -> str:
        """Format newsletter items into text for Claude.

        Args:
            items: List of newsletter content dictionaries

        Returns:
            Formatted string representation
        """
        formatted = []
        for i, item in enumerate(items, 1):
            formatted.append(f"=== Newsletter {i} ===")
            formatted.append(f"Source: {item.get('source', 'Unknown')}")
            formatted.append(f"Title: {item.get('title', 'Untitled')}")
            formatted.append(f"\nContent:\n{item.get('content', '')[:2000]}")  # Limit content length

            # Include important links
            links = item.get('links', [])[:10]  # First 10 links
            if links:
                formatted.append("\nLinks:")
                for link in links:
                    formatted.append(f"- {link.get('text', 'Link')}: {link.get('url', '')}")

            formatted.append("\n")

        return "\n".join(formatted)

    def _build_prompt(
        self,
        newsletters_text: str,
        categories: List[str],
        max_items: int
    ) -> str:
        """Build Claude prompt for summarization.

        Args:
            newsletters_text: Formatted newsletter content
            categories: Category names
            max_items: Max items per category

        Returns:
            Prompt string
        """
        categories_str = ", ".join(categories)

        prompt = f"""You are an AI newsletter digest curator. Your task is to read multiple AI newsletters and create a consolidated daily digest.

CATEGORIES: {categories_str}

INSTRUCTIONS:
1. Read through all the newsletters below
2. Extract the most important and interesting items
3. Categorize each item into one of the categories above
4. Summarize each item in 1-2 concise sentences
5. Include up to {max_items} items per category
6. Prioritize:
   - Novel research and breakthrough papers
   - Significant product launches and tools
   - Important industry news and updates
7. For each item, include:
   - Brief summary (1-2 sentences)
   - Source newsletter name
   - Relevant link (if available)

OUTPUT FORMAT (JSON):
{{
  "Category Name": [
    {{
      "title": "Item headline",
      "summary": "1-2 sentence summary",
      "source": "Newsletter name",
      "link": "URL (if available)"
    }}
  ]
}}

NEWSLETTERS:
{newsletters_text}

Please provide the digest in valid JSON format only, no additional text."""

        return prompt

    def _parse_response(self, response_text: str, categories: List[str]) -> Dict[str, List[Dict]]:
        """Parse Claude's response into structured digest.

        Args:
            response_text: Claude's text response
            categories: Expected categories

        Returns:
            Structured digest dictionary
        """
        try:
            # Try to find JSON in the response
            # Look for content between first { and last }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx+1]
            digest = json.loads(json_str)

            # Ensure all categories exist (even if empty)
            result = {}
            for category in categories:
                result[category] = digest.get(category, [])

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response: {response_text[:500]}")

            # Return empty digest if parsing fails
            return {category: [] for category in categories}
