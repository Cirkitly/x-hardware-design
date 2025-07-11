import pytest
from unittest.mock import MagicMock, mock_open, patch
from pocketflow import Flow
from nodes import (
    ProjectParserNode,
    CandidateSelectionNode,  # Corrected name
    PlanGeneratorNode,       # Corrected name
    HumanApprovalNode,
    ContextualTestGeneratorNode,
    FileWriterNode,
)

# A reusable fixture that provides a mock project structure for multiple tests.
@pytest.fixture
def mock_shared_state():
    return {
        "project_structure": {
            "sources": {
                "spi.c": {
                    "path": "my_c_project/src/spi.c",
                    "content": "int spi_init() { return 0; }",
                    "dependencies": ["spi.h"]
                },
                "i2c.c": {
                    "path": "my_c_project/src/i2c.c",
                    "content": "int i2c_init() { return 0; }",
                    "dependencies": ["i2c.h"]
                }
            },
            "headers": {
                "spi.h": {"path": "my_c_project/include/spi.h", "content": "#define SPI_OK 0"},
                "i2c.h": {"path": "my_c_project/include/i2c.h", "content": "#define I2C_OK 0"}
            },
            "specs": {}
        },
        "repo_path": "my_c_project"
    }

# --- Test ProjectParserNode ---
@patch("nodes.glob")
@patch("nodes.os.path.isdir", return_value=True)
@patch("nodes.prompt_for_input", return_value="my_c_project")
def test_project_parser_node(mock_prompt, mock_isdir, mock_glob):
    """Verify the project parser correctly finds and reads files."""
    node = ProjectParserNode()
    mock_glob.glob.side_effect = [
        ["my_c_project/src/spi.c"],
        ["my_c_project/include/spi.h"],
        [],
        []
    ]
    m = mock_open(read_data='// Mocked file content\n#include "spi.h"')
    
    with patch("builtins.open", m):
        result = node.exec(None)

    assert "spi.c" in result["sources"]
    assert "spi.h" in result["headers"]
    assert result["sources"]["spi.c"]["dependencies"] == ["spi.h"]


# --- Test CandidateSelectionNode ---
def test_candidate_selection_node(mocker, mock_shared_state):
    """Verify the user's choice is correctly identified."""
    node = CandidateSelectionNode() # Corrected name
    mocker.patch("nodes.prompt_for_choice", return_value=2)
    
    selected_file = node.exec(mock_shared_state["project_structure"])
    
    assert selected_file["path"] == "my_c_project/src/i2c.c"


# --- Test PlanGeneratorNode ---
def test_plan_generator_node(mocker):
    """Verify the plan generator calls the LLM with the correct prompt."""
    node = PlanGeneratorNode() # Corrected name
    mock_llm = mocker.patch("nodes.call_llm", return_value="This is a test plan.")
    inputs = {
        "target_content": "int main() {}",
        "target_filename": "main.c",
        "requirements": "Must work."
    }
    
    node.exec(inputs)
    
    mock_llm.assert_called_once()
    prompt_arg = mock_llm.call_args[0][0]
    assert "int main() {}" in prompt_arg
    assert "main.c" in prompt_arg
    assert "Must work." in prompt_arg


# --- Test HumanApprovalNode ---
def test_human_approval_node_approves(mocker):
    """Verify flow continues when user approves."""
    node = HumanApprovalNode()
    node.flow_control = MagicMock()
    node.flow_control.stop_flow = False
    
    mocker.patch("nodes.prompt_for_confirmation", return_value=True)
    
    node.exec("Test plan")
    
    assert node.flow_control.stop_flow is False

def test_human_approval_node_rejects(mocker):
    """Verify flow stops when user rejects."""
    node = HumanApprovalNode()
    node.flow_control = MagicMock()
    node.flow_control.stop_flow = False
    
    mocker.patch("nodes.prompt_for_confirmation", return_value=False)

    node.exec("Test plan")
    
    assert node.flow_control.stop_flow is True


# --- Test FileWriterNode ---
def test_file_writer_node_writes_new_file(mocker):
    """Verify a new file is written correctly."""
    node = FileWriterNode()
    node.flow_control = MagicMock()
    
    mocker.patch("os.path.exists", return_value=False)
    mocked_open = mock_open()
    mocker.patch("builtins.open", mocked_open)

    inputs = {"filename": "test.c", "content": "```c\nint main() {}\n```"}
    
    result = node.exec(inputs)
    
    mocked_open.assert_called_once_with("test.c", 'w', encoding='utf-8')
    handle = mocked_open()
    handle.write.assert_called_once_with("int main() {}")
    assert "Tests written to" in result

def test_file_writer_node_stops_on_overwrite_rejection(mocker):
    """Verify flow stops if user rejects overwriting an existing file."""
    node = FileWriterNode()
    node.flow_control = MagicMock()
    node.flow_control.stop_flow = False
    
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("nodes.prompt_for_confirmation", return_value=False)
    
    node.prep({
        "target_file": {"path": "my_c_project/src/spi.c"},
        "generated_tests": "some code"
    })
    
    assert node.flow_control.stop_flow is True