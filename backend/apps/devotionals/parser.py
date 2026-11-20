import datetime
import logging
import re
from typing import Any, Dict, List, Optional

from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def parse_devotional_date(date_str: str) -> Optional[datetime.date]:
    """
    Parses date strings like:
    - 'THURSDAY NOVEMBER 19, 2026.'
    - 'FRIDAY, 20 NOVEMBER 2026'
    - 'DECEMBER 31, 2026'
    - '2027-01-01'
    """
    cleaned = date_str.strip().rstrip(".").strip()
    # Strip day of week prefix if present (e.g., 'THURSDAY ', 'THURSDAY, ')
    cleaned = re.sub(
        r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    try:
        dt = date_parser.parse(cleaned, fuzzy=True)
        return dt.date()
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def parse_single_devotional_block(block_text: str, default_author: str = "Pastor Paul Rika") -> Dict[str, Any]:
    """
    Parses a single devotional block containing:
    DATE, TOPIC, TEXT, KEY VERSE, Reflection body, Thought for the day, Song for the day, Bible reading.
    """
    issues: List[str] = []
    text = block_text.strip()

    # 1. Author Attribution (if in header)
    author = default_author
    author_match = re.search(
        r"DAILY DEVOTIONAL BY\s+([A-Z\s\.\,\-]+?)(?:\s+INTERNATIONAL DIRECTOR|\s*\n|\.|$)",
        text,
        re.IGNORECASE,
    )
    if author_match:
        extracted_author = author_match.group(1).strip().title()
        if extracted_author and len(extracted_author) > 3:
            author = extracted_author

    # 2. DATE
    date_val: Optional[datetime.date] = None
    date_match = re.search(r"DATE\s*:\s*([^\n]+)", text, re.IGNORECASE)
    if date_match:
        raw_date_str = date_match.group(1).strip()
        date_val = parse_devotional_date(raw_date_str)
        if not date_val:
            issues.append(f"Could not parse date format: '{raw_date_str}'")
    else:
        issues.append("Missing DATE marker")

    # 3. TOPIC
    topic = ""
    topic_match = re.search(
        r"TOPIC\s*:\s*([\s\S]*?)(?=\n\s*(?:TEXT|SCRIPTURE|KEY VERSE)\s*:|\Z)",
        text,
        re.IGNORECASE,
    )
    if topic_match:
        topic = " ".join(topic_match.group(1).split()).strip()
    if not topic:
        issues.append("Missing or empty TOPIC")

    # 4. TEXT (Scripture Passage Reference + Verse text)
    text_reference = ""
    text_body = ""
    text_match = re.search(
        r"TEXT\s*:\s*([^\n]+)\n([\s\S]*?)(?=\n\s*KEY\s+VERSE\s*:|\Z)",
        text,
        re.IGNORECASE,
    )
    if text_match:
        text_reference = text_match.group(1).strip()
        text_body = text_match.group(2).strip()
    else:
        # Fallback if no verses or single line
        simple_text = re.search(r"TEXT\s*:\s*([^\n]+)", text, re.IGNORECASE)
        if simple_text:
            text_reference = simple_text.group(1).strip()

    # 5. KEY VERSE (Reference + Quote)
    key_verse_ref = ""
    key_verse_text = ""
    key_verse_match = None

    # First attempt: match key verse with closing quotation marks
    quoted_match = re.search(
        r"KEY\s+VERSE\s*:\s*([^\n“\"״]+?)(?:[:–—\-]\s*|\s{2,}|\s*)([“\"״][\s\S]*?[”\"״])",
        text,
        re.IGNORECASE,
    )
    if quoted_match:
        key_verse_match = quoted_match
        key_verse_ref = quoted_match.group(1).strip()
        key_verse_text = quoted_match.group(2).strip().strip('“"״').strip()
    else:
        # Fallback if no closing quote found
        key_verse_match = re.search(
            r"KEY\s+VERSE\s*:\s*([\s\S]*?)(?=\n\s*(?:[A-Z][a-zA-Z\s]{3,}\n|Thought for the day|Song for the day|Bible reading)|\n{2,}|\Z)",
            text,
            re.IGNORECASE,
        )
        if key_verse_match:
            kv_raw = key_verse_match.group(1).strip()
            # Look for quotation marks or dash separating ref and quote
            quote_split = re.search(r'([1-3]?\s*[A-Za-z]+\s*\d+:\d+(?:-\d+)?)\s*[:–—\-]?\s*[“"״]([^”"״]+)[”"״]', kv_raw)
            if quote_split:
                key_verse_ref = quote_split.group(1).strip()
                key_verse_text = quote_split.group(2).strip()
            else:
                ref_part_match = re.match(r"^([1-3]?\s*[A-Za-z]+\s*\d+:\d+(?:-\d+)?)(.*)$", kv_raw, re.DOTALL)
                if ref_part_match:
                    key_verse_ref = ref_part_match.group(1).strip()
                    key_verse_text = ref_part_match.group(2).strip().strip('“"״:–—-').strip()
                else:
                    key_verse_ref = text_reference
                    key_verse_text = kv_raw
        else:
            issues.append("Missing KEY VERSE")

    # 6. Trailing sections: Thought for the day, Song for the day, Bible reading
    thought_for_day = ""
    thought_match = re.search(
        r"Thought for the day\s*:\s*([\s\S]*?)(?=\n\s*(?:Song for the day|Bible reading for the day|DATE:)|\Z)",
        text,
        re.IGNORECASE,
    )
    if thought_match:
        thought_for_day = " ".join(thought_match.group(1).split()).strip()

    song_for_day = ""
    song_match = re.search(
        r"Song for the day\s*:\s*([\s\S]*?)(?=\n\s*(?:Bible reading for the day|Thought for the day|DATE:)|\Z)",
        text,
        re.IGNORECASE,
    )
    if song_match:
        song_for_day = " ".join(song_match.group(1).split()).strip()

    bible_reading = ""
    bible_match = re.search(
        r"Bible reading for the day\s*:\s*([\s\S]*?)(?=\n\s*DATE:|\Z)",
        text,
        re.IGNORECASE,
    )
    if bible_match:
        bible_reading = " ".join(bible_match.group(1).split()).strip()

    # 7. Main Reflection Body (Everything after KEY VERSE and before Thought/Song/Bible reading)
    reflection_body = ""
    # Find start after KEY VERSE block
    kv_end_pos = -1
    if key_verse_match:
        kv_end_pos = key_verse_match.end()
    elif text_match:
        kv_end_pos = text_match.end()

    trailing_start_pos = len(text)
    for m in (thought_match, song_match, bible_match):
        if m and m.start() < trailing_start_pos:
            trailing_start_pos = m.start()

    if kv_end_pos != -1 and kv_end_pos < trailing_start_pos:
        reflection_body = text[kv_end_pos:trailing_start_pos].strip()
    elif trailing_start_pos < len(text):
        # Fallback
        reflection_body = text[:trailing_start_pos].strip()

    if not reflection_body:
        issues.append("Empty reflection body message")

    return {
        "date": date_val,
        "title": topic or "Untitled Devotional",
        "author_attribution": author,
        "text_reference": text_reference,
        "text_body": text_body,
        "key_verse_reference": key_verse_ref,
        "key_verse_text": key_verse_text,
        "reflection_body": reflection_body,
        "thought_for_day": thought_for_day,
        "song_for_day": song_for_day,
        "bible_reading_for_day": bible_reading,
        "action_point": thought_for_day,
        "has_parsing_issues": len(issues) > 0,
        "parsing_notes": "; ".join(issues),
    }


def split_text_into_devotional_blocks(full_text: str) -> List[str]:
    """
    Splits a large text into individual daily devotional segments using DATE markers.
    """
    # Look for DATE: markers at line start or after newline
    pattern = r"(?=(?:^|\n)\s*DATE\s*:)"
    raw_blocks = re.split(pattern, full_text, flags=re.IGNORECASE)

    blocks = []
    for b in raw_blocks:
        b_clean = b.strip()
        # Must contain DATE and at least TOPIC or TEXT to be considered a devotional block
        if re.search(r"DATE\s*:", b_clean, re.IGNORECASE) and (
            re.search(r"TOPIC\s*:", b_clean, re.IGNORECASE)
            or re.search(r"TEXT\s*:", b_clean, re.IGNORECASE)
        ):
            blocks.append(b_clean)

    return blocks


POPULAR_AI_MODELS = {
    # 1. Google Gemini (Default)
    "gemini-3.1-flash-lite-preview": {
        "provider": "google",
        "name": "Google Gemini 3.1 Flash-Lite (Recommended Default)",
        "badge": "Fast & Economical",
    },
    "gemini-3-flash-preview": {
        "provider": "google",
        "name": "Google Gemini 3 Flash",
        "badge": "Next-Gen Vision",
    },
    "gemini-2.5-pro": {
        "provider": "google",
        "name": "Google Gemini 2.5 Pro",
        "badge": "High Accuracy",
    },
    # 2. OpenAI
    "gpt-4o": {
        "provider": "openai",
        "name": "OpenAI GPT-4o",
        "badge": "Industry Benchmark",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "name": "OpenAI GPT-4o Mini",
        "badge": "Fast & Efficient",
    },
    # 3. Anthropic Claude
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic",
        "name": "Anthropic Claude 3.5 Sonnet",
        "badge": "Superior Document OCR",
    },
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "name": "Anthropic Claude 3.5 Haiku",
        "badge": "High Speed",
    },
    # 4. Meta Llama Vision
    "meta-llama/llama-3.2-90b-vision-instruct": {
        "provider": "openrouter",
        "name": "Meta Llama 3.2 Vision (90B)",
        "badge": "Open Weights Flagship",
    },
    # 5. Mistral AI
    "mistralai/pixtral-large-2411": {
        "provider": "mistral",
        "name": "Mistral Pixtral Large",
        "badge": "Publication Specialist",
    },
    # 6. Qwen VL
    "qwen/qwen-2.5-vl-72b-instruct": {
        "provider": "openrouter",
        "name": "Alibaba Qwen 2.5 VL (72B)",
        "badge": "OCR & Fine-Print Leader",
    },
}


