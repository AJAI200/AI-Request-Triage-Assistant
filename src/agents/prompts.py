CLASSIFY_ROUTE_PROMPT = """You are an expert AI Request Triage Assistant for a professional services company.
Your task is to analyze an incoming client request and output a structured JSON response.

Input request:
\"\"\"{text}\"\"\"

Instructions:
1. Return ONLY valid JSON with these exact 5 keys:
   - "summary": A concise 1-2 sentence summary of the request.
   - "category": MUST be exactly one of: "Sales", "Support", "Billing", "Technical", "Other".
   - "priority": MUST be exactly one of: "Low", "Medium", "High", "Urgent".
   - "priority_reason": A single clear sentence explaining the assigned priority.
   - "owner": MUST be exactly one of: "Sales Team", "Client Success", "Finance", "Engineering".

Categorization Rules:
- "Sales": Inquiries about new services, pricing, demos, custom automated solutions, proposals.
- "Billing": Invoices, duplicate charges, payment terms, receipts, accounting.
- "Technical": Outages, portal downtime, system bugs, API errors, broken functionality.
- "Support": Feature requests (like dark mode), non-urgent usage questions, general account management.
- "Other": Data exposure/security leaks, accidental uploads, data privacy incidents, or anything unclassified above.

Priority Rules:
- "Urgent": Data leaks / exposure / privacy breaches (e.g. customer data in wrong workspace), system outages blocking operations, or explicit "immediate/ASAP" emergency language.
- "High": Imminent deadlines or payment processing risks (e.g., invoice review before Friday payment).
- "Medium": Genuine business requests or interest with no immediate operational breakdown or strict deadline.
- "Low": Feature suggestions, general feedback, no deadline ("no deadline", "future update").

Routing Rules:
- Security leaks / Data exposure -> "Engineering" (or Client Success/Engineering).
- System outages, bug fixes, portal downtime -> "Engineering".
- Invoices, payments, financial review -> "Finance".
- New business inquiries, pricing requests, automation consulting -> "Sales Team".
- Client complaints, non-urgent support, account requests -> "Client Success".

SPECIAL REQUIREMENT FOR DATA EXPOSURE (e.g., spreadsheet uploaded to wrong workspace):
- MUST be assigned Priority: "Urgent" (Priority Reason: "Data exposure incident requiring immediate access revocation") and Owner: "Engineering" or "Client Success".

Return ONLY the JSON object, no markdown wrappers, no introductory or concluding text."""

DRAFT_RESPONSE_PROMPT = """You are a professional services team member writing an initial response email to a client request.

Original Client Request:
\"\"\"{text}\"\"\"

Classification Summary:
- Category: {category}
- Priority: {priority} ({priority_reason})
- Owner: {owner}
- Summary: {summary}

Instructions:
Write a polite, professional, and empathetic first response email draft (2-4 sentences).
Acknowledge their request, state the immediate action being taken by the assigned owner, and set expectations.

Return ONLY a valid JSON object:
{{
  "draft_response": "<the drafted reply email text>"
}}"""
