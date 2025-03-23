from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from utils import scrape_google_news, analyze_sentiment, comparative_analysis, get_groq_summary, extract_topics
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Check for required API keys
if not os.getenv("GROQ_API_KEY"):
    print("Warning: GROQ_API_KEY not found in environment variables. Local fallbacks will be used.")

# FastAPI app
app = FastAPI(
    title="News Sentiment Analysis API",
    description="API for analyzing sentiment of news articles related to a company",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Models
class NewsAnalysisRequest(BaseModel):
    company: str
    language: Optional[str] = "en"
    summary_length: Optional[int] = 400

class Topic(BaseModel):
    name: str
    count: int

class Article(BaseModel):
    title: str
    summary: str
    source: str
    link: str
    date: str
    sentiment: str
    topics: List[str]

class ComparisonItem(BaseModel):
    comparison: str
    impact: str

class TopicOverlap(BaseModel):
    common_topics: List[str]
    all_topics: List[str]
    topic_frequency: Dict[str, int]

class ComparativeAnalysisResult(BaseModel):
    sentiment_distribution: Dict[str, int]
    topic_overlap: TopicOverlap
    coverage_differences: List[ComparisonItem]

class NewsAnalysisResponse(BaseModel):
    company: str
    articles: List[Article]
    comparative_analysis: ComparativeAnalysisResult
    comprehensive_summary: str

# Dependency for API key validation
async def verify_api_key(x_api_key: str = None):
    # Optional API key check - you might want to implement this for production
    # If you implement this, uncomment the code below
    
    # if not x_api_key or x_api_key != os.getenv("API_SECRET_KEY"):
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the News Sentiment Analysis API"}

@app.post("/analyze", response_model=NewsAnalysisResponse)
async def analyze_news(request: NewsAnalysisRequest, authorized: bool = Depends(verify_api_key)):
    try:
        # Validate company name
        if not request.company or len(request.company.strip()) == 0:
            raise HTTPException(status_code=400, detail="Company name is required")
            
        # Scrape news articles
        articles = scrape_google_news(request.company)
        
        if not articles:
            raise HTTPException(status_code=404, detail=f"No news articles found for {request.company}")
            
        # Analyze sentiment and extract topics for each article
        analyzed_articles = []
        for article in articles:
            article['sentiment'] = analyze_sentiment(article['summary'])
            article['topics'] = extract_topics(f"{article['title']} {article['summary']}")
            analyzed_articles.append(article)
            
        # Generate comparative analysis
        analysis = comparative_analysis(analyzed_articles)
        
        # Create comprehensive summary
        all_articles_text = "\n".join([
            f"Title: {article['title']}\nSummary: {article['summary']}\nSource: {article['source']}\nSentiment: {article['sentiment']}\nTopics: {', '.join(article['topics'])}\n"
            for article in analyzed_articles
        ])
        
        summary_prompt = f"Summarize the following news articles about {request.company} in approximately {request.summary_length} words. Focus on the overall sentiment and key topics:\n{all_articles_text}"
        comprehensive_summary = get_groq_summary(summary_prompt)
        
        if not comprehensive_summary:
            # Fallback to a basic summary if API fails
            total_articles = len(analyzed_articles)
            sentiment_counts = analysis['sentiment_distribution']
            dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "Mixed"
            
            # Extract most common topics
            topic_freq = analysis['topic_overlap']['topic_frequency'] if 'topic_frequency' in analysis['topic_overlap'] else {}
            top_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:3] if topic_freq else []
            top_topics_text = ", ".join([topic for topic, _ in top_topics]) if top_topics else "various topics"
            
            # Basic summary
            comprehensive_summary = f"News analysis for {request.company} based on {total_articles} recent articles. The overall sentiment is {dominant_sentiment.lower()}, with coverage focusing on {top_topics_text}."
            
        # Return response
        return {
            "company": request.company,
            "articles": analyzed_articles,
            "comparative_analysis": analysis,
            "comprehensive_summary":