# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import nltk
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import google.generativeai as genai
import time
import random

import uvicorn

nltk.download('punkt')  # For sentence tokenization
nltk.download('stopwords') # For stop words removal



app = FastAPI()

origins = ["*"]  # Replace with your frontend's URL for production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


genai.configure(api_key="AIzaSyCCZCy1VvMe_3mkB9HQG0NT7yuMv5Skkg4")
model = genai.GenerativeModel("gemini-1.5-flash")



def analyze_reviews(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        response = session.get(url, headers=headers)
        
        # Optional: Random delay to mimic human behavior
        time.sleep(random.uniform(2, 5))
        
        response.raise_for_status()  # Check for HTTP errors
        soup = BeautifulSoup(response.content, "html.parser")
        soup = BeautifulSoup(response.content, "html.parser")


        # More robust review extraction using a more specific selector 
        reviews_section = soup.find("div", {"id": "cm-cr-dp-review-list"})
        if not reviews_section:
             reviews_section = soup.find("span", {"data-hook": "cr-widget-FocalReviews"})
             if not reviews_section:
                  raise ValueError("No reviews section found on the page.")

        review_elements = reviews_section.find_all("span", {"data-hook": "review-body"})
        reviews = [review.text.strip() for review in review_elements]



        if not reviews:
            raise ValueError("No reviews found within the reviews section.")
        
        review_string = "\n".join(reviews)
        response_gemini= model.generate_content("Give me complete analysis out the product features review, the reviews are : " + review_string)
        
        results = []
        results.append({"text": response_gemini.text, "cluster":0})
        return results

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching URL: {e}")
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")



@app.get("/analyze/")
async def analyze_amazon_product(url: str):

    analysis_results = analyze_reviews(url)
    return analysis_results

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)