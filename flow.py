from pocketflow import Flow
from nodes import (
    ProjectParserNode, 
    CandidateSelectionNode,      # Renamed
    RequirementExtractionNode,
    PlanGeneratorNode,           # Renamed
    HumanApprovalNode,
    ContextualTestGeneratorNode, 
    FinalReviewerNode,
    FileWriterNode,
    MakefileGeneratorNode
)

def create_repo_testgen_flow():
    parser_node = ProjectParserNode()
    selector_node = CandidateSelectionNode()         # Renamed
    extractor_node = RequirementExtractionNode()
    plan_generator_node = PlanGeneratorNode()        # Renamed
    human_approval_node = HumanApprovalNode()
    generator_node = ContextualTestGeneratorNode()
    reviewer_node = FinalReviewerNode()
    writer_node = FileWriterNode()
    makefile_node = MakefileGeneratorNode()

    # The new, collaborative "plan-first" flow
    (parser_node >> selector_node >> extractor_node >> plan_generator_node >> 
     human_approval_node >> generator_node >> reviewer_node >> 
     writer_node >> makefile_node)
    
    return Flow(start=parser_node)

repo_testgen_flow = create_repo_testgen_flow()