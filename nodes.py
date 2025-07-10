import os
import glob
from pocketflow import Node
from utils.call_llm import call_llm

class ProjectParserNode(Node):
    def exec(self, _):
        """Scans a repo, identifies source/header files, and maps dependencies."""
        repo_path = input("Enter the path to the repository: ")
        if not os.path.isdir(repo_path):
            raise NotADirectoryError(f"Path is not a valid directory: {repo_path}")
        self.repo_path = repo_path

        # --- START OF IMPROVEMENT ---
        # Define directories and file patterns to exclude from the test candidate list.
        excluded_dirs = ['/unity/', '/tests/']
        
        # Get all C files recursively.
        all_c_files = glob.glob(os.path.join(repo_path, '**/*.c'), recursive=True)

        # Filter the list to get only relevant application source files.
        source_files = []
        for f in all_c_files:
            # Normalize path separators for consistent matching
            normalized_path = f.replace('\\', '/')
            
            # 1. Exclude files that are already tests.
            if os.path.basename(normalized_path).startswith('test_'):
                continue
            
            # 2. Exclude files from specified directories.
            if any(excluded in normalized_path for excluded in excluded_dirs):
                continue
                
            source_files.append(f)
        # --- END OF IMPROVEMENT ---

        project_structure = {"sources": {}, "headers": {}}
        
        # Use the filtered list of source files.
        c_files = source_files
        h_files = glob.glob(os.path.join(repo_path, '**/*.h'), recursive=True)

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


# --- All other nodes remain the same ---

class TestCandidateSelectionNode(Node):
    def prep(self, shared):
        return shared["project_structure"]

    def exec(self, project_structure):
        print("\nFound the following source files:") # Changed message for clarity
        sources = list(project_structure["sources"].keys())
        
        # Add a check for no found files
        if not sources:
            print("No testable source files found after filtering.")
            print("Please check your project structure and exclusion rules in nodes.py.")
            # We can gracefully exit or raise an error.
            # For now, let's raise an error to stop the flow.
            raise FileNotFoundError("No valid source files found to test.")

        for i, src in enumerate(sources):
            print(f"  [{i+1}] {src}")
        while True:
            try:
                choice = int(input("Which file would you like to generate tests for? "))
                if 1 <= choice <= len(sources):
                    selected_file = sources[choice-1]
                    return project_structure["sources"][selected_file]
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a number.")
    
    def post(self, shared, prep_res, exec_res):
        shared["target_file"] = exec_res

class ContextualTestGeneratorNode(Node):
    def prep(self, shared):
        return {
            "target": shared["target_file"],
            "headers": shared["project_structure"]["headers"]
        }

    def exec(self, inputs):
        print("Generating initial draft of tests...")
        target_code = inputs["target"]["content"]
        header_context = ""
        for dep_header_name in inputs["target"]["dependencies"]:
            header_context += f"// Content of header: {dep_header_name}\n"
            header_context += inputs["headers"][dep_header_name]["content"]
            header_context += "\n\n"
        
        prompt = f"""
        You are an expert in C unit testing for embedded systems, using the Unity test framework.
        Your task is to generate a complete C unit test file for the provided source code.

        You are given the source code to test AND the full content of its required header files for context.
        Use this full context to create accurate tests.

        ### Required Headers Context ###
        {header_context}
        
        ### Source Code to Test ###
        ```c
        {target_code}
        ```

        Guidelines:
        1.  Generate a complete, compilable C file that will not produce any compiler warnings.
        2.  Include necessary headers (`unity.h`, `<stdlib.h>` if using malloc/free, and the header for the code under test).
        3.  Create tests for success paths and all edge cases (NULL pointers, invalid values, etc.).
        4.  Include `setUp()`, `tearDown()`, and a `main()` function.
        5.  The `main()` function MUST use the standard Unity test runner format: `UNITY_BEGIN()`, followed by `RUN_TEST()` for each test function, and finally `return UNITY_END();`.
            **Do not use the Unity Fixture style (`UnityMain`).**

        Generate the complete unit test file now.
        """
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res

