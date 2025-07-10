# File: cirkitly/flow.py

from pocketflow import Flow
from nodes import (
    ProjectParserNode, 
    TestCandidateSelectionNode, 
    ContextualTestGeneratorNode, 
    TestRefinementNode,  # <-- Import the new node
    FileWriterNode,
    MakefileGeneratorNode
)

def create_repo_testgen_flow():
    """Creates a flow for generating and refining tests for a file within a repo."""
    # Create nodes
    parser_node = ProjectParserNode()
    selector_node = TestCandidateSelectionNode()
    generator_node = ContextualTestGeneratorNode()
    refiner_node = TestRefinementNode()  # <-- Instantiate the new node
    writer_node = FileWriterNode()
    makefile_node = MakefileGeneratorNode()

    # Connect the full pipeline with the new refinement step
    parser_node >> selector_node >> generator_node >> refiner_node >> writer_node >> makefile_node
    
    return Flow(start=parser_node)

repo_testgen_flow = create_repo_testgen_flow()