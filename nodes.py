import os
import glob
from pocketflow import Node
from utils.call_llm import call_llm
from utils.get_embedding import get_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tui import console, print_step, prompt_for_input, prompt_for_choice, status, prompt_for_confirmation, print_plan

# ... (ProjectParserNode is unchanged) ...
class ProjectParserNode(Node):
    def exec(self, _):
        """Scans a repo for source files and the project for spec files."""
        repo_path = prompt_for_input("Enter the path to the C project", default="my_c_project")
        if not os.path.isdir(repo_path):
            raise NotADirectoryError(f"Path is not a valid directory: {repo_path}")
        self.repo_path = repo_path

        excluded_dirs = ['/unity/', '/tests/']
        all_c_files = glob.glob(os.path.join(repo_path, '**/*.c'), recursive=True)
        source_files = []
        for f in all_c_files:
            normalized_path = f.replace('\\', '/')
            if os.path.basename(normalized_path).startswith('test_'):
                continue
            if any(excluded in normalized_path for excluded in excluded_dirs):
                continue
            source_files.append(f)
        
        project_structure = {"sources": {}, "headers": {}, "specs": {}}
        c_files = source_files
        h_files = glob.glob(os.path.join(repo_path, '**/*.h'), recursive=True)
        
        spec_dir = 'specs'
        spec_files = []
        if os.path.isdir(spec_dir):
            spec_files = glob.glob(os.path.join(spec_dir, '**/*.md'), recursive=True)
            spec_files += glob.glob(os.path.join(spec_dir, '**/*.txt'), recursive=True)
        
        for spec_path in spec_files:
            key = os.path.basename(spec_path)
            with open(spec_path, 'r', encoding='utf-8') as f:
                project_structure["specs"][key] = {"path": spec_path, "content": f.read()}

        for h_path in h_files:
            key = os.path.basename(h_path)
            with open(h_path, 'r', encoding='utf-8') as f:
                project_structure["headers"][key] = {"path": h_path, "content": f.read()}
        for c_path in c_files:
            key = os.path.basename(c_path)
            with open(c_path, 'r', encoding='utf-8') as f:
                content = f.read()
                dependencies = [h for h in project_structure["headers"] if f'#include "{h}"' in content]
                project_structure["sources"][key] = {"path": c_path, "content": content, "dependencies": dependencies}
        return project_structure

    def post(self, shared, prep_res, exec_res):
        shared["project_structure"] = exec_res
        shared["repo_path"] = self.repo_path


# --- RENAMED: from TestCandidateSelectionNode ---
class CandidateSelectionNode(Node):
    def prep(self, shared):
        return shared["project_structure"]

    def exec(self, project_structure):
        print_step("Found the following source files:")
        sources = list(project_structure["sources"].keys())
        
        if not sources:
            console.print("[warning]No testable source files found after filtering.[/warning]")
            raise FileNotFoundError("No valid source files found to test.")

        for i, src in enumerate(sources):
            console.print(f"  [prompt][{i+1}][/prompt] [path]{src}[/path]")
        
        choice = prompt_for_choice("Which file would you like to generate tests for?", sources)
        
        selected_file = sources[choice-1]
        return project_structure["sources"][selected_file]
    
    def post(self, shared, prep_res, exec_res):
        shared["target_file"] = exec_res

# ... (RequirementExtractionNode is unchanged) ...
class RequirementExtractionNode(Node):
    def prep(self, shared):
        return {
            "target_filename": os.path.basename(shared["target_file"]["path"]),
            "specs": shared["project_structure"]["specs"]
        }

    def exec(self, inputs):
        specs = inputs.get("specs", {})
        if not specs:
            print_step("No specification documents found in 'specs/' directory.")
            return "No specific requirements found."

        with status("Analyzing requirements..."):
            target_filename = inputs["target_filename"]
            query = f"What are the functional and error-handling requirements for the code in {target_filename}?"
            query_embedding = get_embedding(query)
            spec_contents = [doc["content"] for doc in specs.values()]
            spec_embeddings = [get_embedding(doc) for doc in spec_contents]

            if not spec_embeddings:
                return "No specific requirements found."

            similarities = cosine_similarity([query_embedding], spec_embeddings)[0]
            most_relevant_idx = np.argmax(similarities)
            
            if similarities[most_relevant_idx] < 0.3:
                return "No specific requirements found."
            
            print_step("Found relevant requirements.")
            return spec_contents[most_relevant_idx]

    def post(self, shared, prep_res, exec_res):
        shared["relevant_requirements"] = exec_res