class TestRefinementNode(Node):
    def prep(self, shared):
        return {
            "generated_code": shared["generated_tests"],
            "original_code": shared["target_file"]["content"],
        }

    def exec(self, inputs):
        current_code = inputs["generated_code"]
        max_retries = 3

        for i in range(max_retries):
            print(f"Self-correction pass {i + 1}/{max_retries}...")
            
            review_prompt = f"""
            You are a senior C developer and QA engineer performing a code review.
            Your task is to analyze the following C unit test code and identify any potential issues.
            Treat compiler warnings (like 'implicit declaration of function') as errors that must be fixed.

            The original source code being tested is:
            ```c
            {inputs['original_code']}
            ```

            Here is the generated unit test to review:
            ```c
            {current_code}
            ```

            Analyze the unit test for the following issues:
            1.  **Compilation Errors & Warnings:** Will this code compile cleanly? Check for missing headers (e.g., `<stdlib.h>` for `malloc`), typos, or incorrect use of constants.
            2.  **Correct `main` function:** The `main` function MUST use the standard Unity test runner format: `UNITY_BEGIN()`, followed by `RUN_TEST()` for each test function, and finally `return UNITY_END();`. Using the `UnityMain` style is an error.
            3.  **Logic Errors:** Does the test correctly verify the intended behavior? Are the assertions correct?
            4.  **Missing Coverage:** Does the test cover all important edge cases mentioned in the original code's comments or logic?

            **Instructions:**
            -   If you find any errors or warnings, provide a corrected, complete, and final version of the code inside a single C markdown block. Do not provide explanations outside the code block.
            -   If the code is already perfect and has no errors or warnings, respond with ONLY the phrase "The code is correct." and nothing else.
            """

            review_response = call_llm(review_prompt)

            if "The code is correct." in review_response:
                print("Code review passed. No more refinement needed.")
                break
            
            print("Found issues, applying corrections...")
            if "```c" in review_response:
                parts = review_response.split("```c")
                if len(parts) > 1:
                    current_code = parts[1].split("```")[0].strip()
            else:
                current_code = review_response.strip()

        print("Refinement complete.")
        return current_code

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res

class FileWriterNode(Node):
    def prep(self, shared):
        original_path = shared["target_file"]["path"]
        dir_name = os.path.dirname(original_path)
        base_name = os.path.basename(original_path)
        base, ext = os.path.splitext(base_name)
        test_filename = os.path.join(dir_name, f"test_{base}.c")
        
        return {
            "filename": test_filename,
            "content": shared["generated_tests"]
        }
    
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
            
        return f"Tests written to {filename}"

    def post(self, shared, prep_res, exec_res):
        shared["output_status"] = exec_res

class MakefileGeneratorNode(Node):
    def prep(self, shared):
        test_file_path = shared["output_status"].split("Tests written to ", 1)[1]
        
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
CFLAGS = -std=c99 -Wall -Wextra -pedantic
UNITY_PATH = ./unity
UNITY_SRC = $(UNITY_PATH)/src/unity.c
INC_DIRS = -I. -I$(UNITY_PATH)/src -I./include

SRC_FILES = {target_src} {test_src} $(UNITY_SRC)
TARGET = test_runner

all: $(TARGET)

$(TARGET): $(SRC_FILES)
	$(CC) $(CFLAGS) $(INC_DIRS) -o $(TARGET) $(SRC_FILES)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)
"""
        makefile_path = os.path.join(repo_path, "Makefile.test")
        with open(makefile_path, 'w') as f:
            f.write(makefile_content.strip())

        return f"Makefile generated at {makefile_path}"
    
    def post(self, shared, prep_res, exec_res):
        shared["makefile_status"] = exec_res