import pytest
from flow import create_qa_flow

@pytest.fixture
def mock_flow_dependencies(mocker):
    """Mocks all external and slow dependencies for a full flow run."""
    # Mock user input
    mocker.patch('builtins.input', return_value="What is Cirkitly?")
    # Mock embedding generation
    mocker.patch('nodes.get_embedding', return_value=[0.1, 0.2, 0.3])
    # Mock knowledge base and retrieval logic to be predictable
    mocker.patch('nodes.KNOWLEDGE_DOCS', ["Test context about Cirkitly"])
    mocker.patch('nodes.KNOWLEDGE_EMBEDDINGS', [[0.1, 0.2, 0.3]]) # Exact match
    # Mock the final LLM call
    mocker.patch('nodes.call_llm', return_value="The final answer is Cirkitly.")

def test_qa_flow_end_to_end(mock_flow_dependencies):
    """
    Tests the entire RAG flow from question to answer, mocking external APIs.
    """
    # Arrange: Create the flow and an initial empty shared state
    qa_flow = create_qa_flow()
    shared = {}
    
    # Act: Run the flow. The mocked input will be used.
    qa_flow.run(shared)
    
    # Assert: Check the final state of the 'shared' dictionary
    # 1. Was the question stored correctly?
    assert shared.get("question") == "What is Cirkitly?"
    
    # 2. Was the question embedding created?
    assert shared.get("question_embedding") == [0.1, 0.2, 0.3]
    
    # 3. Was the correct context retrieved?
    assert shared.get("retrieved_context") == "Test context about Cirkitly"
    
    # 4. Was the final answer generated and stored?
    assert shared.get("answer") == "The final answer is Cirkitly."