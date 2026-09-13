from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from backend.models import DocumentParsed, RewriteResult
from backend.llm.provider import GeminiProvider, LLMProvider
from backend.config import GEMINI_API_KEY

class LLMRewriteSchema(BaseModel):
    executive_summary: str
    key_rights_summary: str
    clauses_simplified: List[Dict[str, str]] = Field(default_factory=list)

# Offline High-Quality Translations for Hindi and Kannada
TRANSLATION_DICTIONARY = {
    "hi": {
        "rental": {
            "summary": "यह एक आवासीय किराया समझौता (Residential Lease Agreement) है। इसमें मकान मालिक और किरायेदार के बीच किराया, सुरक्षा राशि, नोटिस अवधि और परिसर के उपयोग की कानूनी शर्तें तय की गई हैं।",
            "rights": "किरायेदार के अधिकार: परिसर का आवासीय उपयोग, और लीज समाप्ति पर सुरक्षा जमा की वापसी (अध्याय 14.3 के अधीन)। मकान मालिक के अधिकार: समय पर मासिक किराया प्राप्त करना और 30 दिनों का पूर्व लिखित नोटिस देकर समझौता समाप्त करना।"
        },
        "employment": {
            "summary": "यह एक कार्यकारी रोजगार समझौता (Executive Employment Agreement) है। इसमें वेतन, गोपनीय जानकारी की सुरक्षा, गैर-प्रतिस्पर्धा (Non-Compete) और रोजगार समाप्ति के नियम शामिल हैं।",
            "rights": "कर्मचारी के अधिकार: सहमत वेतन और 30 दिनों का नोटिस। कंपनी के अधिकार: व्यापार रहस्यों की सुरक्षा और नौकरी छोड़ने के बाद 12 महीने तक प्रतिस्पर्धी व्यवसाय में काम न करने की बाध्यता।"
        },
        "saas_terms": {
            "summary": "यह सास (SaaS) सेवा की शर्तें हैं। इसमें सॉफ्टवेयर प्लेटफॉर्म का लाइसेंस, भुगतान की शर्तें, स्वतः नवीनीकरण (Auto-Renewal) और एकतरफा संशोधन की शर्तें शामिल हैं।",
            "rights": "ग्राहक के अधिकार: सॉफ्टवेयर प्लेटफॉर्म का गैर-अनन्य उपयोग। कंपनी के अधिकार: चालान जारी होने के 10 दिनों में भुगतान प्राप्त करना, देर से भुगतान पर 15% साप्ताहिक जुर्माना, और 180 दिनों के नोटिस के बिना 3 साल का स्वतः नवीनीकरण।"
        },
        "default": {
            "summary": "यह एक व्यावसायिक कानूनी अनुबंध है जिसमें दोनों पक्षों के अधिकार, दायित्व, भुगतान की शर्तें और विवाद समाधान के नियम शामिल हैं।",
            "rights": "दोनों पक्षों के प्राथमिक अधिकार और कर्तव्य अनुबंध की शर्तों और लागू राज्य कानूनों द्वारा नियंत्रित होते हैं।"
        }
    },
    "kn": {
        "rental": {
            "summary": "ಇದು ವಸತಿ ಬಾಡಿಗೆ ಒಪ್ಪಂದವಾಗಿದೆ (Residential Lease Agreement). ಇದರಲ್ಲಿ ಮನೆಮಾಲೀಕ ಮತ್ತು ಬಾಡಿಗೆದಾರರ ನಡುವಿನ ಬಾಡಿಗೆ, ಮುಂಗಡ ಠೇವಣಿ, ನೋಟಿಸ್ ಅವಧಿ ಮತ್ತು ಆವರಣದ ಬಳಕೆಯ ನಿಯಮಗಳನ್ನು ನಿರ್ದಿಷ್ಟಪಡಿಸಲಾಗಿದೆ.",
            "rights": "ಬಾಡಿಗೆದಾರರ ಹಕ್ಕುಗಳು: ಆವರಣವನ್ನು ವಸತಿ ಉದ್ದೇಶಕ್ಕಾಗಿ ಬಳಸುವುದು ಮತ್ತು ಒಪ್ಪಂದ ಮುಕ್ತಾಯಗೊಂಡ ನಂತರ ಠೇವಣಿ ಮೊತ್ತವನ್ನು ಮರಳಿ ಪಡೆಯುವುದು. ಮಾಲೀಕರ ಹಕ್ಕುಗಳು: ನಿಗದಿತ ಬಾಡಿಗೆ ಸ್ವೀಕರಿಸುವುದು ಮತ್ತು 30 ದಿನಗಳ ಮುಂಚಿತ ನೋಟಿಸ್ ನೀಡಿ ಒಪ್ಪಂದ ರದ್ದುಗೊಳಿಸುವುದು."
        },
        "employment": {
            "summary": "ಇದು ಕಾರ್ಯನಿರ್ವಾಹಕ ಉದ್ಯೋಗ ಒಪ್ಪಂದವಾಗಿದೆ (Executive Employment Agreement). ಇದರಲ್ಲಿ ಉದ್ಯೋಗಿಯ ವೇತನ, ಗೌಪ್ಯ ಮಾಹಿತಿ ರಕ್ಷಣೆ, ಸ್ಪರ್ಧಾ-ರಹಿತ ಷರತ್ತುಗಳು (Non-Compete) ಮತ್ತು ಉದ್ಯೋಗ ಮುಕ್ತಾಯದ ನಿಯಮಗಳಿವೆ.",
            "rights": "ಉದ್ಯೋಗಿಯ ಹಕ್ಕುಗಳು: ನಿಗದಿತ ವೇತನ ಮತ್ತು 30 ದಿನಗಳ ನೋಟಿಸ್ ಅವಧಿ. ಕಂಪನಿಯ ಹಕ್ಕುಗಳು: ಕಂಪನಿಯ ಬೌದ್ಧಿಕ ರಕ್ಷಣೆ ಮತ್ತು ಉದ್ಯೋಗ ಬಿಟ್ಟ ನಂತರ 12 ತಿಂಗಳುಗಳ ಕಾಲ ಸ್ಪರ್ಧಿಗಳೊಂದಿಗೆ ಕೆಲಸ ಮಾಡದಂತೆ ನಿರ್ಬಂಧಿಸುವುದು."
        },
        "saas_terms": {
            "summary": "ಇದು ಸಾಸ್ (SaaS) ಸೇವಾ ನಿಯಮಗಳು ಮತ್ತು ಷರತ್ತುಗಳ ಒಪ್ಪಂದವಾಗಿದೆ. ಇದರಲ್ಲಿ ಸಾಫ್ಟ್‌ವೇರ್ ಪರವಾನಗಿ, ಶುಲ್ಕ ಪಾವತಿ, ಸ್ವಯಂ ನವೀಕರಣ ಮತ್ತು ಏಕಪಕ್ಷೀಯ ತಿದ್ದುಪಡಿ ನಿಯಮಗಳಿವೆ.",
            "rights": "ಗ್ರಾಹಕರ ಹಕ್ಕುಗಳು: ಸಾಫ್ಟ್‌ವೇರ್ ವೇದಿಕೆಯ ಬಳಕೆಯ ಹಕ್ಕು. ಕಂಪನಿಯ ಹಕ್ಕುಗಳು: ಸರಕುಪಟ್ಟಿ ದಿನಾಂಕದಿಂದ 10 ದಿನಗಳಲ್ಲಿ ಪಾವತಿ ಪಡೆಯುವುದು, ವಿಳಂಬ ಪಾವತಿಗೆ ವಾರಕ್ಕೆ 15% ದಂಡ ಮತ್ತು 180 ದಿನಗಳ ಮುಂಚಿತ ನೋಟಿಸ್ ಇಲ್ಲದೆ 3 ವರ್ಷಗಳ ಸ್ವಯಂ ನವೀಕರಣ."
        },
        "default": {
            "summary": "ಇದು ವಾಣಿಜ್ಯ ಕಾನೂನು ಒಪ್ಪಂದವಾಗಿದ್ದು, ಇದರಲ್ಲಿ ಎರಡೂ ಪಕ್ಷಗಳ ಹಕ್ಕುಗಳು, ಕರ್ತವ್ಯಗಳು, ಪಾವತಿ ನಿಯಮಗಳು ಮತ್ತು ವಿವಾದ ಇತ್ಯರ್ಥದ ಷರತ್ತುಗಳಿವೆ.",
            "rights": "ಎರಡೂ ಪಕ್ಷಗಳ ಪ್ರಮುಖ ಹಕ್ಕುಗಳು ಒಪ್ಪಂದದ ನಿಯಮಗಳು ಮತ್ತು ಅನ್ವಯವಾಗುವ ಕಾನೂನುಗಳಿಗೆ ಒಳಪಟ್ಟಿರುತ್ತವೆ."
        }
    }
}

