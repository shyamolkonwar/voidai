"""
Intent Detection and Response Classification Service
Determines what type of response the user expects
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

class ResponseType(Enum):
    """Types of responses the system can generate"""
    CONVERSATIONAL = "conversational"  # Simple chat response
    DATA_QUERY = "data_query"          # SQL query + data
    VISUALIZATION = "visualization"     # Charts/graphs
    MAP = "map"                        # Geographic visualization
    SUMMARY = "summary"                # Data summary/statistics
    COMPARISON = "comparison"          # Compare datasets
    HELP = "help"                      # System help/info

@dataclass
class IntentResult:
    response_type: ResponseType
    confidence: float
    reasoning: str
    visualization_type: Optional[str] = None  # "line", "bar", "scatter", "heatmap"
    requires_data: bool = False

class IntentDetectionService:
    """
    Analyzes user queries to determine intent and expected response type
    """
    
    def __init__(self):
        # Patterns for different intent types
        self.intent_patterns = {
            ResponseType.CONVERSATIONAL: [
                r'^(hi|hello|hey|thanks|thank you|ok|okay|good|great|awesome|cool)$',
                r'^(how are you|what.*your name|who are you)$',
                r'^(bye|goodbye|see you|talk.*later)$',
                r'^\w{1,10}$',  # Single short words
            ],
            
            ResponseType.DATA_QUERY: [
                r'(show|display|find|get|fetch|retrieve|list|give me).*\b(data|measurements|values|records|results)\b',
                r'(temperature|salinity|pressure|depth).*\b(from|in|at|of)\b',
                r'(how many|count|number of).*\b(floats|profiles|measurements)\b',
                r'(what|which).*\b(temperature|salinity|pressure)\b',
                r'(average|mean|max|maximum|min|minimum).*\b(temperature|salinity|pressure)\b',
            ],
            
            ResponseType.VISUALIZATION: [
                r'\b(plot|graph|chart|visualize|draw)\b',
                r'\b(line chart|bar chart|scatter plot|histogram|pie chart)\b',
                r'\b(trend|trends|over time|time series)\b',
                r'\b(1d|2d|3d|one dimension|two dimension|three dimension)\b',
                r'(show.*trend|plot.*against|graph.*vs|chart.*over)',
                r'(correlation|relationship|pattern).*\b(between|of)\b',
            ],
            
            ResponseType.MAP: [
                r'\b(map|location|geographic|spatial|coordinate)\b',
                r'\b(where|location|position|near|around|close to)\b',
                r'\b(latitude|longitude|lat|lon|coordinates)\b',
                r'(show.*map|plot.*map|display.*location)',
                r'(near|around|close to|within.*km|within.*miles)',
            ],
            
            ResponseType.SUMMARY: [
                r'\b(summary|summarize|overview|statistics|stats)\b',
                r'\b(total|overall|general|aggregate)\b',
                r'(what.*overall|give.*summary|provide.*overview)',
                r'(describe|explain).*\b(data|dataset|measurements)\b',
            ],
            
            ResponseType.COMPARISON: [
                r'\b(compare|comparison|vs|versus|difference|differences)\b',
                r'\b(higher|lower|greater|less|more|better|worse)\b.*\b(than|compared to)\b',
                r'(which.*better|which.*higher|which.*more)',
                r'(float.*vs.*float|region.*vs.*region)',
            ],
            
            ResponseType.HELP: [
                r'\b(help|how|what can|capabilities|features)\b',
                r'(how to|how do|what does|can you)',
                r'(instructions|guide|tutorial|example)',
            ]
        }
        
        # Data requirement patterns
        self.data_requiring_patterns = [
            r'\b(temperature|salinity|pressure|depth|measurement)\b',
            r'\b(float|profile|cycle|data)\b',
            r'\b(show|display|find|plot|chart|map)\b',
            r'\b(average|mean|max|min|count|total)\b',
        ]
        
        # Visualization type patterns
        self.visualization_patterns = {
            'line': [r'\b(line|trend|time series|over time)\b'],
            'bar': [r'\b(bar|column|histogram|frequency)\b'],
            'scatter': [r'\b(scatter|correlation|relationship|plot.*vs)\b'],
            'heatmap': [r'\b(heatmap|heat map|density|intensity)\b'],
            'pie': [r'\b(pie|percentage|proportion|distribution)\b'],
            '3d': [r'\b(3d|three dimension|surface|contour)\b'],
        }
    
    def analyze_intent(self, user_query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> IntentResult:
        """
        Analyze user query and determine the intended response type, 
        optionally using chat history for context.
        """
        
        query_lower = user_query.lower().strip()
        
        # Check each intent type
        intent_scores = {}
        
        for response_type, patterns in self.intent_patterns.items():
            score = 0
            matching_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 1
                    matching_patterns.append(pattern)
            
            if score > 0:
                intent_scores[response_type] = {
                    'score': score,
                    'patterns': matching_patterns
                }
        
        # Determine primary intent
        if not intent_scores:
            # Default fallback logic
            if len(query_lower.split()) <= 3 and not any(re.search(p, query_lower) for p in self.data_requiring_patterns):
                primary_intent = ResponseType.CONVERSATIONAL
                confidence = 0.7
            else:
                primary_intent = ResponseType.DATA_QUERY
                confidence = 0.5
        else:
            # Get highest scoring intent
            primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k]['score'])
            max_score = intent_scores[primary_intent]['score']

            confidence = min(0.9, 0.3 + (max_score * 0.2))

        # If the intent is comparison, but there are also visualization keywords, promote to visualization
        if primary_intent == ResponseType.COMPARISON and ResponseType.VISUALIZATION in intent_scores:
            primary_intent = ResponseType.VISUALIZATION
            confidence += 0.1 # Boost confidence slightly
        
        # Determine if data is required
        requires_data = any(re.search(p, query_lower) for p in self.data_requiring_patterns)
        
        # Determine visualization type if applicable
        visualization_type = None
        if primary_intent == ResponseType.VISUALIZATION:
            for viz_type, patterns in self.visualization_patterns.items():
                if any(re.search(p, query_lower) for p in patterns):
                    visualization_type = viz_type
                    break
            if not visualization_type:
                # If it's a comparison, default to scatter, otherwise line
                if ResponseType.COMPARISON in intent_scores:
                    visualization_type = 'scatter'
                else:
                    visualization_type = 'line'
        elif primary_intent == ResponseType.MAP:
            visualization_type = 'map'
        
        # Generate reasoning
        reasoning = self._generate_reasoning(primary_intent, intent_scores.get(primary_intent, {}))
        
        return IntentResult(
            response_type=primary_intent,
            confidence=confidence,
            visualization_type=visualization_type,
            requires_data=requires_data,
            reasoning=reasoning
        )
    
    def _generate_reasoning(self, intent: ResponseType, score_info: Dict) -> str:
        """Generate human-readable reasoning for the intent decision"""
        if not score_info:
            return f"Defaulted to {intent.value} based on query structure"
        
        patterns = score_info.get('patterns', [])
        return f"Detected {intent.value} intent (confidence: {score_info['score']}) based on patterns: {patterns[:2]}"

# Test function
def test_intent_detection():
    """Test the intent detection with various queries"""
    service = IntentDetectionService()
    
    test_queries = [
        "thanks",
        "how are you",
        "Show me temperature data from float 5904471",
        "Plot temperature trends over time",
        "Map the locations of floats near Mumbai",
        "Compare salinity between two regions",
        "Give me a summary of all measurements",
        "What can you do?",
        "Draw a scatter plot of temperature vs depth"
    ]
    
    for query in test_queries:
        result = service.analyze_intent(query)
        print(f"Query: '{query}'")
        print(f"  Intent: {result.response_type.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Requires Data: {result.requires_data}")
        if result.visualization_type:
            print(f"  Viz Type: {result.visualization_type}")
        print(f"  Reasoning: {result.reasoning}")
        print()

if __name__ == "__main__":
    test_intent_detection()