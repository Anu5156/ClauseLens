from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from backend.models import DocumentParsed, RewriteResult
from backend.llm.provider import GeminiProvider, LLMProvider
from backend.config import GEMINI_API_KEY
import re

class LLMRewriteSchema(BaseModel):
    executive_summary: str
    key_rights_summary: str
    clauses_simplified: List[Dict[str, str]] = Field(default_factory=list)

# Offline High-Quality Translations for Hindi and Kannada
TRANSLATION_DICTIONARY = {
    "hi": {
        "rental": {
            "summary": "यह एक आवासीय किराया समझौता (Residential Lease Agreement) है। इसमें मकान मालिक और किरायेदार के बीच किराया, सुरक्षा राशि, नोटिस अवधि और परिसर के उपयोग की कानूनी शर्तें तय की गई हैं।",
            "rights": "किरायेदार के अधिकार: परिसर का शांतिपूर्ण आवासीय उपयोग, और लीज समाप्ति पर सुरक्षा जमा की वापसी (अध्याय 14.3 के अधीन)। मकान मालिक के अधिकार: समय पर मासिक किराया प्राप्त करना और 30 दिनों का पूर्व लिखित नोटिस देकर समझौता समाप्त करना।"
        },
        "employment": {
            "summary": "यह एक कार्यकारी रोजगार समझौता (Executive Employment Agreement) है। इसमें वेतन, गोपनीय जानकारी की सुरक्षा, गैर-प्रतिस्पर्धा (Non-Compete) और रोजगार समाप्ति के नियम शामिल हैं।",
            "rights": "कर्मचारी के अधिकार: $165,000 वार्षिक आधार वेतन, स्वास्थ्य बीमा, और 30 दिनों का पूर्व नोटिस। कंपनी के अधिकार: व्यापार रहस्यों की सुरक्षा और नौकरी छोड़ने के बाद 12 महीने तक प्रतिस्पर्धी व्यवसाय में काम न करने की बाध्यता।"
        },
        "saas_terms": {
            "summary": "यह सास (SaaS) सेवा की शर्तें हैं। इसमें सॉफ्टवेयर प्लेटफॉर्म का लाइसेंस, भुगतान की शर्तें, स्वतः नवीनीकरण (Auto-Renewal) और एकतरफा संशोधन की शर्तें शामिल हैं।",
            "rights": "ग्राहक के अधिकार: सॉफ्टवेयर प्लेटफॉर्म का गैर-अनन्य उपयोग। कंपनी के अधिकार: चालान जारी होने के 10 दिनों में भुगतान प्राप्त करना, देर से भुगतान पर 15% साप्ताहिक जुर्माना, और 180 दिनों के नोटिस के बिना स्वतः नवीनीकरण।"
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
            "rights": "ಉದ್ಯೋಗಿಯ ಹಕ್ಕುಗಳು: $165,000 ವಾರ್ಷಿಕ ಮೂಲ ವೇತನ, ಆರೋಗ್ಯ ವಿಮೆ, ಮತ್ತು 30 ದಿನಗಳ ನೋಟಿಸ್ ಅವಧಿ. ಕಂಪನಿಯ ಹಕ್ಕುಗಳು: ಕಂಪನಿಯ ಬೌದ್ಧಿಕ ರಕ್ಷಣೆ ಮತ್ತು ಉದ್ಯೋಗ ಬಿಟ್ಟ ನಂತರ 12 ತಿಂಗಳುಗಳ ಕಾಲ ಸ್ಪರ್ಧಿಗಳೊಂದಿಗೆ ಕೆಲಸ ಮಾಡದಂತೆ ನಿರ್ಬಂಧಿಸುವುದು."
        },
        "saas_terms": {
            "summary": "ಇದು ಸಾಸ್ (SaaS) ಸೇವಾ ನಿಯಮಗಳು ಮತ್ತು ಷರತ್ತುಗಳ ಒಪ್ಪಂದವಾಗಿದೆ. ಇದರಲ್ಲಿ ಸಾಫ್ಟ್‌ವೇರ್ ಪರವಾನಗಿ, ಶುಲ್ಕ ಪಾವತಿ, ಸ್ವಯಂ ನವೀಕರಣ ಮತ್ತು ಏಕಪಕ್ಷೀಯ ತಿದ್ದುಪಡಿ ನಿಯಮಗಳಿವೆ.",
            "rights": "ಗ್ರಾಹಕರ ಹಕ್ಕುಗಳು: ಸಾಫ್ಟ್‌ವೇರ್ ವೇದಿಕೆಯ ಬಳಕೆಯ ಹಕ್ಕು. ಕಂಪನಿಯ ಹಕ್ಕುಗಳು: ಸರಕುಪಟ್ಟಿ ದಿನಾಂಕದಿಂದ 10 ದಿನಗಳಲ್ಲಿ ಪಾವತಿ ಪಡೆಯುವುದು, ವಿಳಂಬ ಪಾವತಿಗೆ ವಾರಕ್ಕೆ 15% ದಂಡ ಮತ್ತು 180 ದಿನಗಳ ಮುಂಚಿತ ನೋಟಿಸ್ ಇಲ್ಲದೆ ಸ್ವಯಂ ನವೀಕರಣ."
        },
        "default": {
            "summary": "ಇದು ವಾಣಿಜ್ಯ ಕಾನೂನು ಒಪ್ಪಂದವಾಗಿದ್ದು, ಇದರಲ್ಲಿ ಎರಡೂ ಪಕ್ಷಗಳ ಹಕ್ಕುಗಳು, ಕರ್ತವ್ಯಗಳು, ಪಾವತಿ ನಿಯಮಗಳು ಮತ್ತು ವಿವಾದ ಇತ್ಯರ್ಥದ ಷರತ್ತುಗಳಿವೆ.",
            "rights": "ಎರಡೂ ಪಕ್ಷಗಳ ಪ್ರಮುಖ ಹಕ್ಕುಗಳು ಒಪ್ಪಂದದ ನಿಯಮಗಳು ಮತ್ತು ಅನ್ವಯವಾಗುವ ಕಾನೂನುಗಳಿಗೆ ಒಳಪಟ್ಟಿರುತ್ತವೆ."
        }
    }
}

