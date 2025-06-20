"""
Main Scraper Worker
Orchestrates the Reddit scraping, character extraction, and database updates
"""

from database.db_manager import DatabaseManager
from extractors.character_extractor import CharacterExtractor
from scrapers.reddit_scraper import RedditScraper, create_reddit_scraper_from_env, RedditPost
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CosplayRadarScraper:
    def __init__(self):
        """Initialize the main scraper with all components"""
        # Load configuration from environment
        self.config = self._load_config()

        # Initialize components
        self.reddit_scraper = create_reddit_scraper_from_env()
        if not self.reddit_scraper:
            raise ValueError("Failed to initialize Reddit scraper")

        self.character_extractor = CharacterExtractor()
        self.db_manager = DatabaseManager()

        logger.info("CosplayRadar Scraper initialized successfully")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'subreddits': os.getenv('REDDIT_SUBREDDITS', 'cosplay,anime,gaming,cosplayers').split(','),
            'scrape_limit': int(os.getenv('SCRAPE_LIMIT', '100')),
            'min_score_threshold': int(os.getenv('MIN_SCORE_THRESHOLD', '10')),
            'time_filter': os.getenv('TIME_FILTER', 'day'),
            'sort_method': os.getenv('SORT_METHOD', 'hot'),
            'min_confidence_threshold': float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.6')),
            'max_characters_per_run': int(os.getenv('MAX_CHARACTERS_PER_RUN', '50')),
            'enable_comments_analysis': os.getenv('ENABLE_COMMENTS_ANALYSIS', 'false').lower() == 'true'
        }

    def run_scraping_cycle(self) -> Dict[str, Any]:
        """Run a complete scraping cycle"""
        start_time = datetime.now()
        logger.info(f"Starting scraping cycle at {start_time}")

        results = {
            'start_time': start_time.isoformat(),
            'posts_scraped': 0,
            'characters_found': 0,
            'characters_updated': 0,
            'characters_created': 0,
            'errors': [],
            'processing_time': 0
        }

        try:
            # Step 1: Scrape Reddit posts
            logger.info("Step 1: Scraping Reddit posts")
            posts = self._scrape_reddit_posts()
            results['posts_scraped'] = len(posts)

            if not posts:
                logger.warning("No posts found, ending cycle")
                return results

            # Step 2: Extract characters from posts
            logger.info("Step 2: Extracting characters from posts")
            characters = self._extract_characters_from_posts(posts)
            results['characters_found'] = len(characters)

            if not characters:
                logger.warning("No characters extracted, ending cycle")
                return results

            # Step 3: Update database
            logger.info("Step 3: Updating database")
            db_results = self._update_database(characters)
            results.update(db_results)

            # Step 4: Update trend data
            logger.info("Step 4: Updating trend data")
            self._update_trend_data(characters)

        except Exception as e:
            logger.error(f"Error in scraping cycle: {e}")
            results['errors'].append(str(e))

        finally:
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['processing_time'] = (
                end_time - start_time).total_seconds()

            logger.info(
                f"Scraping cycle completed in {
                    results['processing_time']:.2f} seconds")
            logger.info(
                f"Results: {
                    json.dumps(
                        results,
                        indent=2,
                        default=str)}")

        return results

    def _scrape_reddit_posts(self) -> List[RedditPost]:
        """Scrape posts from Reddit"""
        try:
            posts = self.reddit_scraper.scrape_cosplay_posts(
                subreddits=self.config['subreddits'],
                time_filter=self.config['time_filter'],
                limit=self.config['scrape_limit'],
                sort=self.config['sort_method']
            )

            # Filter by minimum score
            filtered_posts = [
                post for post in posts
                if post.score >= self.config['min_score_threshold']
            ]

            logger.info(
                f"Scraped {
                    len(posts)} posts, {
                    len(filtered_posts)} meet score threshold")
            return filtered_posts

        except Exception as e:
            logger.error(f"Error scraping Reddit posts: {e}")
            return []

    def _extract_characters_from_posts(
            self, posts: List[RedditPost]) -> List[Dict[str, Any]]:
        """Extract character information from posts"""
        all_characters = []

        for post in posts:
            try:
                # Combine title and text for analysis
                text_content = f"{post.title} {post.text}".strip()

                # Extract characters from text
                characters = self.character_extractor.extract_characters_from_text(
                    text_content, post.permalink)

                # Add post context and calculate scores
                for character in characters:
                    # Filter by confidence threshold
                    if character['confidence'] < self.config['min_confidence_threshold']:
                        continue

                    # Add post metrics
                    post_metrics = {
                        'upvotes': post.score,
                        'comments': post.num_comments,
                        'upvote_ratio': post.upvote_ratio,
                        'subreddit': post.subreddit
                    }

                    # Calculate popularity score
                    popularity_score = self.character_extractor.calculate_character_score(
                        character, post_metrics)

                    # Enhance character data
                    enhanced_character = {
                        **character,
                        'popularity_score': popularity_score,
                        'post_id': post.id,
                        'post_score': post.score,
                        'post_comments': post.num_comments,
                        'subreddit': post.subreddit,
                        'discovered_at': post.created_utc,
                        'post_url': post.permalink
                    }

                    # Get additional context from comments if enabled
                    if self.config['enable_comments_analysis']:
                        try:
                            comments = self.reddit_scraper.get_post_comments(
                                post.id, limit=10)
                            if comments:
                                # Analyze comments for additional character
                                # context
                                # Use first 5 comments
                                comment_text = ' '.join(comments[:5])
                                comment_characters = self.character_extractor.extract_characters_from_text(
                                    comment_text, post.permalink)

                                # Boost confidence if character mentioned in
                                # comments
                                for comment_char in comment_characters:
                                    if comment_char['name'].lower(
                                    ) == character['name'].lower():
                                        enhanced_character['confidence'] = min(
                                            1.0, enhanced_character['confidence'] + 0.1)
                                        enhanced_character['popularity_score'] += 5
                                        break
                        except Exception as e:
                            logger.warning(
                                f"Error analyzing comments for post {
                                    post.id}: {e}")

                    all_characters.append(enhanced_character)

            except Exception as e:
                logger.warning(
                    f"Error extracting characters from post {
                        post.id}: {e}")
                continue

        # Remove duplicates and sort by popularity score
        unique_characters = {}
        for char in all_characters:
            char_key = char['name'].lower()
            if char_key not in unique_characters:
                unique_characters[char_key] = char
            else:
                # Keep the character with higher popularity score
                existing = unique_characters[char_key]
                if char['popularity_score'] > existing['popularity_score']:
                    unique_characters[char_key] = char
                else:
                    # Merge some data
                    existing['popularity_score'] = max(
                        existing['popularity_score'], char['popularity_score'])

        # Limit number of characters and sort by score
        sorted_characters = sorted(
            unique_characters.values(),
            key=lambda x: x['popularity_score'],
            reverse=True
        )

        limited_characters = sorted_characters[:
                                               self.config['max_characters_per_run']]

        logger.info(
            f"Extracted {
                len(all_characters)} total character mentions, " f"{
                len(unique_characters)} unique, " f"{
                len(limited_characters)} selected for processing")

        return limited_characters

    def _update_database(
            self, characters: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update database with character information"""
        created_count = 0
        updated_count = 0
        errors = []

        for character in characters:
            try:
                # Prepare character data for database
                character_data = {
                    'name': character['name'],
                    'series': character.get('series', 'Unknown'),
                    'category': self.db_manager.map_fandom_to_category(character.get('fandom', 'Other')),
                    'difficulty': self.db_manager.calculate_difficulty(character),
                    # Convert to 0-1 scale
                    'popularity': character['popularity_score'] / 100.0,
                    'imageUrl': self.db_manager.generate_character_image_url(character['name']),
                    'description': f"Character discovered from Reddit post on r/{character.get('subreddit', 'unknown')}",
                    'tags': self.db_manager.generate_character_tags(character),
                    'fandom': character.get('fandom', 'Other'),
                    'gender': character.get('gender', 'Unknown'),
                    'popularityScore': character['popularity_score'],
                    'sourceUrl': character.get('source_url', character.get('post_url'))
                }

                # Upsert character to database
                result = self.db_manager.upsert_character(character_data)

                if result and result.get('created'):
                    created_count += 1
                    logger.info(f"Created new character: {character['name']}")
                elif result:
                    updated_count += 1
                    logger.info(f"Updated character: {character['name']}")

            except Exception as e:
                error_msg = f"Error updating character {
                    character.get(
                        'name', 'unknown')}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return {
            'characters_created': created_count,
            'characters_updated': updated_count,
            'database_errors': errors
        }

    def _update_trend_data(self, characters: List[Dict[str, Any]]) -> None:
        """Update trend data for characters"""
        try:
            for character in characters:
                trend_data = {
                    'character_name': character['name'],
                    'platform': 'REDDIT',
                    'mentions': 1,  # Each scrape cycle counts as 1 mention
                    'engagement': character.get('post_score', 0) + character.get('post_comments', 0),
                    'sentiment': 0.5,  # Neutral sentiment for now
                    'date': datetime.now()
                }

                self.db_manager.insert_trend_data(trend_data)

        except Exception as e:
            logger.error(f"Error updating trend data: {e}")


def main():
    """Main entry point for the scraper"""
    logger.info("Starting CosplayRadar Scraper")

    try:
        scraper = CosplayRadarScraper()
        results = scraper.run_scraping_cycle()

        # Log summary
        logger.info("=" * 50)
        logger.info("SCRAPING CYCLE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Posts scraped: {results['posts_scraped']}")
        logger.info(f"Characters found: {results['characters_found']}")
        logger.info(f"Characters created: {results['characters_created']}")
        logger.info(f"Characters updated: {results['characters_updated']}")
        logger.info(
            f"Processing time: {
                results['processing_time']:.2f} seconds")

        if results.get('errors'):
            logger.warning(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                logger.warning(f"  - {error}")

        return results

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        return None


if __name__ == "__main__":
    main()
