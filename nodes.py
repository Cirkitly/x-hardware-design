import os
import glob
from pocketflow import Node
from utils.call_llm import call_llm
from utils.get_embedding import get_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- START OF NEW DOCUMENT LOADING LOGIC ---
def load_knowledge_documents(path="knowledge_source"):
    """Loads all .txt files from a given directory."""
    docs = []
    filepaths = glob.glob(os.path.join(path, "*.txt"))
    print(f"Found {len(filepaths)} knowledge document(s)...")
    for filepath in filepaths:
        with open(filepath, 'r', encoding='utf-8') as f:
            docs.append(f.read())
    return docs

# Load documents from the directory
KNOWLEDGE_DOCS = load_knowledge_documents()
# --- END OF NEW DOCUMENT LOADING LOGIC ---

# This is a one-time setup to "index" our knowledge base.
# In a real app, this would be done offline and stored in a vector DB.
print("Pre-calculating embeddings for knowledge base...")
if KNOWLEDGE_DOCS:
    KNOWLEDGE_EMBEDDINGS = np.array([get_embedding(doc) for doc in KNOWLEDGE_DOCS])
    print("...done.")
else:
    KNOWLEDGE_EMBEDDINGS = np.array([])
    print("...knowledge base is empty.")


class GetQuestionNode(Node):
    def exec(self, _):
        # Get question directly from user input
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question
        shared["question"] = exec_res
        return "default"  # Go to the next node

class EmbeddingNode(Node):
    def prep(self, shared):
        return shared["question"]

    def exec(self, question):
        # Generate an embedding for the user's question
        return get_embedding(question)

    def post(self, shared, prep_res, exec_res):
        shared["question_embedding"] = exec_res

class RetrievalNode(Node):
    def prep(self, shared):
        return shared["question_embedding"]
    
    def exec(self, question_embedding):
        # If there are no documents, return a helpful message.
        if len(KNOWLEDGE_DOCS) == 0:
            return "No documents found in the knowledge base."
            
        # Find the most similar document from our knowledge base
        query_embedding = np.array(question_embedding).reshape(1, -1)
        similarities = cosine_similarity(query_embedding, KNOWLEDGE_EMBEDDINGS)
        
        # Get the index of the most similar document
        most_similar_idx = np.argmax(similarities)
        
        # Retrieve the document text
        return KNOWLEDGE_DOCS[most_similar_idx]

    def post(self, shared, prep_res, exec_res):
        shared["retrieved_context"] = exec_res

class AnswerNode(Node):
    def prep(self, shared):
        # Read question AND context from shared
        return {
            "question": shared["question"],
            "context": shared["retrieved_context"]
        }
    
    def exec(self, inputs):
        # Create an augmented prompt for the LLM
        prompt = f"""
        Based on the following context, answer the user's question.
        If the context is not relevant, answer based on your general knowledge.

        Context:
        "{inputs['context']}"

        Question:
        "{inputs['question']}"
        """
        # Call LLM to get the answer
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # Store the answer in shared
        shared["answer"] = exec_res