# --- RENAMED: from TestPlanGeneratorNode ---
class PlanGeneratorNode(Node):
    def prep(self, shared):
        return {
            "target_content": shared["target_file"]["content"],
            "target_filename": os.path.basename(shared["target_file"]["path"]),
            "requirements": shared.get("relevant_requirements", "No specific requirements provided.")
        }

    def exec(self, inputs):
        with status("Generating a test plan for your review..."):
            prompt = f"""
            You are a senior C software test engineer. Your task is to create a test plan for the C source file `{inputs['target_filename']}`.

            Analyze the provided source code and functional requirements, then create a clear, concise test plan in Markdown format.
            For each function in the source file, list the specific test cases you will create. Each test case should be a bullet point describing its purpose (e.g., testing success, error handling, edge cases).

            ### Functional Requirements ###
            {inputs['requirements']}

            ### Source Code to Plan For ###
            ```c
            {inputs['target_content']}
            ```

            Return ONLY the Markdown test plan. Do not write any C code yet.
            """
            response = call_llm(prompt, use_cache=False)
        print_step("Test plan generated.")
        return response

    def post(self, shared, prep_res, exec_res):
        shared["test_plan"] = exec_res

# ... (The rest of the file: HumanApprovalNode, ContextualTestGeneratorNode, etc., are unchanged) ...
class HumanApprovalNode(Node):
    def prep(self, shared):
        return shared["test_plan"]

    def exec(self, test_plan):
        console.print()
        print_plan(test_plan)
        console.print()

        if not prompt_for_confirmation("Does this test plan look correct? Shall I proceed with generating the code?"):
            print_step("Aborting based on user input. No code will be generated.")
            self.flow_control.stop_flow = True # Stops the flow
        
        return test_plan # Pass the approved plan through
    
    def post(self, shared, prep_res, exec_res):
        pass

class ContextualTestGeneratorNode(Node):
    def prep(self, shared):
        return {
            "target_content": shared["target_file"]["content"],
            "target_filename": os.path.basename(shared["target_file"]["path"]),
            "approved_plan": shared["test_plan"]
        }
    
    def exec(self, inputs):
        console.print("\n[info]This next step involves a large request to the AI and may take a few minutes. Please be patient...[/info]")
        with status("Generating test code based on the approved plan..."):
            prompt = f"""
            You are an expert C unit testing engineer. Your task is to write a complete C test file that implements the following approved test plan for the source code in `{inputs['target_filename']}`.

            **Implement this EXACT test plan:**
            {inputs['approved_plan']}

            **Base the tests on this source code:**
            ```c
            {inputs['target_content']}
            ```
            
            **CRITICAL INSTRUCTIONS:**
            1.  Write a complete C file containing Unity tests. The code must be complete and syntactically correct.
            2.  Include the necessary headers: `#include "unity.h"`, `#include "spi.h"`.
            3.  **To access the internal state for testing, you MUST declare the global variables from `spi.c` as `extern`. Add these lines at the top of the test file:**
                ```c
                extern spi_state_t g_spi_state;
                extern spi_config_t g_spi_config;
                ```
            4.  Implement the `setUp()` function to reset the state before each test.
            """
            response = call_llm(prompt, max_tokens=4096)
        print_step("Initial draft generated.")
        return response

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res