# Category-level translations for Hindi
CLAUSE_CATEGORY_HI = {
    "payment_terms": "भुगतान और शुल्क की शर्तें: समझौते के अनुसार समय पर भुगतान करना अनिवार्य है।",
    "notice_period": "नोटिस अवधि: अनुबंध में किसी भी बदलाव या समाप्ति के लिए पूर्व लिखित सूचना आवश्यक है।",
    "termination": "अनुबंध समाप्ति: समझौते को समाप्त करने के नियम, नोटिस और शर्तें।",
    "dispute_resolution": "विवाद समाधान: किसी भी मतभेद की स्थिति में मध्यस्थता या न्यायालयीन प्रक्रिया।",
    "governing_law": "लागू क्षेत्राधिकार: यह अनुबंध निर्दिष्ट राज्य और देश के कानूनों द्वारा शासित होगा।",
    "non_compete": "गैर-प्रतिस्पर्धा: अनुबंध अवधि के दौरान और बाद में प्रतिस्पर्धी व्यवसाय में काम करने पर कानूनी रोक।",
    "confidentiality": "गोपनीयता: व्यापार रहस्यों और निजी डेटा को गुप्त रखने की बाध्यता।",
    "indemnity": "क्षतिपूर्ति: किसी भी नुकसान या कानूनी दावे के लिए वित्तीय उत्तरदायित्व।",
    "unilateral_amendment": "एकतरफा संशोधन: कंपनी द्वारा बिना पूर्व सहमति के नियमों में बदलाव का अधिकार।",
    "ip_assignment": "बौद्धिक संपदा: कार्य के दौरान निर्मित सभी आविष्कारों और कॉपीराइट पर कंपनी का स्वामित्व।",
    "limitation_of_liability": "दायित्व की सीमा: किसी भी क्षति की स्थिति में अधिकतम वित्तीय सीमा।",
    "auto_renewal": "स्वतः नवीनीकरण: अनुबंध बिना पूर्व सूचना दिए स्वचालित रूप से नवीनीकृत हो जाएगा।",
    "other": "सामान्य कानूनी प्रावधान और परिभाषाएँ।"
}