def extract_devotional_page_with_ai(
    image_bytes: bytes,
    target_year: int = 2026,
    ocr_model: str = "gemini-3.1-flash-lite-preview",
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Sends a page image to the selected AI Vision model (Gemini, OpenAI, Anthropic, Mistral, OpenRouter)
    and returns the structured devotional dictionary.
    Returns None if the page is preliminary/back-matter (is_devotional == False).
    """
    import base64
    import json
    import os
    import time
    import requests

    b64_img = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""You are an expert OCR and theological document parser. Analyze this scanned page from the Holiness Revival Movement Worldwide (HOREMOW) Daily Devotional book.
Extract all structured fields into JSON. The target year is {target_year}.

JSON Schema:
{{
  "is_devotional": true, // Set to false if this page is preliminary (cover, title, publisher info, preface, table of contents, introduction) or back-matter (branch directory, addresses, ad)
  "book_page_number": 11,
  "raw_date_str": "SATURDAY July 11",
  "date": "{target_year}-07-11", // ISO date formatted as YYYY-MM-DD combining the month, day, and target year {target_year}
  "topic": "APPEARANCE AND MODESTY OF A HOLY CHRISTIAN",
  "text_reference": "Isaiah 3: 16 - 24", // Scripture passage reference
  "text_body": "", // Numbered verses if printed, or empty if only the reference is given
  "key_verse_reference": "Jeremiah 4:30",
  "key_verse_text": "And when thou art spoiled...",
  "reflection_body": "Full text of the reflection / sermon / Q&A",
  "thought_for_day": "Holiness is next to Godliness",
  "song_for_day": "Holiness is the beauty of Believer...",
  "bible_reading_for_day": "Ecclesiastes 5-8",
  "is_continuation": false // Set to true if this page does NOT have a new topic/date header and is a continuation of the previous day's reflection
}}
Return ONLY valid JSON.
"""

    model_config = POPULAR_AI_MODELS.get(ocr_model, {})
    provider = model_config.get("provider", "google")
    if ocr_model.startswith("gemini"):
        provider = "google"
    elif ocr_model.startswith("gpt"):
        provider = "openai"
    elif ocr_model.startswith("claude"):
        provider = "anthropic"

    # -------------------------------------------------------------
    # PROVIDER 1: GOOGLE GEMINI (DEFAULT)
    # -------------------------------------------------------------
    if provider == "google":
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        models_to_try = [
            ocr_model,
            "gemini-3.1-flash-lite-preview",
            "gemini-flash-lite-latest",
            "gemini-3-flash-preview",
        ]
        # Remove duplicates while preserving order
        seen = set()
        models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

        last_error = ""
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
                            {"text": prompt},
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                },
            }

            for attempt in range(2):
                try:
                    resp = requests.post(url, json=payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            continue
                        candidate = candidates[0]
                        content_obj = candidate.get("content", {})
                        parts = content_obj.get("parts", [])
                        if not parts or "text" not in parts[0]:
                            continue
                        parsed = json.loads(parts[0]["text"])
                        if not parsed.get("is_devotional", True):
                            return None
                        return parsed
                    elif resp.status_code in (429, 503):
                        logger.warning(f"Google {model_name} returned {resp.status_code} (attempt {attempt+1}); retrying...")
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        last_error = f"{resp.status_code}: {resp.text}"
                        break
                except Exception as e:
                    last_error = str(e)
                    time.sleep(1)

        raise RuntimeError(f"Gemini Vision extraction failed: {last_error}")

    # -------------------------------------------------------------
    # PROVIDER 2: OPENAI (GPT-4o, GPT-4o-mini)
    # -------------------------------------------------------------
    elif provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": ocr_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_text)
        if not parsed.get("is_devotional", True):
            return None
        return parsed

    # -------------------------------------------------------------
    # PROVIDER 3: ANTHROPIC CLAUDE
    # -------------------------------------------------------------
    elif provider == "anthropic":
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": ocr_model,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64_img,
                            },
                        },
                        {"type": "text", "text": prompt + "\nOutput valid JSON only."},
                    ],
                }
            ],
            "temperature": 0.1,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Anthropic error {resp.status_code}: {resp.text}")
        data = resp.json()
        raw_text = data["content"][0]["text"]
        # Extract json block if wrapped in markdown
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(raw_text)
        if not parsed.get("is_devotional", True):
            return None
        return parsed

    # -------------------------------------------------------------
    # PROVIDER 4: OPENAI-COMPATIBLE (OpenRouter, Mistral, Groq, Llama, Qwen)
    # -------------------------------------------------------------
    else:
        key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("MISTRAL_API_KEY") or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError(f"API key is not configured for model {ocr_model}.")

        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        if provider == "mistral":
            endpoint = "https://api.mistral.ai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": ocr_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt + "\nOutput valid JSON only."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}",
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.1,
        }
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"{provider} error {resp.status_code}: {resp.text}")
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(raw_text)
        if not parsed.get("is_devotional", True):
            return None
        return parsed