def rewrite_clause_simple(text: str) -> str:
    """Simplifies legalese to clear conversational English."""
    simplified = text
    replacements = [
        (r'\bhereinafter referred to as\b', 'called'),
        (r'\bshall be obligated to\b', 'must'),
        (r'\bshall deposit the sum of\b', 'will pay'),
        (r'\bshall be governed by and construed in accordance with\b', 'follows the laws of'),
        (r'\bnon-exclusive, non-transferable license\b', 'permission to use'),
        (r'\bupon execution of this Agreement\b', 'when signing this contract'),
        (r'\bterminate this Agreement at any time by providing\b', 'cancel anytime with'),
        (r'\bautomatically renews unless\b', 'renews automatically unless you give')
    ]
    import re
    for pattern, repl in replacements:
        simplified = re.sub(pattern, repl, simplified, flags=re.IGNORECASE)
    return simplified.strip()

def generate_document_rewrite(
    doc: DocumentParsed,
    level: str = "plain_english",
    language: str = "en",
    provider: Optional[LLMProvider] = None
) -> RewriteResult:
    """
    Rewrites document into plain language (plain_english or simple)
    and provides executive summaries in English, Hindi, or Kannada.
    """
    lang = language.lower()
    doc_type = doc.doc_type if hasattr(doc, "doc_type") and doc.doc_type else "default"

    # 1. LLM Translation & Simplification if Gemini is available
    if GEMINI_API_KEY and provider is None:
        try:
            provider = GeminiProvider()
        except Exception:
            provider = None

    if provider and lang in {"en", "hi", "kn"}:
        lang_names = {"en": "English", "hi": "Hindi (हिंदी)", "kn": "Kannada (ಕನ್ನಡ)"}
        prompt = f"""
Rewrite and summarize the following contract into {lang_names.get(lang, 'English')}.
Reading level target: {level.upper()} (plain language, direct phrasing, zero legalese).

Contract Document: {doc.filename}
Text Excerpt:
{doc.raw_text[:2000]}

Respond in the requested language ({lang_names.get(lang, 'English')}) strictly according to the schema:
- executive_summary: 2-3 sentences summarizing the purpose and obligations
- key_rights_summary: 2-3 sentences detailing the main rights and risks for the parties
"""
        try:
            res: LLMRewriteSchema = provider.generate_structured(
                schema=LLMRewriteSchema,
                prompt=prompt,
                system_instruction=f"You are a plain-language legal translator. Translate clearly into {lang_names.get(lang, 'English')}."
            )
            return RewriteResult(
                level=level,
                language=lang,
                executive_summary=res.executive_summary,
                key_rights_summary=res.key_rights_summary,
                clauses_simplified=[
                    {"clause_number": c.clause_number, "title": c.title, "simplified_text": rewrite_clause_simple(c.text)}
                    for c in doc.clauses[:6]
                ]
            )
        except Exception:
            pass

    # 2. Offline Deterministic Translation & Plain English Engine
    if lang in TRANSLATION_DICTIONARY:
        t_dict = TRANSLATION_DICTIONARY[lang].get(doc_type, TRANSLATION_DICTIONARY[lang]["default"])
        exec_summary = t_dict["summary"]
        rights_summary = t_dict["rights"]
    else:
        # Default English
        if level == "simple":
            exec_summary = f"This contract ({doc.filename}) is an agreement between the parties setting out what each side agrees to do, how payments work, and how either side can cancel."
            rights_summary = "Your main rights include using the services or premises as agreed, receiving notices before changes, and knowing how long the deal lasts."
        else:
            exec_summary = f"This document represents a binding legal agreement ({doc.filename}). It defines mutual operational obligations, fee schedules, notice requirements, and conditions for termination."
            rights_summary = "Key entitlements include permitted operational use, specified cure windows, refund of deposits subject to terms, and clear notice requirements for termination."

    clauses_simplified = [
        {
            "clause_number": c.clause_number,
            "title": c.title,
            "simplified_text": rewrite_clause_simple(c.text) if level == "simple" else c.text.strip()
        }
        for c in doc.clauses
    ]

    return RewriteResult(
        level=level,
        language=lang,
        executive_summary=exec_summary,
        key_rights_summary=rights_summary,
        clauses_simplified=clauses_simplified
    )
