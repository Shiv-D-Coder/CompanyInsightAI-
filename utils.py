import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from gtts import gTTS
import json
import re

# Load environment variables
load_dotenv()

def get_groq_summary(text, fallback=True):
    """Summarize text using Groq API with fallback to local summarization."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY not found in environment variables")
        if fallback:
            return local_summarize(text)
        return None
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()['choices'][0]['message']['content']
        
    except requests.exceptions.RequestException as e:
        print(f"Groq API Error: {e}")
        if fallback:
            print("Using local summarization as fallback")
            return local_summarize(text)
        return None
    except KeyError as e:
        print(f"Groq API Response Error: {e}")
        if fallback:
            return local_summarize(text)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if fallback:
            return local_summarize(text)
        return None

def local_summarize(text, max_sentences=5):
    """Local fallback for summarization when API is unavailable."""
    # Simple extractive summarization
    if not text or len(text) < 100:
        return text
        
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    if len(sentences) <= max_sentences:
        return text
        
    # Calculate sentence importance (using word frequency as a simple metric)
    word_frequencies = {}
    for sentence in sentences:
        for word in sentence.lower().split():
            if word not in word_frequencies:
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1
                
    # Normalize frequencies
    max_frequency = max(word_frequencies.values()) if word_frequencies else 1
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_frequency
        
    # Score sentences
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        for word in sentence.lower().split():
            if word in word_frequencies:
                if i not in sentence_scores:
                    sentence_scores[i] = word_frequencies[word]
                else:
                    sentence_scores[i] += word_frequencies[word]
                    
    # Get top sentences
    summary_sentences_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    summary_sentences_indices = sorted(summary_sentences_indices)  # Preserve original order
    
    # Create summary
    summary = ' '.join([sentences[i] for i in summary_sentences_indices])
    return summary

def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def scrape_google_news(company):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cookie': 'CONSENT=YES+'
    }
    
    url = f"https://news.google.com/rss/search?q={company}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse RSS feed
        soup = BeautifulSoup(response.content, 'xml')
        
        articles = []
        items = soup.find_all('item')
        
        if not items:
            print(f"No items found in RSS feed for {company}, trying alternative parsing method")
            # Alternative parsing method
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('item')
            
        if not items:
            # Try an alternative approach with different RSS feed
            alt_url = f"https://news.google.com/news/rss/search/section/q/{company}/{company}?hl=en&gl=US&ned=us"
            try:
                alt_response = requests.get(alt_url, headers=headers, timeout=10)
                alt_response.raise_for_status()
                alt_soup = BeautifulSoup(alt_response.content, 'xml')
                items = alt_soup.find_all('item')
            except Exception as e:
                print(f"Alternative RSS feed failed: {e}")
                
        if not items:
            print(f"Failed to fetch news for {company}")
            return []
            
        for item in items[:10]:  # Limit to 10 articles
            try:
                title_tag = item.find('title')
                description_tag = item.find('description')
                source_tag = item.find('source')
                link_tag = item.find('link')
                date_tag = item.find('pubDate')
                
                title = title_tag.text if title_tag else "No title"
                summary_text = description_tag.text if description_tag else "No description"
                source = source_tag.text if source_tag else "Unknown source"
                link = link_tag.text if link_tag else "#"
                date = date_tag.text if date_tag else "Unknown date"
                
                cleaned_summary = remove_html_tags(summary_text)
                articles.append({
                    "title": title,
                    "summary": cleaned_summary,
                    "source": source,
                    "link": link,
                    "date": date
                })
            except (AttributeError, TypeError) as e:
                print(f"Error parsing article: {e}")
                continue
                
        return articles
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return []

def analyze_sentiment(text):
    if not text or text.strip() == "":
        return "Neutral"  # Default for empty text
        
    try:
        tb = TextBlob(text)
        vader = SentimentIntensityAnalyzer()
        
        # Hybrid scoring
        final_score = (tb.sentiment.polarity + vader.polarity_scores(text)['compound']) / 2
        return "Positive" if final_score > 0.05 else "Negative" if final_score < -0.05 else "Neutral"
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return "Neutral"  # Default in case of error

def extract_topics(text):
    """Extract basic topics from text."""
    topic_keywords = {
        "Finance": ["finance", "market", "stock", "invest", "financial", "economy", "economic", 
                   "shares", "investors", "trading", "profit", "revenue", "earnings"],
        "Technology": ["tech", "technology", "digital", "software", "hardware", "app", "device", 
                      "innovation", "platform", "product", "AI", "artificial intelligence"],
        "Automotive": ["vehicle", "car", "automotive", "drive", "driving", "EV", "electric vehicle", 
                       "autonomous", "self-driving", "model", "battery", "charging"],
        "Regulation": ["regulation", "regulatory", "compliance", "legal", "law", "lawsuit", 
                       "litigation", "court", "ruling", "guideline", "policy", "policies"],
        "Environment": ["environment", "environmental", "climate", "green", "sustainable", 
                       "sustainability", "carbon", "emission", "renewable", "clean energy"]
    }
    
    found_topics = []
    text_lower = text.lower()
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            found_topics.append(topic)
    
    # Default topic if none found
    if not found_topics:
        found_topics = ["General"]
        
    return found_topics

def comparative_analysis(articles):
    if not articles:
        return {
            "sentiment_distribution": {},
            "topic_overlap": {},
            "coverage_differences": []
        }
        
    analysis = {
        "sentiment_distribution": {},
        "topic_overlap": {},
        "coverage_differences": []
    }
    
    # Sentiment distribution
    sentiment_counts = {}
    for article in articles:
        sentiment = article.get('sentiment', 'Unknown')
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    analysis['sentiment_distribution'] = sentiment_counts
    
    # Extract topics for each article
    all_topics = set()
    article_topics = []
    
    for article in articles:
        title = article.get('title', '')
        summary = article.get('summary', '')
        combined_text = f"{title} {summary}"
        
        topics = extract_topics(combined_text)
        article['topics'] = topics
        article_topics.append(topics)
        all_topics.update(topics)
    
    # Find common topics
    common_topics = set(all_topics)
    for topics in article_topics:
        common_topics = common_topics.intersection(set(topics))
    
    # Create topic overlap analysis
    topic_analysis = {
        "common_topics": list(common_topics) if common_topics else [],
        "all_topics": list(all_topics),
        "topic_frequency": {}
    }
    
    # Calculate topic frequency
    for topic in all_topics:
        count = sum(1 for article_topic in article_topics if topic in article_topic)
        topic_analysis["topic_frequency"][topic] = count
    
    analysis['topic_overlap'] = topic_analysis
    
    # Generate coverage differences
    if len(articles) >= 2:
        # Compare articles with different sentiments
        sentiments = set(article.get('sentiment', 'Unknown') for article in articles)
        if len(sentiments) >= 2:
            pos_articles = [a for a in articles if a.get('sentiment') == 'Positive']
            neg_articles = [a for a in articles if a.get('sentiment') == 'Negative']
            neu_articles = [a for a in articles if a.get('sentiment') == 'Neutral']
            
            # Generate comparisons
            comparisons = []
            
            if pos_articles and neg_articles:
                pos_topics = set()
                for a in pos_articles:
                    pos_topics.update(a.get('topics', []))
                    
                neg_topics = set()
                for a in neg_articles:
                    neg_topics.update(a.get('topics', []))
                
                pos_unique = pos_topics - neg_topics
                neg_unique = neg_topics - pos_topics
                
                comparison = {
                    "comparison": f"Positive articles focus on {', '.join(pos_unique) if pos_unique else 'various topics'}, while negative articles focus on {', '.join(neg_unique) if neg_unique else 'various topics'}.",
                    "impact": "This contrast shows different aspects of the company's public perception."
                }
                comparisons.append(comparison)
            
            # Add overall sentiment trend
            if sentiment_counts:
                max_sentiment = max(sentiment_counts, key=sentiment_counts.get)
                comparison = {
                    "comparison": f"Overall coverage is predominantly {max_sentiment.lower()}.",
                    "impact": f"The {max_sentiment.lower()} sentiment suggests {'a positive public perception' if max_sentiment == 'Positive' else 'a negative public perception' if max_sentiment == 'Negative' else 'a balanced public perception'}."
                }
                comparisons.append(comparison)
                
            analysis['coverage_differences'] = comparisons
    
    return analysis

def generate_hindi_tts(company_name, text, language="hi", filename="output.mp3"):
    """Convert text to speech in specified language with local fallback.
    
    Args:
        company_name (str): Name of the company for the summary
        text (str): Text to convert to speech or to summarize first
        language (str): Language code for TTS (default: "hi" for Hindi)
        filename (str): Output filename for the audio file
        
    Returns:
        str: Path to the audio file if successful, None otherwise
    """
    try:
        # For non-English languages, handle translation locally if API fails
        if language != "en":
            language_names = {
                "hi": "Hindi",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "zh-cn": "Chinese"
            }
            
            language_name = language_names.get(language, language)
            
            # Create prompt for translation and summarization
            prompt = f"Translate and summarize the following text about {company_name} to {language_name}. Keep the main points and key insights:\n\n{text}"
            
            # Try to get translated summary
            translated_text = get_groq_summary(prompt)
            
            if not translated_text:
                # If translation fails, just use a simple message in the target language
                if language == "hi":
                    translated_text = f"{company_name} के बारे में समाचार सारांश। यह एक स्थानीय रूप से उत्पन्न संदेश है क्योंकि अनुवाद API उपलब्ध नहीं थी।"
                elif language == "es":
                    translated_text = f"Resumen de noticias sobre {company_name}. Este es un mensaje generado localmente porque la API de traducción no estaba disponible."
                elif language == "fr":
                    translated_text = f"Résumé des nouvelles sur {company_name}. Il s'agit d'un message généré localement car l'API de traduction n'était pas disponible."
                elif language == "de":
                    translated_text = f"Nachrichtenzusammenfassung über {company_name}. Dies ist eine lokal generierte Nachricht, da die Übersetzungs-API nicht verfügbar war."
                elif language == "zh-cn":
                    translated_text = f"关于{company_name}的新闻摘要。这是一条本地生成的消息，因为翻译API不可用。"
                else:
                    # Default to English if language not supported
                    translated_text = f"News summary about {company_name}. This is a locally generated message as the translation API was not available."
                
            # Use the translated text for TTS
            tts_text = translated_text
        else:
            # For English, use the original text
            tts_text = text
        
        # Generate TTS
        tts = gTTS(text=tts_text, lang=language)
        tts.save(filename)
        return filename
        
    except Exception as e:
        print(f"TTS generation error: {e}")
        return None