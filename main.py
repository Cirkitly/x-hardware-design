# File: cirkitly/main.py

from flow import repo_testgen_flow
import sys

def main():
    """
    Main function to run the repository test generation bot.
    """
    print("Welcome to Cirkitly: The AI Test Generation Copilot")
    
    shared = {}
    try:
        repo_testgen_flow.run(shared)
        
        # Cleaned-up final output
        print("\n" + "="*50)
        print("Cirkitly Task Complete!")
        output_status = shared.get('output_status', 'File writer did not run.')
        makefile_status = shared.get('makefile_status', 'Makefile generator did not run.')
        print(f"  - {output_status}")
        print(f"  - {makefile_status}")
        
        if 'repo_path' in shared:
            print("\nTo run your new tests, navigate to the project directory and run:")
            print(f"  cd {shared['repo_path']} && make -f Makefile.test run")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()