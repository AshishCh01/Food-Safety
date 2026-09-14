import re

def route_query(question: str, has_case_context: bool = False) -> dict:
    normalized = question.strip().lower()
    
    # Inspector Stats keywords
    stats_patterns = [
        r"how many (inspections|complaints|cases)",
        r"(my|completed|assigned|pending) (inspections|complaints|cases)",
        r"inspections (have i|did i) complete",
        r"cases (are )?assigned to me"
    ]
    
    for pattern in stats_patterns:
        if re.search(pattern, normalized):
            return {"query_type": "INSPECTOR_STATS", "requires_rag": False, "requires_case": False}
            
    # Regulation / Guidance / Hybrid keywords
    rag_patterns = [
        r"regulation", r"fssai", r"legal", r"standard", r"section", r"requirement",
        r"permissible", r"temperature", r"guideline", r"law", r"act"
    ]
    guidance_patterns = [
        r"what should i check", r"how should i inspect", r"what should i verify",
        r"inspection checklist", r"what should i focus on", r"evidence should i collect",
        r"what should i document"
    ]
    case_context_patterns = [
        r"this complaint", r"the complaint", r"this case", r"the case", 
        r"this business", r"the business", r"here", r"this restaurant",
        r"this issue", r"the issue", r"ai evidence analysis", r"case brief",
        r"ai analysis", r"ai findings"
    ]
    
    is_rag = any(re.search(p, normalized) for p in rag_patterns)
    is_guidance = any(re.search(p, normalized) for p in guidance_patterns)
    mentions_case = any(re.search(p, normalized) for p in case_context_patterns) or "complaint" in normalized
    
    if is_guidance:
        if has_case_context:
            return {"query_type": "HYBRID", "requires_rag": True, "requires_case": True}
        else:
            return {"query_type": "REGULATION", "requires_rag": True, "requires_case": False}
            
    if is_rag:
        # If it's a regulation question but mentions the case/complaint, it's HYBRID or needs case context
        if has_case_context and mentions_case:
            return {"query_type": "HYBRID", "requires_rag": True, "requires_case": True}
        return {"query_type": "REGULATION", "requires_rag": True, "requires_case": False}
        
    # Application data keywords
    app_data_patterns = [
        r"summarize", r"summary", r"status", r"complaint", r"describe", r"details",
        r"what is this", r"tell me about", r"explain", r"what happened",
        r"where is", r"location", r"business", r"who reported", r"when was", r"priority",
        r"category", r"evidence", r"previous complaint", r"previous inspection", r"prior inspection",
        r"ai analysis", r"case brief", r"what did the ai find", r"ai evidence analysis"
    ]
    
    if any(re.search(p, normalized) for p in app_data_patterns):
        return {"query_type": "APPLICATION_DATA", "requires_rag": False, "requires_case": True}
        
    # General fallback - default to searching knowledge base for any unrecognized food-safety/regulatory question
    return {"query_type": "GENERAL", "requires_rag": True, "requires_case": False}
