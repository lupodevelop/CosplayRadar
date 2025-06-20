"""
Character Extractor Module
Extracts character names from Reddit posts using NLP and regex patterns
"""

import re
import logging
from typing import List, Dict, Any, Set

try:
    import spacy
except ImportError:
    spacy = None

import nltk
from nltk.corpus import words
from nltk.tokenize import word_tokenize

logger = logging.getLogger(__name__)


class CharacterExtractor:
    def __init__(self):
        """Initialize the character extractor with NLP models"""
        self.nlp = None
        self.word_list = set()
        self.anime_characters = self._load_anime_characters()
        self.game_characters = self._load_game_characters()
        self.common_cosplay_terms = {
            'cosplay',
            'costume',
            'character',
            'anime',
            'manga',
            'game',
            'series',
            'outfit',
            'wig',
            'props',
            'makeup',
            'photoshoot',
            'convention',
            'con'}

        # Initialize spaCy if available
        if spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy English model")
            except OSError:
                logger.warning(
                    "spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None

        # Initialize NLTK
        try:
            nltk.data.find('corpora/words')
            self.word_list = set(words.words())
        except LookupError:
            logger.warning("NLTK words corpus not found. Installing...")
            nltk.download('words', quiet=True)
            self.word_list = set(words.words())

    def _load_anime_characters(self) -> Set[str]:
        """Load known anime character names"""
        # Popular anime characters (expanded list)
        return {
            'nezuko', 'nezuko kamado', 'tanjiro', 'tanjiro kamado', 'zenitsu', 'inosuke',
            'naruto', 'naruto uzumaki', 'sasuke', 'sasuke uchiha', 'sakura', 'kakashi',
            'luffy', 'monkey d luffy', 'zoro', 'roronoa zoro', 'nami', 'sanji', 'chopper',
            'goku', 'son goku', 'vegeta', 'gohan', 'piccolo', 'frieza',
            'ichigo', 'ichigo kurosaki', 'rukia', 'orihime', 'uryu', 'renji',
            'edward elric', 'alphonse elric', 'roy mustang', 'winry',
            'light yagami', 'ryuk', 'l lawliet', 'misa',
            'natsu', 'natsu dragneel', 'lucy', 'lucy heartfilia', 'erza', 'gray',
            'rimuru', 'rimuru tempest', 'milim', 'shion', 'benimaru',
            'tatsumaki', 'saitama', 'genos', 'fubuki', 'king',
            'senku', 'senku ishigami', 'kohaku', 'chrome', 'tsukasa',
            'mob', 'shigeo kageyama', 'reigen', 'dimple', 'ritsu',
            'tohru', 'kobayashi', 'kanna', 'elma', 'lucoa',
            'miku', 'hatsune miku', 'rin', 'kagamine rin', 'len', 'kagamine len',
            'rem', 'ram', 'emilia', 'subaru', 'beatrice', 'puck',
            'ainz', 'ainz ooal gown', 'albedo', 'shalltear', 'cocytus',
            'kirito', 'asuna', 'sinon', 'alice', 'eugeo', 'klein',
            'shinji', 'shinji ikari', 'rei', 'rei ayanami', 'asuka', 'gendo',
            'jotaro', 'jotaro kujo', 'dio', 'joseph', 'josuke', 'giorno',
            'deku', 'izuku midoriya', 'bakugo', 'todoroki', 'uraraka', 'iida',
            'power', 'denji', 'makima', 'aki', 'kobeni', 'angel devil'
        }

    def _load_game_characters(self) -> Set[str]:
        """Load known game character names"""
        return {
            'mario', 'luigi', 'peach', 'princess peach', 'bowser', 'yoshi',
            'link', 'zelda', 'princess zelda', 'ganondorf', 'samus', 'pikachu',
            'pokemon', 'ash', 'ash ketchum', 'misty', 'brock',
            'kratos', 'atreus', 'freya', 'baldur', 'thor',
            'geralt', 'ciri', 'yennefer', 'triss', 'dandelion',
            'cloud', 'cloud strife', 'tifa', 'aerith', 'sephiroth', 'barret',
            'master chief', 'cortana', 'arbiter', 'johnson',
            'lara croft', 'nathan drake', 'elena', 'sully',
            'aloy', 'rost', 'erend', 'varl', 'nil',
            'arthur morgan', 'john marston', 'dutch', 'micah',
            'joel', 'ellie', 'tommy', 'maria', 'abby',
            'spider-man', 'spiderman', 'peter parker', 'miles morales',
            'batman', 'superman', 'wonder woman', 'flash', 'aquaman',
            'tracer', 'dva', 'mercy', 'genji', 'reaper', 'widowmaker',
            'ryu', 'chun-li', 'ken', 'cammy', 'zangief', 'dhalsim',
            'sonic', 'tails', 'knuckles', 'shadow', 'amy', 'eggman'
        }

    def extract_characters_from_text(
            self, text: str, post_url: str = "") -> List[Dict[str, Any]]:
        """Extract potential character names from text"""
        if not text:
            return []

        text = text.lower().strip()
        characters = []

        # Method 1: Direct known character matching
        characters.extend(self._extract_known_characters(text, post_url))

        # Method 2: NER with spaCy (if available)
        if self.nlp:
            characters.extend(self._extract_with_spacy(text, post_url))

        # Method 3: Pattern-based extraction
        characters.extend(self._extract_with_patterns(text, post_url))

        # Method 4: Context-based extraction
        characters.extend(self._extract_with_context(text, post_url))

        # Remove duplicates and return
        unique_characters = {}
        for char in characters:
            name_key = char['name'].lower()
            if name_key not in unique_characters:
                unique_characters[name_key] = char
            else:
                # Merge confidence scores
                existing = unique_characters[name_key]
                existing['confidence'] = max(
                    existing['confidence'], char['confidence'])
                if char.get('series') and not existing.get('series'):
                    existing['series'] = char['series']
                if char.get('fandom') and not existing.get('fandom'):
                    existing['fandom'] = char['fandom']

        return list(unique_characters.values())

    def _extract_known_characters(
            self, text: str, post_url: str) -> List[Dict[str, Any]]:
        """Extract characters from known character lists"""
        characters = []

        # Check anime characters
        for char_name in self.anime_characters:
            if char_name in text:
                characters.append({
                    'name': char_name.title(),
                    'confidence': 0.9,
                    'fandom': 'Anime',
                    'source_url': post_url,
                    'extraction_method': 'known_anime'
                })

        # Check game characters
        for char_name in self.game_characters:
            if char_name in text:
                characters.append({
                    'name': char_name.title(),
                    'confidence': 0.9,
                    'fandom': 'Game',
                    'source_url': post_url,
                    'extraction_method': 'known_game'
                })

        return characters

    def _extract_with_spacy(
            self, text: str, post_url: str) -> List[Dict[str, Any]]:
        """Extract characters using spaCy NER"""
        if not self.nlp:
            return []

        characters = []
        doc = self.nlp(text)

        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'CHARACTER']:
                name = ent.text.strip()
                if len(name) > 1 and name.lower(
                ) not in self.common_cosplay_terms:
                    confidence = 0.7 if ent.label_ == 'CHARACTER' else 0.6
                    characters.append({
                        'name': name.title(),
                        'confidence': confidence,
                        'source_url': post_url,
                        'extraction_method': 'spacy_ner'
                    })

        return characters

    def _extract_with_patterns(
            self, text: str, post_url: str) -> List[Dict[str, Any]]:
        """Extract characters using regex patterns"""
        characters = []

        # Pattern for "cosplaying as X" or "X cosplay"
        patterns = [
            r'cosplaying\s+as\s+([A-Za-z][A-Za-z\s]+?)(?:\s|$|[,.\!])',
            r'([A-Za-z][A-Za-z\s]+?)\s+cosplay',
            r'my\s+([A-Za-z][A-Za-z\s]+?)\s+costume',
            r'dressed\s+as\s+([A-Za-z][A-Za-z\s]+?)(?:\s|$|[,.\!])',
            r'([A-Za-z][A-Za-z\s]+?)\s+from\s+([A-Za-z][A-Za-z\s]+)',
            r'character:\s*([A-Za-z][A-Za-z\s]+?)(?:\s|$|[,.\!])',
            r'character\s+is\s+([A-Za-z][A-Za-z\s]+?)(?:\s|$|[,.\!])'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                series = match.group(2).strip() if len(
                    match.groups()) > 1 else None

                if (len(name) > 1 and
                    name.lower() not in self.common_cosplay_terms and
                        not name.lower() in self.word_list):

                    char_data = {
                        'name': name.title(),
                        'confidence': 0.8,
                        'source_url': post_url,
                        'extraction_method': 'pattern_matching'
                    }

                    if series:
                        char_data['series'] = series.title()
                        char_data['fandom'] = self._classify_fandom(series)

                    characters.append(char_data)

        return characters

    def _extract_with_context(
            self, text: str, post_url: str) -> List[Dict[str, Any]]:
        """Extract characters using context analysis"""
        characters = []

        # Look for capitalized words near cosplay terms
        words = word_tokenize(text)
        cosplay_indices = []

        for i, word in enumerate(words):
            if word.lower() in self.common_cosplay_terms:
                cosplay_indices.append(i)

        for idx in cosplay_indices:
            # Check words within 5 positions of cosplay terms
            start = max(0, idx - 5)
            end = min(len(words), idx + 5)

            for i in range(start, end):
                word = words[i]
                if (word.istitle() and
                    len(word) > 2 and
                    word.lower() not in self.common_cosplay_terms and
                        word.lower() not in self.word_list):

                    characters.append({
                        'name': word,
                        'confidence': 0.5,
                        'source_url': post_url,
                        'extraction_method': 'context_analysis'
                    })

        return characters

    def _classify_fandom(self, series_name: str) -> str:
        """Classify the fandom type based on series name"""
        series_lower = series_name.lower()

        anime_keywords = [
            'anime',
            'manga',
            'naruto',
            'dragon ball',
            'one piece',
            'demon slayer',
            'attack on titan']
        game_keywords = [
            'game',
            'mario',
            'zelda',
            'pokemon',
            'final fantasy',
            'overwatch',
            'league of legends']
        movie_keywords = [
            'movie',
            'film',
            'marvel',
            'dc',
            'star wars',
            'harry potter',
            'lord of the rings']

        for keyword in anime_keywords:
            if keyword in series_lower:
                return 'Anime'

        for keyword in game_keywords:
            if keyword in series_lower:
                return 'Game'

        for keyword in movie_keywords:
            if keyword in series_lower:
                return 'Movie'

        return 'Other'

    def calculate_character_score(
            self, character_data: Dict[str, Any], post_metrics: Dict[str, Any]) -> float:
        """Calculate popularity score for a character based on various factors"""
        base_score = character_data.get('confidence', 0.5)

        # Post engagement score (upvotes, comments)
        upvotes = post_metrics.get('upvotes', 0)
        comments = post_metrics.get('comments', 0)

        engagement_score = min(1.0, (upvotes + comments * 2) / 1000)

        # Extraction method bonus
        method_bonus = {
            'known_anime': 0.3,
            'known_game': 0.3,
            'pattern_matching': 0.2,
            'spacy_ner': 0.1,
            'context_analysis': 0.0
        }.get(character_data.get('extraction_method', ''), 0.0)

        final_score = (base_score * 0.4 + engagement_score *
                       0.5 + method_bonus * 0.1) * 100

        return min(100.0, max(0.0, final_score))
