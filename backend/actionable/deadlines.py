import re
from datetime import datetime, timedelta
from typing import List, Optional
from backend.models import ClauseNode, DocumentParsed, DeadlineItem, DeadlineExport

def extract_deadlines(
    doc: DocumentParsed,
    effective_date_str: Optional[str] = None
) -> DeadlineExport:
    """
    Extracts obligations and relative deadline timeframes from clauses,
    resolves them against effective_date, and builds an RFC 5545 .ics calendar export.
    """
    base_date = datetime.now()
    if effective_date_str:
        try:
            base_date = datetime.strptime(effective_date_str.strip(), "%Y-%m-%d")
        except ValueError:
            pass

    deadlines: List[DeadlineItem] = []
    count = 0

    for clause in doc.clauses:
        text = clause.text
        text_lower = text.lower()

        # 1. Payment deadlines (within X days of invoice date)
        pay_match = re.search(r'within\s+(\d+)\s*days\s*(?:of|after)\s*(?:invoice|receipt|issuance)', text_lower)
        if pay_match:
            count += 1
            days = int(pay_match.group(1))
            res_date = base_date + timedelta(days=days)
            deadlines.append(DeadlineItem(
                id=f"{doc.id}_deadline_{count}",
                party="Customer" if "customer" in text_lower else "Paying Party",
                obligation=f"Invoice Payment Due (Net {days})",
                trigger="Invoice issuance / receipt",
                relative_days=days,
                resolved_date=res_date.strftime("%Y-%m-%d"),
                clause_id=clause.id,
                clause_number=clause.clause_number
            ))

        # 2. Auto-renewal / cancellation notice (X days prior to expiration)
        renew_match = re.search(r'(\d+)\s*days\s*(?:written\s+)?notice\s*(?:prior\s+to|before)\s*(?:term\s+)?(?:expiration|renewal|expiry)', text_lower)
        if renew_match:
            count += 1
            days = int(renew_match.group(1))
            # Assume 1-year contract expiration for standard renewal date
            contract_expiry = base_date + timedelta(days=365)
            res_date = contract_expiry - timedelta(days=days)
            deadlines.append(DeadlineItem(
                id=f"{doc.id}_deadline_{count}",
                party="Customer" if "customer" in text_lower else "Either Party",
                obligation=f"Non-Renewal Written Opt-Out Deadline ({days} days prior to expiry)",
                trigger=f"Contract expiration ({days} days prior)",
                relative_days=days,
                resolved_date=res_date.strftime("%Y-%m-%d"),
                clause_id=clause.id,
                clause_number=clause.clause_number
            ))

        # 3. Termination for convenience notice
        term_match = re.search(r'(?:terminate|terminating)\s*(?:this\s+agreement\s+)?(?:at\s+any\s+time\s+)?(?:by\s+providing\s+)?(\d+)\s*days\s*written\s*notice', text_lower)
        if term_match and not renew_match:
            count += 1
            days = int(term_match.group(1))
            res_date = base_date + timedelta(days=days)
            deadlines.append(DeadlineItem(
                id=f"{doc.id}_deadline_{count}",
                party="Either Party",
                obligation=f"Termination for Convenience Effective Date ({days} days notice)",
                trigger="Service of written notice",
                relative_days=days,
                resolved_date=res_date.strftime("%Y-%m-%d"),
                clause_id=clause.id,
                clause_number=clause.clause_number
            ))

        # 4. Deposit refund deadline
        dep_match = re.search(r'refunded|returned\s*(?:within\s+)?(\d+)\s*days', text_lower)
        if dep_match:
            count += 1
            days = int(dep_match.group(1))
            res_date = base_date + timedelta(days=days)
            deadlines.append(DeadlineItem(
                id=f"{doc.id}_deadline_{count}",
                party="Landlord",
                obligation=f"Security Deposit Refund Deadline ({days} days post-termination)",
                trigger="Lease termination / move-out",
                relative_days=days,
                resolved_date=res_date.strftime("%Y-%m-%d"),
                clause_id=clause.id,
                clause_number=clause.clause_number
            ))

        # 5. Cure period deadline
        cure_match = re.search(r'cure\s+(?:period\s+of\s+)?(\d+)\s*days', text_lower)
        if cure_match:
            count += 1
            days = int(cure_match.group(1))
            res_date = base_date + timedelta(days=days)
            deadlines.append(DeadlineItem(
                id=f"{doc.id}_deadline_{count}",
                party="Breaching Party",
                obligation=f"Breach Cure Window ({days} days)",
                trigger="Receipt of default notice",
                relative_days=days,
                resolved_date=res_date.strftime("%Y-%m-%d"),
                clause_id=clause.id,
                clause_number=clause.clause_number
            ))

    # Generate RFC 5545 iCalendar string
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ClauseLens//Legal Deadlines Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    now_stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    for item in deadlines:
        dt_val = item.resolved_date.replace("-", "") if item.resolved_date else base_date.strftime("%Y%m%d")
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{item.id}@clauselens.ai",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{dt_val}",
            f"DTEND;VALUE=DATE:{dt_val}",
            f"SUMMARY:[ClauseLens] {item.obligation}",
            f"DESCRIPTION:Party: {item.party}\\nClause: {item.clause_number}\\nTrigger: {item.trigger}\\nDocument: {doc.filename}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:Legal Deadline Reminder",
            "TRIGGER:-P1D",
            "END:VALARM",
            "END:VEVENT"
        ])

    ics_lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(ics_lines)

    return DeadlineExport(
        effective_date=base_date.strftime("%Y-%m-%d"),
        deadlines=deadlines,
        ics_content=ics_content
    )
