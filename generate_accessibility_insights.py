#
# A script to generate accessibility insights for data visualizations using Gemini 2.5 Flash.
# It processes PNG images from a 'screenshots' folder, extracts question-answer pairs
# relevant to users with visual impairments, and saves them to a JSON file.
#

import os
import json
import time
import pathlib
from typing import List

# Pydantic is used for defining the strict output schema for the LLM
from pydantic import BaseModel, Field

# Google Generative AI libraries for interacting with the Gemini API
import google
from google import genai
from google.genai.types import GenerateContentResponse, Part, GenerateContentConfig

# Other utilities
from dotenv import load_dotenv
from tqdm import tqdm


# --- Pydantic Models for Structured Output ---

class A11yQA(BaseModel):
    """A single question and answer pair focusing on accessibility."""
    question: str = Field(
        ...,
        description="A question a user with visual impairments (e.g., using a screen reader) might have about the data visualization."
    )
    answer: str = Field(
        ...,
        description="A concise, data-driven answer that describes the visual trend, pattern, or relationship shown in the chart."
    )

class A11yInsights(BaseModel):
    """The root object for the LLM's response, containing a list of Q&A pairs."""
    insights: List[A11yQA] = Field(
        ...,
        description="A list of question-and-answer pairs that provide accessibility insights for the data visualization."
    )


# --- Robust LLM Querying Function ---

def query_llm_with_retries(
    client: genai.Client,
    prompt: str,
    image_bytes: bytes,
    response_format: BaseModel,
    model_name: str,
    max_retries: int = 5
) -> dict | None:
    """
    Queries Gemini with an image and a prompt, handling retries and errors.
    Returns parsed JSON from the model's response or None on failure.
    """
    for attempt in range(max_retries):
        try:
            # The 'contents' must include the image bytes and a simple instruction.
            # The detailed instructions are in the 'system_instruction' prompt.
            contents = [
                Part.from_bytes(data=image_bytes, mime_type='image/png'),
                "Analyze this data visualization for accessibility."
            ]
            
            # Generate content using the provided image, prompt, and response schema
            response: GenerateContentResponse = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=GenerateContentConfig(
                    system_instruction=prompt,
                    response_mime_type='application/json',
                    response_schema=response_format
                )
            )
            # The response text is a JSON string that needs to be parsed
            return json.loads(response.text)

        except (google.genai.errors.ServerError) as e:
            print(f"API error: {e}")
            if attempt < max_retries - 1:
                sleep_duration = (2 ** attempt) * 2  # Exponential backoff
                print(f"Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print("Max retries reached. Returning None.")
                return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}. Response text: {response.text}")
            if attempt < max_retries - 1:
                sleep_duration = (2 ** attempt) * 2
                print(f"Retrying in {sleep_duration} seconds...")
                time.sleep(sleep_duration)
            else:
                print("Max retries reached due to persistent decoding errors. Returning None.")
                return None
    return None


# --- Main Orchestration Function ---

def generate_insights():
    """
    Main function to orchestrate the process of generating accessibility insights.
    """
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")
    
    # Configure the Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Define paths
    screenshot_folder = pathlib.Path('screenshots')
    output_path = pathlib.Path('html/aiInsights.json')

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(exist_ok=True)

    # --- System Prompt ---
    # This prompt guides the LLM to perform the specific task required.
    system_prompt = """
You are an expert in data visualization and web accessibility. Your task is to analyze the provided image of a data visualization (e.g., a chart or graph) and generate a list of question-and-answer pairs.

These pairs should anticipate questions a user relying on assistive technology (like a screen reader) might have. Focus on extracting insights that require visual interpretation and cannot be understood by reading a simple data table.

Key areas to focus on:
- **Trends:** What is the overall trend shown in the data over time or across categories? (e.g., "Is there a general upward or downward trend?")
- **Relationships:** How do different data series relate to each other? (e.g., "Does variable A increase when variable B decreases?")
- **Comparisons:** Which categories have the highest or lowest values? How significant are the differences?
- **Outliers:** Are there any data points that deviate significantly from the general pattern?
- **Patterns:** Is there a cyclical or seasonal pattern in the data?

CRITICAL: Do not just read out data points. Provide high-level, synthesized answers that describe the visual story of the chart. Strictly adhere to the provided JSON schema for your response.
    """

    # --- Load Existing Data for Idempotency ---
    all_insights = {}
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                all_insights = json.load(f)
            print(f"Loaded {len(all_insights)} existing insights from {output_path}")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing file at {output_path}. Starting fresh.")

    # --- Process Images ---
    image_paths = list(screenshot_folder.glob('*.png'))
    if not image_paths:
        print(f"No PNG images found in the '{screenshot_folder}' directory. Exiting.")
        return

    print(f"\nFound {len(image_paths)} images to process.")
    for image_path in tqdm(image_paths, desc="Processing Images"):
        # The key for the JSON output is the filename without the extension
        image_key = image_path.stem

        # Skip if this image has already been processed
        if image_key in all_insights:
            continue

        print(f"\nProcessing new image: {image_path.name}")
        
        # Read the image file in binary mode
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        # Call the LLM with the image and prompt
        response_data = query_llm_with_retries(
            client=client,
            prompt=system_prompt,
            image_bytes=image_bytes,
            response_format=A11yInsights,
            model_name="gemini-2.5-flash",
        )

        if response_data and 'insights' in response_data:
            # The Pydantic model ensures the 'insights' key exists and is a list
            all_insights[image_key] = response_data['insights']
            print(f"Successfully extracted {len(response_data['insights'])} Q&A pairs for {image_key}.")
        else:
            print(f"Failed to extract insights for {image_key} after all retries.")
            # Optionally, add a placeholder to prevent reprocessing failed images
            all_insights[image_key] = [] 
    
    # --- Save Results ---
    with open(output_path, 'w') as f:
        json.dump(all_insights, f, indent=4)
    
    print(f"\nSuccessfully saved all insights to {output_path}")


if __name__ == "__main__":
    generate_insights()
