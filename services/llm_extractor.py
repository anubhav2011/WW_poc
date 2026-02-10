import json
import os
import re
from typing import Optional, Dict
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


def normalize_date_format(date_str: str) -> str:
    """
    Normalize various date formats to DD-MM-YYYY.
    
    Handles:
    - DD/MM/YYYY -> DD-MM-YYYY
    - DD.MM.YYYY -> DD-MM-YYYY
    - YYYY-MM-DD -> DD-MM-YYYY
    - D-M-YYYY -> DD-MM-YYYY (add leading zeros)
    """
    if not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    # Replace common separators with hyphen
    date_str = date_str.replace('/', '-').replace('.', '-').replace(' ', '-')
    
    # Split by hyphen
    parts = date_str.split('-')
    
    if len(parts) != 3:
        return date_str  # Return as-is if format is unexpected
    
    # Check if format is YYYY-MM-DD
    if len(parts[0]) == 4 and parts[0].isdigit():
        # YYYY-MM-DD -> DD-MM-YYYY
        year, month, day = parts
        return f"{day.zfill(2)}-{month.zfill(2)}-{year}"
    
    # Assume DD-MM-YYYY format
    day, month, year = parts
    
    # Add leading zeros if needed
    day = day.zfill(2)
    month = month.zfill(2)
    
    # Handle 2-digit year (e.g., 87 -> 1987)
    if len(year) == 2:
        year_int = int(year)
        # Assume 1900s for years > 50, 2000s for years <= 50
        year = f"19{year}" if year_int > 50 else f"20{year}"
    
    return f"{day}-{month}-{year}"


def call_llm_with_retry(prompt: str, system_prompt: str, max_retries: int = 3) -> Optional[Dict]:
    """
    Call OpenAI API with retry logic and JSON parsing.
    
    Args:
        prompt: User prompt with instructions
        system_prompt: System role instructions
        max_retries: Maximum retry attempts
        
    Returns:
        Parsed JSON dict or None if failed
    """
    if not openai_client:
        logger.error("OpenAI API key not set. Cannot extract data with LLM.")
        return None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM extraction attempt {attempt + 1}/{max_retries}")
            
            response = openai_client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"LLM response received: {len(content)} characters")
            
            # Remove markdown code blocks if present
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            content = content.strip()
            
            # Parse JSON
            try:
                data = json.loads(content)
                logger.info(f"Successfully parsed JSON response: {list(data.keys())}")
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                logger.warning(f"Response content: {content[:500]}")
                
                # Try to extract JSON from text if it's embedded
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        logger.info("Successfully extracted JSON from response text")
                        return data
                    except json.JSONDecodeError:
                        pass
                
                if attempt < max_retries - 1:
                    logger.info("Retrying LLM call...")
                    continue
                else:
                    logger.error(f"Failed to parse JSON after {max_retries} attempts")
                    return None
                    
        except Exception as e:
            logger.error(f"LLM API call error on attempt {attempt + 1}: {str(e)}", exc_info=True)
            if attempt < max_retries - 1:
                logger.info("Retrying LLM call...")
                continue
            else:
                logger.error(f"LLM API call failed after {max_retries} attempts")
                return None
    
    return None


def extract_personal_data_llm(raw_ocr_text: str) -> Optional[Dict]:
    """
    Extract structured personal document data using LLM.
    
    Args:
        raw_ocr_text: Complete OCR text from personal document (Aadhaar, PAN, etc.)
        
    Returns:
        Dict with extracted data:
        {
            "name": "BABU KHAN",
            "dob": "01-12-1987",
            "address": "KAMLA RAMAN NAGAR...",
            "mobile": "7905285898"
        }
    """
    logger.info("=== Starting LLM extraction for PERSONAL document ===")
    logger.info(f"OCR text length: {len(raw_ocr_text)} characters")
    
    system_prompt = """You are an expert data extraction assistant specializing in Indian identity documents (Aadhaar, PAN Card, Voter ID, etc.).

Your task is to extract structured information from OCR text and return ONLY a valid JSON object. Do not include any explanations or markdown formatting."""

    user_prompt = f"""Extract the following information from this personal identity document OCR text:

Required fields:
- name: Full name of the person (as printed on document)
- dob: Date of birth in DD-MM-YYYY format (extract and convert if needed)
- address: Complete address as printed on document
- mobile: Mobile number (if present on document, otherwise null)

Important instructions:
1. Extract the EXACT name as printed on the document
2. Convert date of birth to DD-MM-YYYY format (e.g., "01-12-1987")
3. If any field is not found or unclear, set it to null
4. Return ONLY a JSON object with these exact field names
5. Do not include any explanations or markdown

OCR Text:
\"\"\"
{raw_ocr_text}
\"\"\"

Return ONLY the JSON object:"""

    result = call_llm_with_retry(user_prompt, system_prompt)
    
    if result:
        # Normalize date format
        if result.get('dob'):
            result['dob'] = normalize_date_format(result['dob'])
        
        logger.info(f"✓ Personal data extracted successfully: name={result.get('name')}, dob={result.get('dob')}")
        return result
    else:
        logger.error("✗ Failed to extract personal data with LLM")
        return None


