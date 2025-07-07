from pocketflow import Flow
from nodes import GetQuestionNode, EmbeddingNode, RetrievalNode, AnswerNode

def create_qa_flow():
    """Create and return a RAG question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    embedding_node = EmbeddingNode()
    retrieval_node = RetrievalNode()
    answer_node = AnswerNode()
    
    # Connect nodes in the RAG sequence
    get_question_node >> embedding_node >> retrieval_node >> answer_node
    
    # Create flow starting with the input node
    return Flow(start=get_question_node)

qa_flow = create_qa_flow()