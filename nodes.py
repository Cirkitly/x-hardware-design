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

        # --- START OF FIX ---
        # Store the repo_path on the node instance so we can access it in the post() method.
        self.repo_path = repo_path
        # --- END OF FIX ---

        project_structure = {"sources": {}, "headers": {}}
        
        c_files = glob.glob(os.path.join(repo_path, '**/*.c'), recursive=True)
        h_files = glob.glob(os.path.join(repo_path, '**/*.h'), recursive=True)

        for h_path in h_files:
            key = os.path.basename(h_path)
            with open(h_path, 'r') as f:
                project_structure["headers"][key] = {"path": h_path, "content": f.read()}

        for c_path in c_files:
            key = os.path.basename(c_path)
            with open(c_path, 'r') as f:
                content = f.read()
                dependencies = [h for h in project_structure["headers"] if f'#include "{h}"' in content]
                project_structure["sources"][key] = {"path": c_path, "content": content, "dependencies": dependencies}

        return project_structure

    def post(self, shared, prep_res, exec_res):
        shared["project_structure"] = exec_res
        # --- START OF FIX ---
        # Now, save the repo_path to the shared dictionary for later nodes.
        shared["repo_path"] = self.repo_path
        # --- END OF FIX ---


class TestCandidateSelectionNode(Node):
    def prep(self, shared):
        return shared["project_structure"]

    def exec(self, project_structure):
        """Asks the user to select which file to test."""
        print("\nFound the following testable source files:")
        sources = list(project_structure["sources"].keys())
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
        """Generates tests using the code AND its dependency headers as context."""
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
        1.  Generate a complete, compilable C file.
        2.  Include necessary headers (`unity.h`, and the header for the code under test).
        3.  Create tests for success paths and all edge cases (NULL pointers, invalid values, etc.).
        4.  Include `setUp()`, `tearDown()`, and a `main()` function to run the tests.

        Generate the unit test file now.
        """
        return call_llm(prompt)

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
        """Writes the generated tests to a file."""
        filename = inputs["filename"]
        content = inputs["content"]
        
        if "```c" in content:
            # A more robust way to extract code from markdown blocks
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
        return {
            "repo_path": shared["repo_path"],
            "target_source_path": shared["target_file"]["path"],
            "test_file_path": shared["output_status"].split("Tests written to ")[1]
        }
    
    def exec(self, inputs):
        """Generates a simple Makefile to compile and run the test."""
        repo_path = inputs["repo_path"]
        target_src = os.path.relpath(inputs["target_source_path"], repo_path)
        test_src = os.path.relpath(inputs["test_file_path"], repo_path)
        
        makefile_content = f"""
# Basic Makefile for running the generated test
# Assumes Unity is in a ./unity/ directory relative to this Makefile

CC = gcc
UNITY_PATH = ./unity
UNITY_SRC = $(UNITY_PATH)/src/unity.c
INC_DIRS = -I. -I$(UNITY_PATH)/src -I./include

SRC_FILES = {target_src} {test_src} $(UNITY_SRC)
TARGET = test_runner

all: $(TARGET)

$(TARGET): $(SRC_FILES)
	$(CC) -o $(TARGET) $(SRC_FILES) $(INC_DIRS)

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