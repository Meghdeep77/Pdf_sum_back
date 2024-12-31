import PyPDF2
import os
import requests
from dotenv import load_dotenv
from nltk.tokenize import sent_tokenize
import nltk

# Load necessary components
nltk.download('punkt')  # Ensure 'punkt' data is downloaded
load_dotenv()  # Load environment variables from .env file

# Get OpenAI API Key from .env file
OPENAI_API_KEY = os.getenv('OPEN_API_KEY')
prompts = {}
prompts['exam_sum'] = "Summarize the following text in order to prepare for an exam, break it down to sub topics and put bullet points under each topic, make sure every topic is covered"
prompts['qp_dup'] = "Make another question paper following the same format and the same level of difficulty for the same subject, keep the ratio of theory to numerical/coding questions the same "
prompts['question'] = "From the following text generate various relevant questions to test the understanding of the student generate 5 MCQ questions, 5 2 mark questions 5 3 mark questions and 5 5 mark questions "
# Function to split text into manageable chunks
def split_text_into_chunks(text, max_tokens=3000):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = len(sentence.split())
        if current_tokens + sentence_tokens <= max_tokens:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_tokens = sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Function to summarize text using OpenAI API endpoint
def summarize_text_with_api(chunk, max_tokens=3000):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an expert summarizer."},
            {"role": "user", "content": f"{prompts['exam_sum']}:\n\n{chunk}"}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "[Error occurred during summarization]"

def generate_questions_with_api(chunk, max_tokens=3000):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an expert question setter for a university exam."},
            {"role": "user", "content": f"{prompts['question']}:\n\n{chunk}"}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return "[Error occurred during summarization]"


def gen_ques_from_pdf(pdf_path, Save_to_txt=False):
    extracted_text = ""

    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                extracted_text += text.strip() if text else "[No text found on this page]\n"

    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None

    # Split text into manageable chunks
    chunks = split_text_into_chunks(extracted_text, max_tokens=3000)

    # Summarize each chunk using OpenAI API
    questions = ""
    for idx, chunk in enumerate(chunks):
        print(f"Summarizing chunk {idx + 1}/{len(chunks)}...")
        questions += generate_questions_with_api(chunk) + "\n"

    # Optionally save the summary to a text file
    if Save_to_txt:
        try:
            output_file = f"{os.path.splitext(pdf_path)[0]}_questions.txt"
            with open(output_file, 'w') as file:
                file.write(questions)
            print(f"Summary has been saved to {output_file}")
        except Exception as e:
            print(f"An error occurred while saving the summary: {e}")

    return questions

def summarize_pdf(pdf_path, Save_to_txt=False):
    extracted_text = ""

    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                extracted_text += text.strip() if text else "[No text found on this page]\n"

    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None

    # Split text into manageable chunks
    chunks = split_text_into_chunks(extracted_text, max_tokens=3000)

    # Summarize each chunk using OpenAI API
    summary = ""
    for idx, chunk in enumerate(chunks):
        print(f"Summarizing chunk {idx + 1}/{len(chunks)}...")
        summary += summarize_text_with_api(chunk) + "\n"

    # Optionally save the summary to a text file
    if Save_to_txt:
        try:
            output_file = f"{os.path.splitext(pdf_path)[0]}_summary.txt"
            with open(output_file, 'w') as file:
                file.write(summary)
            print(f"Summary has been saved to {output_file}")
        except Exception as e:
            print(f"An error occurred while saving the summary: {e}")

    return summary


#pdf_path = "example.pdf"
#summary = summarize_pdf(pdf_path, Save_to_txt=True)
#print("Summary:")
#print(summary)
