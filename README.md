# DragonHacks2025
# rInsight

**Empowering Drexel Counselors with Reddit-Driven Mental Health Insights**

rInsight is a web application that analyzes live r/Drexel posts from Reddit to provide real-time mental health insights for Drexel University counselors. Built for DragonHacks 2025, it uses the Reddit API and Gemini AI to calculate stress scores, identify key concerns (e.g., housing, academics), and recommend campus resources.

![rInsight Dashboard]([path/to/screenshot.png](https://devpost.com/software/xyz-bx5d04))  
*Dashboard showing live stress scores with animated gauges and gradient text.*

## Features

- **Live Data Analysis**: Fetches r/Drexel posts in real time using the Reddit API.
- **Gemini AI Integration**: Performs sentiment analysis (scores from -1 to 1) and keyword extraction to identify stress-related terms.
- **Stress Score Calculation**:
  \[
  \text{Stress Score} = 100 - \left( 0.4 \cdot (1 - \text{Sentiment}) + 0.3 \cdot \text{Keyword Frequency} + 0.2 \cdot \text{Engagement} + 0.1 \cdot \text{Academic Stress Peak} \right) \times 100
  \]
  - **Interpretation**: < 50: Critical (e.g., 17); 50–70: Moderate; > 70: Low.
- **Visualizations**: Animated gauges, trend graphs, and bar charts using Chart.js.
- **Actionable Recommendations**: Links to Drexel resources like the [Counseling Center](https://drexel.edu/counselingandhealth/counseling-center).
- **Polished UI/UX**: Features gradient text, hover animations, and card-based design with TailwindCSS.

## Tech Stack

- **Frontend**: React, Chart.js, Flatpickr, TailwindCSS, HTML/CSS
- **Backend**: Flask (Python)
- **APIs**: Reddit API (live), Gemini AI (live for sentiment analysis and keyword extraction)
- **Tools**: Babel (JSX transpilation), local development server

## Prerequisites

- Python 3.8+
- Node.js (for React transpilation, though we use CDN for simplicity)
- Reddit API credentials (client ID, secret, etc.)
- Gemini AI API key
- Internet connection (for live API calls and CDN dependencies)

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/rInsight.git
   cd rInsight