def extract_educational_data_llm(raw_ocr_text: str) -> Optional[Dict]:
    """
    Extract structured educational document data using LLM.
    
    Args:
        raw_ocr_text: Complete OCR text from educational document (marksheet)
        
    Returns:
        Dict with extracted data:
        {
            "name": "BABU KHAN",
            "dob": "01-12-1987",
            "document_type": "marksheet",
            "qualification": "Class 10",
            "board": "CBSE",
            "stream": null,
            "year_of_passing": "2017",
            "school_name": "ST DON BOSCO COLLEGE",
            "marks_type": "CGPA",
            "marks": "07.4 CGPA"
        }
    """
    logger.info("=== Starting LLM extraction for EDUCATIONAL document ===")
    logger.info(f"OCR text length: {len(raw_ocr_text)} characters")
    
    system_prompt = """You are an expert data extraction assistant specializing in Indian educational documents (marksheets, certificates, degrees).

Your task is to extract structured information from OCR text and return ONLY a valid JSON object. Do not include any explanations or markdown formatting.

IMPORTANT: You MUST extract the student's name and date of birth from the document if present. These fields are CRITICAL for identity verification."""

    user_prompt = f"""Extract the following information from this educational document (marksheet/certificate) OCR text:

Required fields (CRITICAL - MUST EXTRACT IF PRESENT):
- name: Student's full name EXACTLY as printed on document (CRITICAL - used for identity verification)
- dob: Date of birth in DD-MM-YYYY format (if visible on document, CRITICAL - used for identity verification)

Other required fields:
- document_type: Always "marksheet" for educational documents
- qualification: Class/Standard (e.g., "Class 10", "Class 12", "Class X", "Class XII")
- board: Board/Council name (e.g., "CBSE", "ICSE", "State Board", "UP Board")
- stream: Stream if Class 12 (e.g., "Science", "Commerce", "Arts"), set to null for Class 10
- year_of_passing: Year of passing in YYYY format (e.g., "2017")
- school_name: School/College name
- marks_type: Either "CGPA" or "Percentage"
- marks: The marks value with unit (e.g., "7.4 CGPA" or "85%")

Extraction Priority (Search order):
1. Student's Name - look for: "Name:", "Student Name:", "Candidate Name:", or the printed name field
2. Date of Birth - look for: "DOB:", "Date of Birth:", "D.O.B:", birth date field, or enrollment records showing age/DOB
3. If DOB not found, search enrollment/admission forms for birth year/date

Critical instructions:
1. ALWAYS attempt to extract name and DOB - even if partially visible
2. For name: use EXACT spelling from document, preserve capitalization
3. For DOB: normalize to DD-MM-YYYY format if different format found
4. If DOB is not present on marksheet, set to null (but try hard to find it)
5. If any other field is not found, set it to null
6. Return ONLY a JSON object with these exact field names
7. Do not include any explanations or markdown

OCR Text:
\"\"\"
{raw_ocr_text}
\"\"\"

Return ONLY the JSON object:"""

    result = call_llm_with_retry(user_prompt, system_prompt)
    
    if result:
        # Normalize date format if present
        if result.get('dob'):
            result['dob'] = normalize_date_format(result['dob'])
            logger.info(f"[EDU-LLM] ✓ Extracted DOB: {result['dob']}")
        else:
            logger.warning(f"[EDU-LLM] ✗ No DOB found in educational document")
        
        # Normalize qualification
        if result.get('qualification'):
            qual = result['qualification'].upper()
            if 'X' in qual and '12' not in qual and 'XII' not in qual:
                result['qualification'] = 'Class 10'
            elif 'XII' in qual or '12' in qual:
                result['qualification'] = 'Class 12'
        
        # Log extracted name
        if result.get('name'):
            logger.info(f"[EDU-LLM] ✓ Extracted name: {result.get('name')}")
        else:
            logger.warning(f"[EDU-LLM] ✗ No name found in educational document")
        
        logger.info(f"✓ Educational data extracted: name={result.get('name')}, qualification={result.get('qualification')}, dob={result.get('dob')}")
        return result
    else:
        logger.error("✗ Failed to extract educational data with LLM")
        return None


def extract_data_with_fallback(raw_ocr_text: str, document_type: str) -> Optional[Dict]:
    """
    Extract data with LLM, with fallback to empty structure if LLM unavailable.
    
    Args:
        raw_ocr_text: Complete OCR text
        document_type: "personal" or "educational"
        
    Returns:
        Extracted data dict or None
    """
    if document_type == "personal":
        return extract_personal_data_llm(raw_ocr_text)
    elif document_type == "educational":
        return extract_educational_data_llm(raw_ocr_text)
    else:
        logger.error(f"Unknown document type: {document_type}")
        return None
