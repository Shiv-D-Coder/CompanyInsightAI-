import streamlit as st
from utils import scrape_google_news, analyze_sentiment, comparative_analysis, generate_hindi_tts, get_groq_summary, extract_topics
import os
import tempfile

# Configuration for summary length
SUMMARY_LENGTHS = {
    "Short": 150,
    "Medium": 400,
    "Long": 800
}

LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh-cn"
}

def main():
    st.set_page_config(page_title="News Sentiment Analyzer", page_icon="📰")

    # Sidebar
    with st.sidebar:
        st.title("News Sentiment Analyzer 📰")
        
        # API Key Input - moved to top
        st.subheader("API Configuration")
        groq_api_key = st.text_input("Enter Groq API Key (optional):", type="password")
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
            st.success("API key set! ✅")
        
        st.markdown("---")
        
        # Settings section
        st.subheader("Settings")
        selected_length = st.selectbox("Select Summary Length:", list(SUMMARY_LENGTHS.keys()))
        summary_length_words = SUMMARY_LENGTHS[selected_length]
        
        selected_language = st.selectbox("Select Language:", list(LANGUAGE_OPTIONS.keys()))
        language_code = LANGUAGE_OPTIONS[selected_language]
        
        st.markdown("---")
        
        # How it works section
        st.subheader("How it Works:")
        st.write("1. Enter your API key (optional)")
        st.write("2. Enter a company name to analyze")
        st.write("3. The app fetches news articles and analyzes their sentiment")
        st.write("4. A summary is generated in your selected language and provided as audio")
        
        st.markdown("---")
        st.markdown("Made with ❤️ by Shiv Patel")  # Replace with your name

    # Main App
    st.header("Analyze News Sentiment 📊")
    company = st.text_input("Enter Company Name", placeholder="e.g., Tesla")

    if company:
        with st.spinner(f"Fetching and analyzing news about {company}... 🔍"):
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Fetch News
            status_text.text("Fetching news articles...")
            articles = scrape_google_news(company)
            progress_bar.progress(25)
            
            if not articles:
                st.error(f"No news articles found for {company}. Please try another company name.")
                return
                
            # Step 2: Analyze Sentiment and Extract Topics
            status_text.text("Analyzing sentiment and extracting topics...")
            analyzed_articles = []
            for i, article in enumerate(articles):
                article['sentiment'] = analyze_sentiment(article['summary'])
                article['topics'] = extract_topics(f"{article['title']} {article['summary']}")
                analyzed_articles.append(article)
                progress_bar.progress(25 + int(25 * (i+1) / len(articles)))
            
            # Step 3: Generate Analysis
            status_text.text("Generating comparative analysis...")
            analysis = comparative_analysis(analyzed_articles)
            progress_bar.progress(60)
            
            # Step 4: Create Comprehensive Summary
            status_text.text("Creating comprehensive summary...")
            all_articles_text = "\n".join([
                f"Title: {article['title']}\nSummary: {article['summary']}\nSource: {article['source']}\nSentiment: {article['sentiment']}\nTopics: {', '.join(article['topics'])}\n"
                for article in analyzed_articles
            ])
            
            # Pass additional parameters to get_groq_summary
            groq_summary = get_groq_summary(
                all_articles_text,
                language=language_code,
                company_name=company,
                summary_length=summary_length_words
            )
            progress_bar.progress(80)
            
            # Check if we have a valid summary
            if not groq_summary:
                st.warning("⚠️ API-based summarization failed. Using a basic summary instead.")
                
                # Create a basic summary
                total_articles = len(analyzed_articles)
                sentiment_counts = analysis['sentiment_distribution']
                dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "Mixed"
                
                # Extract most common topics
                topic_freq = analysis['topic_overlap']['topic_frequency'] if 'topic_frequency' in analysis['topic_overlap'] else {}
                top_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:3] if topic_freq else []
                top_topics_text = ", ".join([topic for topic, _ in top_topics]) if top_topics else "various topics"
                
                # Basic summary
                groq_summary = f"News analysis for {company} based on {total_articles} recent articles. The overall sentiment is {dominant_sentiment.lower()}, with coverage focusing on {top_topics_text}."
            
            # Step 5: Generate Audio
            status_text.text("Generating audio summary...")
            
            # Use the summary directly without additional instructions
            prompt_for_tts = groq_summary
            
            # Use temp file for audio to avoid permission issues
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                audio_file_path = tmp_file.name
            
            audio_file = generate_hindi_tts(company, prompt_for_tts, language=language_code, filename=audio_file_path)
            progress_bar.progress(100)
            status_text.empty()
            
            # Display results
            st.subheader("📊 Sentiment Analysis Results")
            
            # Display audio if generated successfully
            if audio_file:
                st.subheader(f"🎧 Audio Summary ({selected_language})")
                st.audio(audio_file, format="audio/mp3")
            else:
                st.error(f"Failed to generate {selected_language} audio summary. 😢")
            
            # Display text summary
            st.subheader("📝 Text Summary")
            st.write(groq_summary)
            
            # Display sentiment distribution
            st.subheader("Sentiment Distribution")
            sentiment_data = analysis.get('sentiment_distribution', {})
            
            # Convert to percentages
            total_articles = len(analyzed_articles)
            sentiment_percentages = {
                k: round(v / total_articles * 100, 1) 
                for k, v in sentiment_data.items()
            }
            
            # Create columns for sentiment display
            cols = st.columns(3)
            sentiment_colors = {
                "Positive": "green",
                "Neutral": "blue",
                "Negative": "red"
            }
            
            for i, (sentiment, percentage) in enumerate(sentiment_percentages.items()):
                color = sentiment_colors.get(sentiment, "gray")
                cols[i].metric(
                    label=f"{sentiment} Articles",
                    value=f"{percentage}%",
                    delta=f"{sentiment_data.get(sentiment, 0)} articles"
                )
            
            # Display topic distribution
            if 'topic_overlap' in analysis and 'topic_frequency' in analysis['topic_overlap']:
                st.subheader("Topic Distribution")
                topic_data = analysis['topic_overlap']['topic_frequency']
                
                # Sort topics by frequency
                sorted_topics = sorted(topic_data.items(), key=lambda x: x[1], reverse=True)
                
                # Create bar chart
                topic_names = [topic for topic, _ in sorted_topics]
                topic_counts = [count for _, count in sorted_topics]
                
                st.bar_chart({
                    "Topic": topic_names,
                    "Count": topic_counts
                })
            
            # Display articles in expandable sections
            st.subheader("📰 Articles")
            for i, article in enumerate(analyzed_articles):
                sentiment = article.get('sentiment', 'Unknown')
                color = sentiment_colors.get(sentiment, "gray")
                
                with st.expander(f"📄 {article['title']} ({sentiment})"):
                    st.write(f"**Source:** {article['source']}")
                    st.write(f"**Date:** {article['date']}")
                    st.write(f"**Summary:** {article['summary']}")
                    st.write(f"**Sentiment:** {sentiment}")
                    st.write(f"**Topics:** {', '.join(article.get('topics', ['General']))}")
                    st.markdown(f"[Read full article]({article['link']})")
            
            # Display comparative analysis
            if 'coverage_differences' in analysis and analysis['coverage_differences']:
                st.subheader("Comparative Analysis")
                for comparison in analysis['coverage_differences']:
                    st.write(f"**Comparison:** {comparison.get('comparison', '')}")
                    st.write(f"**Impact:** {comparison.get('impact', '')}")
                    st.markdown("---")
            
            # Cleanup temp file
            try:
                os.unlink(audio_file)
            except:
                pass
                
            # Display JSON
            with st.expander("View Complete Analysis JSON"):
                st.json({
                    "Company": company,
                    "Articles Count": len(analyzed_articles),
                    "Sentiment Distribution": analysis.get('sentiment_distribution', {}),
                    "Topic Distribution": analysis.get('topic_overlap', {}),
                    "Comparative Analysis": analysis.get('coverage_differences', [])
                }, expanded=False)

if __name__ == "__main__":
    main()