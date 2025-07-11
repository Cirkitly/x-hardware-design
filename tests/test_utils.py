import pytest
import requests
from unittest.mock import MagicMock, mock_open, patch

from utils.call_llm import call_llm
from utils.get_embedding import get_embedding

# --- Tests for call_llm (Updated to patch the correct import source) ---
@patch('openai.AzureOpenAI')
def test_call_llm_success(mock_azure_openai):
    """Test call_llm on a successful API call using the AzureOpenAI client."""
    mock_client_instance = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Hello, this is a test."
    
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_azure_openai.return_value = mock_client_instance

    result = call_llm("test prompt", use_cache=False)

    assert result == "Hello, this is a test."
    mock_client_instance.chat.completions.create.assert_called_once()


@patch('openai.AzureOpenAI')
def test_call_llm_api_error(mock_azure_openai):
    """Test call_llm when the API client raises an error."""
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.side_effect = Exception("Azure API Error")
    mock_azure_openai.return_value = mock_client_instance

    with pytest.raises(Exception, match='Azure API Error'):
        call_llm("test prompt", use_cache=False)


def test_call_llm_uses_cache(mocker):
    """Test that call_llm uses the cache and avoids an API call."""
    prompt = "cached question"
    cached_response = "This is from the cache"
    cache_content = f'{{"{prompt}": "{cached_response}"}}'

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=cache_content))
    mock_client = mocker.patch("openai.AzureOpenAI")

    result = call_llm(prompt, use_cache=True)

    assert result == cached_response
    mock_client.assert_not_called()


# --- Tests for get_embedding (Unchanged, still uses requests) ---
def test_get_embedding_success(mocker):
    """Test get_embedding on a successful API call."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mocker.patch("requests.post", return_value=mock_response)

    result = get_embedding("test text")

    assert result == [0.1, 0.2, 0.3]
    requests.post.assert_called_once()
    assert requests.post.call_args.args[0] == "http://localhost:11434/api/embeddings"


def test_get_embedding_api_error(mocker):
    """Test get_embedding when the API returns an error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal server error"}
    mocker.patch("requests.post", return_value=mock_response)

    with pytest.raises(requests.exceptions.HTTPError, match='Ollama API Error: Internal server error'):
        get_embedding("test text")