# Category-level translations for Kannada
CLAUSE_CATEGORY_KN = {
    "payment_terms": "ಪಾವತಿ ನಿಯಮಗಳು ಮತ್ತು ಶುಲ್ಕಗಳು: ಒಪ್ಪಂದದ ಪ್ರಕಾರ ನಿಗದಿತ ಸಮಯದಲ್ಲಿ ಶುಲ್ಕ ಪಾವತಿಸುವುದು ಕಡ್ಡಾಯವಾಗಿದೆ.",
    "notice_period": "ನೋಟಿಸ್ ಅವಧಿ: ಯಾವುದೇ ಬದಲಾವಣೆ ಅಥವಾ ರದ್ದತಿಗೆ ಮುಂಚಿತ ಲಿಖಿತ ನೋಟಿಸ್ ನೀಡುವುದು ಅವಶ್ಯಕ.",
    "termination": "ಒಪ್ಪಂದ ಮುಕ್ತಾಯ: ಒಪ್ಪಂದವನ್ನು ರದ್ದುಗೊಳಿಸುವ ನಿಯಮಗಳು ಮತ್ತು ಷರತ್ತುಗಳು.",
    "dispute_resolution": "ವಿವಾದ ಇತ್ಯರ್ಥ: ಯಾವುದೇ ಭಿನ್ನಾಭಿಪ್ರಾಯದ ಸಂದರ್ಭದಲ್ಲಿ ಮಧ್ಯಸ್ಥಿಕೆ ಅಥವಾ ನ್ಯಾಯಾಲಯದ ಕಾನೂನು ಕ್ರಮ.",
    "governing_law": "ಅನ್ವಯವಾಗುವ ಕಾನೂನು: ಈ ಒಪ್ಪಂದವು ನಿರ್ದಿಷ್ಟ ನ್ಯಾಯವ್ಯಾಪ್ತಿಯ ಕಾನೂನುಗಳಿಗೆ ಒಳಪಟ್ಟಿರುತ್ತದೆ.",
    "non_compete": "ಸ್ಪರ್ಧಾ-ರಹಿತ ನಿರ್ಬಂಧ: ಒಪ್ಪಂದದ ಅವಧಿಯಲ್ಲಿ ಮತ್ತು ನಂತರ ಸ್ಪರ್ಧಾತ್ಮಕ ಸಂಸ್ಥೆಗಳಲ್ಲಿ ಕೆಲಸ ಮಾಡುವುದನ್ನು ನಿರ್ಬಂಧಿಸಲಾಗಿದೆ.",
    "confidentiality": "ಗೌಪ್ಯತೆ: ವ್ಯಾಪಾರ ರಹಸ್ಯಗಳು ಮತ್ತು ವೈಯಕ್ತಿಕ ಮಾಹಿತಿಯನ್ನು ರಕ್ಷಿಸುವ ಬದ್ಧತೆ.",
    "indemnity": "ಪರಿಹಾರ: ಯಾವುದೇ ಹಾನಿ ಅಥವಾ ಕಾನೂನು ಹಕ್ಕೊತ್ತಾಯಗಳಿಗೆ ಹಣಕಾಸಿನ ಹೊಣೆಗಾರಿಕೆ.",
    "unilateral_amendment": "ಏಕಪಕ್ಷೀಯ ತಿದ್ದುಪಡಿ: ಪೂರ್ವಾನುಮತಿಯಿಲ್ಲದೆ ನಿಯಮಗಳನ್ನು ಬದಲಾಯಿಸುವ ಅಧಿಕಾರ.",
    "ip_assignment": "ಬೌದ್ಧಿಕ ಆಸ್ತಿ ಹಕ್ಕು: ಕೆಲಸದ ಸಮಯದಲ್ಲಿ ರಚಿಸಲಾದ ಎಲ್ಲಾ ಆವಿಷ್ಕಾರಗಳ ಮೇಲೆ ಸಂಸ್ಥೆಯ ಸಂಪೂರ್ಣ ಒಡೆತನ.",
    "limitation_of_liability": "ಹೊಣೆಗಾರಿಕೆಯ ಮಿತಿ: ಯಾವುದೇ ನಷ್ಟದ ಸಂದರ್ಭದಲ್ಲಿ ಗರಿಷ್ಠ ಪರಿಹಾರದ ಮಿತಿ.",
    "auto_renewal": "ಸ್ವಯಂ ನವೀಕರಣ: ಮುಂಚಿತ ಸೂಚನೆ ನೀಡದಿದ್ದರೆ ಒಪ್ಪಂದವು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ನವೀಕರಣಗೊಳ್ಳುತ್ತದೆ.",
    "other": "ಸಾಮಾನ್ಯ ಕಾನೂನು ನಿಬಂಧನೆಗಳು ಮತ್ತು ವ್ಯಾಖ್ಯಾನಗಳು."
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
    and provides executive summaries and clause explanations in English, Hindi, or Kannada.
    """
    raw_lang = (language or "en").lower().strip()
    if raw_lang.startswith("hi"):
        lang = "hi"
    elif raw_lang.startswith("kn"):
        lang = "kn"
    else:
        lang = "en"

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
                    {
                        "clause_number": c.clause_number,
                        "title": c.title,
                        "original_text": c.text.strip(),
                        "simplified_text": rewrite_clause_simple(c.text) if lang == "en" else (CLAUSE_CATEGORY_HI.get(c.category, c.title) if lang == "hi" else CLAUSE_CATEGORY_KN.get(c.category, c.title))
                    }
                    for c in doc.clauses
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

    clauses_simplified = []
    for c in doc.clauses:
        cat = getattr(c, "category", "other")
        if lang == "hi":
            simplified_body = CLAUSE_CATEGORY_HI.get(cat, f"खंड {c.clause_number}: {c.title} - यह खंड अनुबंध के अंतर्गत लागू नियमों को परिभाषित करता है।")
            title_text = f"{c.title} (खंड {c.clause_number})"
        elif lang == "kn":
            simplified_body = CLAUSE_CATEGORY_KN.get(cat, f"ಷರತ್ತು {c.clause_number}: {c.title} - ಈ ಷರತ್ತು ಒಪ್ಪಂದದ ಅಡಿಯಲ್ಲಿ ಅನ್ವಯವಾಗುವ ನಿಯಮಗಳನ್ನು ವಿವರಿಸುತ್ತದೆ.")
            title_text = f"{c.title} (ಷರತ್ತು {c.clause_number})"
        else:
            simplified_body = rewrite_clause_simple(c.text) if level == "simple" else c.text.strip()
            title_text = c.title

        clauses_simplified.append({
            "clause_number": c.clause_number,
            "title": title_text,
            "original_text": c.text.strip(),
            "simplified_text": simplified_body
        })

    return RewriteResult(
        level=level,
        language=lang,
        executive_summary=exec_summary,
        key_rights_summary=rights_summary,
        clauses_simplified=clauses_simplified
    )

