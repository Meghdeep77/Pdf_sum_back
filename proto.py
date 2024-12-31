import PyPDF2
from dotenv import load_dotenv
import os
import requests
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline, BartTokenizer

# Load necessary components
nltk.download('punkt')  # Ensure 'punkt' data is downloaded
load_dotenv()  # Load environment variables from .env file

# Get Hugging Face API Key from .env file
HF_API_KEY = os.getenv('HUGGING_API_KEY')
print(HF_API_KEY)

# Define the API URL for Hugging Face's Inference API
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

# Initialize Hugging Face pipeline for summarization (local)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")


# Function to split text efficiently
def split_text_into_chunks(text, max_tokens=1024):
    # Tokenize text into sentences
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        # Tokenize the sentence and count tokens
        tokenized_sentence = tokenizer(sentence, truncation=False, return_tensors="pt")["input_ids"]
        sentence_length = tokenized_sentence.shape[1]  # Number of tokens in the sentence

        # Check if adding this sentence exceeds the max token limit
        if current_tokens + sentence_length <= max_tokens:
            current_chunk.append(sentence)
            current_tokens += sentence_length
        else:
            # Save the current chunk and start a new one
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_tokens = sentence_length

    # Add the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# Function to summarize text using Hugging Face Inference API (remote)
def summarize_text_with_api(text, max_length=500, min_length=300):
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }

    payload = {
        "inputs": text,
        "parameters": {
            "max_length": max_length,  # Maximum length of the summary
            "min_length": min_length,  # Minimum length of the summary
            "do_sample": False         # Use deterministic output
        }
    }

    # Make the API request
    response = requests.post(API_URL, headers=headers, json=payload)

    # Print the response for debugging
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")

    # Check if the request was successful
    if response.status_code == 200:
        summary = response.json()
        return summary[0]['summary_text']
    else:
        print(f"Error: {response.status_code}")
        return f"Error occurred: {response.text}"




# Function to summarize text locally using Hugging Face model (pipeline)
def summarize_text_locally(text, max_length=750, min_length=500):
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']


# Main function to extract, split, and summarize PDF
def summarize_pdf(pdf_path, USE_API=False, Save_to_txt = False):
    extracted_text = ""

    try:
        # Open the PDF file and extract text
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)

            # Extract text from each page
            for page in reader.pages:
                text = page.extract_text()
                extracted_text += text.strip() if text else "[No text found on this page]\n"

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    # Tokenize the extracted text and check if it exceeds the token limit
    print(extracted_text)
    tokens = tokenizer(extracted_text, truncation=False)["input_ids"]
    print(f"Number of tokens: {len(tokens)}")

    if len(tokens) > 1024:
        print("The text exceeds the maximum token limit and needs to be split.")

    # Split text if token count exceeds the limit
    chunks = split_text_into_chunks(extracted_text, max_tokens=1024)

    # Generate summaries for each chunk
    summary = ""
    for idx, chunk in enumerate(chunks):
        print(f"Summarizing chunk {idx + 1}...")

        if USE_API:
            summary += summarize_text_with_api(chunk) + "\n"
        else:
            summary += summarize_text_locally(chunk) + "\n"
    #summary = summarize_text_with_api(summary)
    if Save_to_txt:
        try:
            with open(f"{pdf_file[:-4]}_summary.txt", 'w') as file:
                file.write(summary)
            print(f"Summary has been saved to {pdf_file[:-4]}_summary.txt")
        except Exception as e:
            print(f"An error occurred while saving the summary: {e}")

    return summary


# Example usage
pdf_path = "example.pdf"  # Replace with the path to your PDF

# Set USE_API to True to use the Hugging Face API or False for local model
summary = summarize_pdf(pdf_path, USE_API=True,Save_to_txt=True)  # Set USE_API to False for local summarization
print("Summary:")
print(summary)
