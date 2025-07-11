# File: cirkitly/flow.py

from pocketflow import Flow
from nodes import (
    ProjectParserNode, 
    TestCandidateSelectionNode, 
    RequirementExtractionNode,
    ContextualTestGeneratorNode, 
    FinalReviewerNode, # New
    HumanReviewNode,   # New
    FileWriterNode,
    MakefileGeneratorNode
)

def create_repo_testgen_flow():
    parser_node = ProjectParserNode()
    selector_node = TestCandidateSelectionNode()
    extractor_node = RequirementExtractionNode()
    generator_node = ContextualTestGeneratorNode()
    reviewer_node = FinalReviewerNode()
    human_node = HumanReviewNode()
    writer_node = FileWriterNode()
    makefile_node = MakefileGeneratorNode()

    # The new, more robust flow
    (parser_node >> selector_node >> extractor_node >> generator_node >> 
     reviewer_node >> human_node >> writer_node >> makefile_node)
    
    return Flow(start=parser_node)

repo_testgen_flow = create_repo_testgen_flow()