class FinalReviewerNode(Node):
    def prep(self, shared):
        return {"generated_code": shared["generated_tests"]}

    def exec(self, inputs):
        with status("Performing final syntax and structural review..."):
            review_prompt = f"""
            You are a C language syntax checker and fixer. Your only job is to ensure the following code is valid, compilable C.

            **Code to fix:**
            ```c
            {inputs['generated_code']}
            ```

            **Fix these common errors:**
            1.  **Completeness:** Ensure no functions are left unfinished. Check for hanging curly braces or incomplete statements.
            2.  **Includes:** Ensure necessary headers like `unity.h`, `spi.h`, `<stdlib.h>` are included.
            3.  **Global Variable Access:** Ensure the test file declares `extern spi_state_t g_spi_state;` and `extern spi_config_t g_spi_config;` at the top level to access the module's internal state.
            4.  **Struct Initializers:** Ensure all `spi_config_t` structs are initialized using designated initializers, like `spi_config_t my_config = {{.mode = 0, .speed_hz = 1000000}};`. This prevents overflow warnings.
            5.  **Mandatory Functions:** Ensure `setUp(void)`, `tearDown(void)`, and a `main` function with `RUN_TEST` calls exist.

            Return ONLY the complete, corrected C code in a single markdown block.
            """
            response = call_llm(review_prompt, use_cache=False, max_tokens=4096)
        print_step("Final review complete.")
        return response

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res


class FileWriterNode(Node):
    def prep(self, shared):
        original_path = shared["target_file"]["path"]
        dir_name = os.path.dirname(original_path)
        base_name = os.path.basename(original_path)
        base, ext = os.path.splitext(base_name)
        test_filename = os.path.join(dir_name, f"test_{base}.c")
        
        if os.path.exists(test_filename):
            if not prompt_for_confirmation(f"[warning]File [path]{test_filename}[/path] already exists. Overwrite?[/warning]", default=False):
                print_step("Aborting. No files were written.")
                self.flow_control.stop_flow = True

        return {"filename": test_filename, "content": shared["generated_tests"]}
    
    def exec(self, inputs):
        filename = inputs["filename"]
        content = inputs["content"]
        
        if "```c" in content:
            parts = content.split("```c")
            if len(parts) > 1:
                content = parts[1].split("```")[0]
        
        content = content.strip()
            
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Tests written to [path]{filename}[/path]"

    def post(self, shared, prep_res, exec_res):
        shared["output_status"] = exec_res

class MakefileGeneratorNode(Node):
    def prep(self, shared):
        test_file_path = shared["output_status"].split("[path]")[1].split("[/path]")[0]
        
        return {
            "repo_path": shared["repo_path"],
            "target_source_path": shared["target_file"]["path"],
            "test_file_path": test_file_path
        }
    
    def exec(self, inputs):
        repo_path = inputs["repo_path"]
        target_src = os.path.relpath(inputs["target_source_path"], repo_path)
        test_src = os.path.relpath(inputs["test_file_path"], repo_path)
        
        makefile_content = f"""
# Basic Makefile for running the generated test
# Assumes Unity is in a ./unity/ directory relative to this Makefile

CC = gcc
# ADDED -DTEST to CFLAGS to expose test-only functions
CFLAGS = -std=c99 -Wall -Wextra -pedantic -DTEST

UNITY_PATH = ./unity
UNITY_SRC = $(UNITY_PATH)/src/unity.c

# Include paths for all necessary headers
INC_DIRS = -I. -I$(UNITY_PATH)/src -I./include

# All source files that need to be compiled
SRC_FILES = {target_src} {test_src} $(UNITY_SRC)

# The name of the final executable
TARGET = test_runner

# Default target
all: $(TARGET)

# Rule to build the test runner executable
$(TARGET): $(SRC_FILES)
	$(CC) $(CFLAGS) $(INC_DIRS) -o $(TARGET) $(SRC_FILES)

# Rule to run the tests
run: $(TARGET)
	./$(TARGET)

# Rule to clean up build artifacts
clean:
	rm -f $(TARGET)
"""
        makefile_path = os.path.join(repo_path, "Makefile.test")
        with open(makefile_path, 'w') as f:
            f.write(makefile_content.strip())
            
        return f"Makefile generated at [path]{makefile_path}[/path]"
    
    def post(self, shared, prep_res, exec_res):
        shared["makefile_status"] = exec_res