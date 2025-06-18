import os
import base64
import json
import re
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from PIL import Image
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found in .env file")
    raise ValueError("GOOGLE_API_KEY not found in .env file")
if not GEMINI_MODEL:
    logger.error("GEMINI_MODEL not found in .env file")
    raise ValueError("GEMINI_MODEL not found in .env file")

app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2
)

prompt_template = PromptTemplate(
    input_variables=["image_description"],
    template=""" 
        You are an expert image analyst tasked with identifying real-world issues in images for a government reporting app. Analyze the provided image description and identify any potential problems or issues present in the image, such as safety hazards, infrastructure damage, or environmental concerns. 
        Return a JSON object with exactly three fields:
        - "problems": an array of strings listing identified problems (e.g., "broken lock on door", "pothole in road", "leaking pipe").
        - "problem_types": an array of strings categorizing each problem (e.g., "security", "infrastructure", "safety", "environmental", "maintenance").
        - "suggestions": an array of strings with practical suggestions to address each problem, in the same order (e.g., "Replace the lock", "Report to local authorities for repair").
        If no problems are found, return empty arrays for all fields.

        **Instructions**:
        - Output ONLY valid JSON.
        - Do NOT include markdown, code blocks, or any text outside the JSON object.
        - Ensure the JSON object contains exactly three fields: "problems", "problem_types", and "suggestions".
        - Each problem must have a corresponding problem type and suggestion at the same index.
        - Use concise, standard terms for problem types relevant to government or public reporting.


        Example output:
        {{
          "problems": [
            "كالون الباب مكسور",
            "رصيف مكسر",
            "صندوق زبالة مليان على آخره"
          ],
          "problem_types": [
            "أمان",
            "بنية تحتية",
            "صيانة"
          ],
          "suggestions": [
            "غيّر الكالون وبلّغ إدارة المبنى",
            "بلّغ الحي عشان يصلّحوا الرصيف",
            "اطلب ييجوا يلمّوا الزبالة أكتر"
          ]
        }}
        
        \n
        
        Image description: {image_description}
        
        \n

        Response in Egyptian Arabic dialect
    """
)

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    logger.info(f"Received upload request for file: {file.filename}")
    try:
        # Validate file
        if not file.content_type.startswith("image/"):
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        contents = await file.read()
        logger.info(f"Read {len(contents)} bytes from file")
        if len(contents) > 5 * 1024 * 1024:
            logger.warning("File size exceeds 5MB")
            raise HTTPException(status_code=400, detail="Image size must be less than 5MB")

        # Process image
        logger.info("Processing image")
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        logger.info("Image converted to base64")

        # Gemini description
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Describe this image in detail."},
                {"type": "image_url", "image_url": f"data:image/png;base64,{img_base64}"}
            ]
        )
        logger.info("Invoking Gemini for description")
        try:
            description = llm.invoke([message]).content
            logger.info("Received description")
        except Exception as e:
            logger.error(f"Gemini description failed: {str(e)}")
            return JSONResponse(content={"problems": [], "problem_types": [], "suggestions": []})

        # Analyze description
        chain = prompt_template | llm
        logger.info("Analyzing description")
        try:
            result = chain.invoke({"image_description": description})
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return JSONResponse(content={"problems": [], "problem_types": [], "suggestions": []})

        # Parse JSON
        try:
            cleaned_output = result.content.strip()
            cleaned_output = re.sub(r'^```json\s*|\s*```$', '', cleaned_output, flags=re.MULTILINE)
            output = json.loads(cleaned_output)
            if not isinstance(output, dict) or set(output.keys()) != {"problems", "problem_types", "suggestions"}:
                logger.warning("Invalid JSON structure")
                raise ValueError("Invalid JSON structure")
            if not (isinstance(output["problems"], list) and isinstance(output["problem_types"], list) and isinstance(output["suggestions"], list)):
                logger.warning("Problems, problem_types, or suggestions not arrays")
                raise ValueError("Problems, project_types, and suggestions must be arrays")
            logger.info("Successfully parsed JSON")
            return JSONResponse(content=output)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            return JSONResponse(content={"problems": [], "problem_types": [], "suggestions": []})

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(content={"problems": [], "problem_types": [], "suggestions": []})
