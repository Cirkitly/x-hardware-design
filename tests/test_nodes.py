import pytest
from nodes import GetQuestionNode, EmbeddingNode, RetrievalNode, AnswerNode

# --- Mocks for external dependencies ---
# We mock the heavyweight 'get_embedding' and 'KNOWLEDGE_EMBEDDINGS' at the module level
# because their initialization is slow. We can override these mocks in specific tests if needed.
@pytest.fixture(autouse=True)
def mock_node_dependencies(mocker):
    """Auto-mock dependencies for all tests in this file."""
    # Mock the embedding function to return a predictable vector
    mocker.patch("nodes.get_embedding", return_value=[0.1] * 1024)
    # Mock the pre-calculated knowledge embeddings
    mocker.patch("nodes.KNOWLEDGE_EMBEDDINGS", [[0.1] * 1024])
    # Mock the LLM call to return a simple response
    mocker.patch("nodes.call_llm", return_value="This is a test answer.")


# --- Test GetQuestionNode ---
def test_get_question_node_exec(mocker):
    """Test GetQuestionNode's exec method captures input."""
    # Arrange
    mocker.patch('builtins.input', return_value="What is Cirkitly?")
    node = GetQuestionNode()
    
    # Act
    result = node.exec(None)
    
    # Assert
    assert result == "What is Cirkitly?"

def test_get_question_node_post():
    """Test GetQuestionNode's post method updates shared state."""
    # Arrange
    node = GetQuestionNode()
    shared = {}
    
    # Act
    node.post(shared, None, "Test Question")
    
    # Assert
    assert shared["question"] == "Test Question"


# --- Test EmbeddingNode ---
def test_embedding_node_prep():
    """Test EmbeddingNode's prep method reads from shared state."""
    # Arrange
    node = EmbeddingNode()
    shared = {"question": "Test Question"}
    
    # Act
    result = node.prep(shared)
    
    # Assert
    assert result == "Test Question"

def test_embedding_node_exec(mocker):
    """Test EmbeddingNode's exec method calls get_embedding."""
    # Arrange
    mock_get_embedding = mocker.patch("nodes.get_embedding")
    node = EmbeddingNode()
    
    # Act
    node.exec("Test Question")
    
    # Assert
    mock_get_embedding.assert_called_once_with("Test Question")

def test_embedding_node_post():
    """Test EmbeddingNode's post method updates shared state."""
    # Arrange
    node = EmbeddingNode()
    shared = {}
    embedding_vector = [0.1, 0.2, 0.3]
    
    # Act
    node.post(shared, None, embedding_vector)
    
    # Assert
    assert shared["question_embedding"] == embedding_vector


# --- Test RetrievalNode ---
def test_retrieval_node_exec(mocker):
    """Test RetrievalNode's exec method finds the most similar doc."""
    # Arrange
    # This test relies on the auto-mocked KNOWLEDGE_EMBEDDINGS.
    # We can also mock cosine_similarity to force a specific outcome.
    mocker.patch("nodes.cosine_similarity", return_value=[[0.9, 0.1, 0.5]])
    mocker.patch("nodes.KNOWLEDGE_DOCS", ["Doc A", "Doc B", "Doc C"])
    node = RetrievalNode()
    
    # Act
    result = node.exec([0.1] * 1024) # Input embedding doesn't matter due to mock
    
    # Assert
    assert result == "Doc A" # Because we mocked similarities to make the first one highest


# --- Test AnswerNode ---
def test_answer_node_prep():
    """Test AnswerNode's prep method gathers context and question."""
    # Arrange
    node = AnswerNode()
    shared = {"question": "Q1", "retrieved_context": "C1"}

    # Act
    result = node.prep(shared)

    # Assert
    assert result == {"question": "Q1", "context": "C1"}


def test_answer_node_exec(mocker):
    """Test AnswerNode's exec method constructs the correct prompt."""
    # Arrange
    mock_call_llm = mocker.patch("nodes.call_llm")
    node = AnswerNode()
    inputs = {"question": "The Question", "context": "The Context"}
    
    # Act
    node.exec(inputs)

    # Assert
    # Check that call_llm was called once with a prompt containing our inputs
    mock_call_llm.assert_called_once()
    prompt_arg = mock_call_llm.call_args[0][0]
    assert "The Question" in prompt_arg
    assert "The Context" in prompt_arg