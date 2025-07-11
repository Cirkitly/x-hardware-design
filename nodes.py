# File: cirkitly/nodes.py
# This is the complete, corrected, and final version of the file.

import os
import glob
from pocketflow import Node
from utils.call_llm import call_llm
from utils.get_embedding import get_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tui import console, print_step, prompt_for_input, prompt_for_choice, status

def print_code(code):
    """Prints code in a formatted way to the console."""
    console.print(f"[code]\n{code}\n[/code]")

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

class TestCandidateSelectionNode(Node):
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

class ContextualTestGeneratorNode(Node):
    def prep(self, shared):
        return {"target": shared["target_file"], "headers": shared["project_structure"]["headers"], "requirements": shared.get("relevant_requirements", "No specific requirements provided.")}
    
    def exec(self, inputs):
        with status("Generating initial draft of tests..."):
            target_filename = os.path.basename(inputs["target"]["path"])
            target_header = os.path.splitext(target_filename)[0] + ".h"
            prompt = f"""
            You are an expert C unit testing engineer. Generate a comprehensive test suite for the function(s) in `{target_filename}` based on the provided specification and source code.

            ### Functional Requirements from Specification ###
            {inputs["requirements"]}

            ### Source Code to Test ###
            ```c
            {inputs["target"]["content"]}
            ```
            
            **Task:** Write a complete C file containing Unity tests. The tests should be thorough and cover all requirements.
            """
            response = call_llm(prompt)
        print_step("Initial draft generated.")
        return response

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res

class FinalReviewerNode(Node):
    """A final pass to fix C syntax and structural errors."""
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
            1.  **Function Signatures:** Ensure all test function names are valid C identifiers. They must not contain spaces. Example: `void my test()` is WRONG. `void my_test()` is CORRECT.
            2.  **Includes:** Ensure necessary headers like `unity.h`, `spi.h`, `<stdlib.h>` are included.
            3.  **Mandatory Functions:** Ensure `setUp(void)` and `tearDown(void)` exist, even if empty.
            4.  **RUN_TEST calls:** Ensure the arguments to `RUN_TEST()` are valid function names that exist in the file.

            Return ONLY the complete, corrected C code in a single markdown block.
            """
            response = call_llm(review_prompt, use_cache=False)
        print_step("Final review complete.")
        return response

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res

class HumanReviewNode(Node):
    """Shows the final code to the user and asks for approval before writing."""
    def prep(self, shared):
        return shared["generated_tests"]

    def exec(self, generated_code):
        if "```c" in generated_code:
            code_to_show = generated_code.split("```c")[1].split("```")[0].strip()
        else:
            code_to_show = generated_code.strip()

        console.print()
        print_code(code_to_show)
        console.print()

        if not prompt_for_confirmation("Save this generated test file?"):
            print_step("Aborting. No files were written.")
            self.flow_control.stop_flow = True # Stops the flow from proceeding
        
        return generated_code # Pass the code through
    
    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res


class FileWriterNode(Node):
    def prep(self, shared):
        original_path = shared["target_file"]["path"]
        dir_name = os.path.dirname(original_path)
        base_name = os.path.basename(original_path)
        base, ext = os.path.splitext(base_name)
        test_filename = os.path.join(dir_name, f"test_{base}.c")
        
        # Add overwrite guard
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