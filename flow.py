from pocketflow import Flow
from nodes import (
    ProjectParserNode, 
    TestCandidateSelectionNode, 
    ContextualTestGeneratorNode, 
    FileWriterNode,
    MakefileGeneratorNode
)

def create_repo_testgen_flow():
    """Creates a flow for generating tests for a file within a repo."""
    # Create nodes
    parser_node = ProjectParserNode()
    selector_node = TestCandidateSelectionNode()
    generator_node = ContextualTestGeneratorNode()
    writer_node = FileWriterNode()
    makefile_node = MakefileGeneratorNode()

    # Connect the full pipeline
    parser_node >> selector_node >> generator_node >> writer_node >> makefile_node
    
    return Flow(start=parser_node)

repo_testgen_flow = create_repo_testgen_flow()