def extract_devotional_page_with_gemini(
    image_bytes: bytes,
    target_year: int = 2026,
    gemini_api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Backward compatibility alias for extract_devotional_page_with_ai"""
    return extract_devotional_page_with_ai(
        image_bytes=image_bytes,
        target_year=target_year,
        ocr_model="gemini-3.1-flash-lite-preview",
        api_key=gemini_api_key,
    )


def parse_scanned_devotional_pdf(
    file_path: str,
    target_year: int = 2026,
    start_page: int = 1,
    end_page: int = 184,
    ocr_model: str = "gemini-3.1-flash-lite-preview",
    api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    progress_callback: Optional[Any] = None,
    default_author: str = "Pastor Paul Rika",
) -> List[Dict[str, Any]]:
    """
    Renders pages of a scanned PDF and uses the configured AI Vision model to extract daily devotionals.
    Skips preliminary/back-matter pages automatically and stitches multi-page devotionals.
    """
    import io

    import pypdfium2 as pdfium

    effective_key = api_key or gemini_api_key

    pdf = pdfium.PdfDocument(file_path)
    total_pdf_pages = len(pdf)

    # In HOREMOW publications, book page 1 starts after ~6 preliminary pages.
    # We calculate the PDF index window safely.
    # If the PDF has ~204 pages and devotional is 1-184:
    pdf_offset = max(0, total_pdf_pages - (end_page - start_page + 1) - 10)
    if pdf_offset > 8 or pdf_offset < 4:
        pdf_offset = 6  # standard 6 preliminary pages default

    start_idx = max(0, start_page - 1 + pdf_offset)
    end_idx = min(total_pdf_pages, end_page + pdf_offset)

    target_page_indices = list(range(start_idx, end_idx))
    total_to_process = len(target_page_indices)

    parsed_entries: List[Dict[str, Any]] = []
    processed_count = 0

    for p_idx in target_page_indices:
        processed_count += 1
        page = pdf[p_idx]
        buf = io.BytesIO()
        try:
            pil_img = page.render(scale=1.5).to_pil()
            pil_img.save(buf, format="JPEG", quality=85)
            img_bytes = buf.getvalue()
        finally:
            page.close()

        try:
            extracted = extract_devotional_page_with_ai(
                img_bytes,
                target_year=target_year,
                ocr_model=ocr_model or "gemini-3.1-flash-lite-preview",
                api_key=effective_key,
            )
        except Exception as e:
            logger.error(f"Failed to extract page {p_idx+1} with {ocr_model}: {e}")
            continue

        if not extracted or not extracted.get("is_devotional", True):
            if progress_callback:
                progress_callback(processed_count, total_to_process, None)
            continue

        # Handle multi-page continuation
        if extracted.get("is_continuation", False) and parsed_entries:
            prev = parsed_entries[-1]
            more_body = extracted.get("reflection_body", "").strip()
            if more_body:
                prev["reflection_body"] = (prev["reflection_body"] + "\n\n" + more_body).strip()
            if progress_callback:
                progress_callback(processed_count, total_to_process, prev)
            continue

        # Construct validated entry
        date_obj = parse_devotional_date(extracted.get("date", "")) or parse_devotional_date(
            f"{extracted.get('raw_date_str', '')} {target_year}"
        )
        if not date_obj:
            # Fallback to date parser on date field
            try:
                date_obj = datetime.date.fromisoformat(extracted.get("date", ""))
            except Exception:
                pass

        if not date_obj:
            logger.warning(f"Skipping page {p_idx+1} due to unresolvable date: {extracted.get('raw_date_str')}")
            continue

        entry_record: Dict[str, Any] = {
            "date": date_obj,
            "title": extracted.get("topic", "Daily Devotional").strip(),
            "author_attribution": default_author,
            "text_reference": extracted.get("text_reference", "").strip(),
            "text_body": extracted.get("text_body", "").strip(),
            "key_verse_reference": extracted.get("key_verse_reference", "").strip(),
            "key_verse_text": extracted.get("key_verse_text", "").strip(),
            "reflection_body": extracted.get("reflection_body", "").strip(),
            "thought_for_day": extracted.get("thought_for_day", "").strip(),
            "song_for_day": extracted.get("song_for_day", "").strip(),
            "bible_reading_for_day": extracted.get("bible_reading_for_day", "").strip(),
            "action_point": extracted.get("thought_for_day", "").strip(),
            "order": len(parsed_entries) + 1,
            "has_parsing_issues": False,
            "parsing_notes": "",
        }

        parsed_entries.append(entry_record)

        if progress_callback:
            progress_callback(processed_count, total_to_process, entry_record)

    pdf.close()
    return parsed_entries


def parse_devotional_pdf(
    file_path: str,
    default_author: str = "Pastor Paul Rika",
    target_year: int = 2026,
    start_page: int = 1,
    end_page: int = 184,
    ocr_model: str = "gemini-3.1-flash-lite-preview",
    api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    progress_callback: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Reads a PDF file. If the file contains digital text, extracts entries instantly using pypdfium2.
    If the file is a scanned book (zero digital text), seamlessly routes to parse_scanned_devotional_pdf via the chosen AI Vision model.
    """
    effective_key = api_key or gemini_api_key
    pages_text: List[str] = []

    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(file_path)
        for page in pdf:
            try:
                textpage = page.get_textpage()
                extracted = textpage.get_text_range()
                if extracted and extracted.strip():
                    pages_text.append(extracted.strip())
            finally:
                page.close()
        pdf.close()
    except Exception as e:
        logger.warning(f"pypdfium2 extraction encountered error ({e}); checking fallback")
        pages_text = []

    total_chars = sum(len(t) for t in pages_text)

    # If digital text is missing or virtually empty, this is a SCANNED PDF:
    if total_chars < 100:
        logger.info(f"PDF {file_path} contains 0 digital chars; routing to {ocr_model} scanned book OCR.")
        return parse_scanned_devotional_pdf(
            file_path=file_path,
            target_year=target_year,
            start_page=start_page,
            end_page=end_page,
            ocr_model=ocr_model,
            api_key=effective_key,
            progress_callback=progress_callback,
            default_author=default_author,
        )

    # Standard digital text extraction
    full_text = "\n\n".join(pages_text)
    blocks = split_text_into_devotional_blocks(full_text)

    # If digital text does not contain any devotional blocks (e.g. only preface/directory has text,
    # while the body is scanned images), route to Gemini Vision OCR:
    if not blocks or (len(blocks) < 10 and len(pages_text) > 30):
        logger.info(
            f"Digital text in {file_path} contains only {len(blocks)} blocks for {len(pages_text)} pages. "
            f"Routing to {ocr_model} scanned book OCR pipeline."
        )
        return parse_scanned_devotional_pdf(
            file_path=file_path,
            target_year=target_year,
            start_page=start_page,
            end_page=end_page,
            ocr_model=ocr_model,
            api_key=effective_key,
            progress_callback=progress_callback,
            default_author=default_author,
        )

    parsed_entries: List[Dict[str, Any]] = []
    for idx, block in enumerate(blocks):
        entry = parse_single_devotional_block(block, default_author=default_author)
        entry["order"] = idx + 1
        parsed_entries.append(entry)

    return parsed_entries
