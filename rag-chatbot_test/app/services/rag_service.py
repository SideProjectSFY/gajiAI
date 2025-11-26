"""
RAG Service - Stub implementation for testing
This file is a temporary stub to allow imports to succeed during testing.
The actual implementation will be done in a future story.
"""

class RAGService:
    """Stub RAG Service class"""
    
    def __init__(self, collection_name: str = None, gemini_api_key: str = None, **kwargs):
        """Initialize stub RAG service - accepts any parameters for compatibility"""
        self.collection_name = collection_name
        self.gemini_api_key = gemini_api_key
    
    async def query(self, query: str):
        """Stub query method"""
        raise NotImplementedError("RAG Service not yet implemented")
    
    def generate_hybrid_response(self, user_message: str, scenario_context: str = None, 
                                 book_id: str = None, conversation_history: list = None):
        """Stub hybrid response generation"""
        return "This is a stub response from RAG Service.", {"rag_used": False, "stub": True}
    
    def generate_response_stream(self, user_message: str, scenario_context: str = None,
                                 book_id: str = None, conversation_history: list = None, top_k: int = 5):
        """Stub streaming response"""
        stub_message = "This is a stub streaming response from RAG Service."
        for word in stub_message.split():
            yield word + " "
    
    def generate_response_without_rag(self, user_message: str, scenario_context: str = None,
                                     conversation_history: list = None):
        """Stub response without RAG"""
        return "This is a stub response without RAG."
    
    def search_relevant_passages(self, query: str, book_id: str = None, top_k: int = 5):
        """Stub passage search"""
        return [
            {
                "text": "This is a stub passage.",
                "metadata": {"book_id": book_id or "unknown", "stub": True}
            }
        ]
