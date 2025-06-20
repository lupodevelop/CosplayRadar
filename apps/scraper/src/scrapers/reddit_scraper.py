import os
import praw
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RedditPost:
    id: str
    title: str
    content: str
    author: str
    score: int
    num_comments: int
    created_utc: datetime
    subreddit: str
    url: str
    flair: Optional[str] = None


class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def scrape_subreddit(
            self,
            subreddit_name: str,
            limit: int = 100) -> List[RedditPost]:
        """Scrape posts from a subreddit"""
        posts = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            for submission in subreddit.hot(limit=limit):
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    content=submission.selftext,
                    author=str(
                        submission.author) if submission.author else "[deleted]",
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_utc=datetime.fromtimestamp(
                        submission.created_utc),
                    subreddit=subreddit_name,
                    url=submission.url,
                    flair=submission.link_flair_text)
                posts.append(post)
        except Exception as e:
            print(f"Error scraping subreddit {subreddit_name}: {e}")

        return posts

    def search_posts(
            self,
            query: str,
            subreddit_name: str = None,
            limit: int = 100) -> List[RedditPost]:
        """Search for posts matching a query"""
        posts = []
        try:
            if subreddit_name:
                subreddit = self.reddit.subreddit(subreddit_name)
                submissions = subreddit.search(query, limit=limit)
            else:
                submissions = self.reddit.subreddit(
                    "all").search(query, limit=limit)

            for submission in submissions:
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    content=submission.selftext,
                    author=str(
                        submission.author) if submission.author else "[deleted]",
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_utc=datetime.fromtimestamp(
                        submission.created_utc),
                    subreddit=submission.subreddit.display_name,
                    url=submission.url,
                    flair=submission.link_flair_text)
                posts.append(post)
        except Exception as e:
            print(f"Error searching posts: {e}")

        return posts


def create_reddit_scraper_from_env() -> Optional[RedditScraper]:
    """Create Reddit scraper from environment variables"""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'CosplayRadar/1.0')

    if not client_id or not client_secret:
        print("Reddit credentials not found in environment variables")
        return None

    return RedditScraper(client_id, client_secret, user_agent)
