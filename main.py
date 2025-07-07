from flow import repo_testgen_flow
import sys

def main():
    """
    Main function to run the repository test generation bot.
    """
    print("Welcome to Cirkitly: Repository Test Generator")
    
    shared = {}
    repo_testgen_flow.run(shared)
    
    print("\n" + "="*20)
    print("Test Generation Complete!")
    print(shared.get("output_status", "File writer did not run."))
    print(shared.get("makefile_status", "Makefile generator did not run."))
    print("="*20 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)