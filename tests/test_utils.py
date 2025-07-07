import pytest
import requests
from unittest.mock import MagicMock, mock_open

from utils.call_llm import call_llm
from utils.get_embedding import get_embedding

# --- Tests for call_llm ---

def test_call_llm_success(mocker):
    """Test call_llm on a successful API call."""
    # Arrange: Mock the requests.post call
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Hello, this is a test."}
    mocker.patch("requests.post", return_value=mock_response)

    # Act: Call the function
    result = call_llm("test prompt", use_cache=False)

    # Assert: Check that the function returns the correct text
    assert result == "Hello, this is a test."
    requests.post.assert_called_once()

def test_call_llm_api_error(mocker):
    """Test call_llm when the API returns an error."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": "Model not found"}
    mocker.patch("requests.post", return_value=mock_response)

    # Act & Assert: Check that our specific HTTPError is raised
    with pytest.raises(requests.exceptions.HTTPError, match='Ollama API Error: Model not found'):
        call_llm("test prompt", use_cache=False)

def test_call_llm_uses_cache(mocker):
    """Test that call_llm uses the cache and avoids an API call."""
    # Arrange: Mock file system functions to simulate a cache hit
    prompt = "cached question"
    cached_response = "This is from the cache"
    cache_content = f'{{"{prompt}": "{cached_response}"}}'

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=cache_content))
    mock_post = mocker.patch("requests.post") # Mock post to ensure it's not called

    # Act
    result = call_llm(prompt, use_cache=True)

    # Assert
    assert result == cached_response
    mock_post.assert_not_called() # Verify no network call was made


# --- Tests for get_embedding ---

def test_get_embedding_success(mocker):
    """Test get_embedding on a successful API call."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mocker.patch("requests.post", return_value=mock_response)

    # Act
    result = get_embedding("test text")

    # Assert
    assert result == [0.1, 0.2, 0.3]
    requests.post.assert_called_once()
    # Check if the correct endpoint was called
    assert requests.post.call_args.args[0] == "http://localhost:11434/api/embeddings"


def test_get_embedding_api_error(mocker):
    """Test get_embedding when the API returns an error."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal server error"}
    mocker.patch("requests.post", return_value=mock_response)

    # Act & Assert
    with pytest.raises(requests.exceptions.HTTPError, match='Ollama API Error: Internal server error'):
        get_embedding("test text")