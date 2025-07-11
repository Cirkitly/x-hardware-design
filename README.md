# Cirkitly: Your AI-Powered C Test Copilot

Welcome to Cirkitly! This is an AI assistant that collaborates with you to write robust unit tests for your C code. Instead of just generating code, Cirkitly first proposes a detailed test plan for your approval, ensuring you are always in control.

![Cirkitly Demo](assets/demo.gif)

### The New Workflow (The Magic)

Cirkitly acts as your partner, following a professional test development process:

1.  **Scans Your Project:** It finds all your `.c` and `.h` source files.
2.  **Proposes a Test Plan:** After you select a file, the AI analyzes the source code and any relevant specifications. It then presents you with a detailed, human-readable test plan, outlining every test case it intends to write.
3.  **Gets Your Approval:** You review the plan. If it's correct and complete, you give the green light. This ensures the AI builds exactly what you want.
4.  **Writes the Test Code:** The AI now writes a complete `test_*.c` file that precisely implements the approved plan, covering success paths, error handling, and edge cases.
5.  **Creates a Build File:** It also generates a `Makefile.test` so you can immediately compile and run your new tests.

---

### Requirements

1.  **Python:** You'll need Python 3.10 or newer.
2.  **A C Compiler:** A `gcc` compatible compiler is needed to run the generated tests.
3.  **An AI Backend:** You need access to an AI model, either locally via Ollama or through the cloud via Azure OpenAI.

---

### Step-by-Step Installation & Configuration

#### Step 1: Get the Cirkitly Code

```bash
# Clone the repository from GitHub
git clone https://github.com/Cirkitly/x-hardware-design

# Navigate into the project directory
cd x-hardware-design
```

#### Step 2: Install Python Packages

```bash
# Install all required Python packages
pip install -r requirements.txt
```

#### Step 3: Configure the AI Backend

Cirkitly needs API keys and endpoint information to communicate with an AI. This is stored in a `.env` file. First, copy the example file:

```bash
cp .env.example .env
```

Now, open the new `.env` file and fill it out according to **one** of the options below.

---

##### **Option A: Azure OpenAI (Recommended for Speed & Power)**

Edit your `.env` file to look like this, replacing the placeholder values with your actual Azure credentials.

```dotenv
# .env file for Azure

AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-azure-openai-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# The DEPLOYMENT name is not the model name (e.g., gpt-4), 
# but the custom name you gave the model when you deployed it in Azure.

LOG_DIR=logs
```

---

##### **Option B: Ollama (Free, Private, and Local)**

If you prefer to run models locally, first download and run [Ollama](https://ollama.com/). Then, pull the required models:

```bash
# 1. Download the main language model (for writing code)
ollama pull llama3

# 2. Download the embedding model (for understanding text)
ollama pull mxbai-embed-large
```

The default `.env.example` is already set up for Ollama, so you don't need to make any changes to your `.env` file.

---

### How to Use It (The Fun Part!)

#### Step 1: Prepare Your C Project

Cirkitly works with standard C project layouts. The included `my_c_project` is a great starting point.

```
my_c_project/
├── include/
│   └── spi.h       <-- Your header files
└── src/
    └── spi.c       <-- Your source code
```

#### Step 2: Run Cirkitly

From the main `cirkitly` directory, run the program:

```bash
python main.py
```

#### Step 3: Follow the Prompts

1.  `Enter the path to the C project:`
    *   Press Enter to accept the default (`my_c_project`).

2.  `Which file would you like to generate tests for?`
    *   It will show you a numbered list. Type the number for `spi.c` and press Enter.

#### Step 4: Approve the Test Plan

Cirkitly will now present you with a detailed Markdown plan. Review the proposed test cases. If you're happy with the plan, approve it to proceed.

```text
Does this test plan look correct? Shall I proceed with generating the code? [y/n] (y): y
```

#### Step 5: Get the Results!

The AI will generate the code and tell you when it's done.

```
==================================================
Cirkitly Task Complete!
  - Tests written to my_c_project/src/test_spi.c
  - Makefile generated at my_c_project/Makefile.test
==================================================
```

---

### How to Run Your New Tests

You've generated the tests, now let's run them!

#### Step 1: Get the Unity Testing Framework

The generated tests use **Unity**, a popular C testing framework. You only need to do this once per C project.

```bash
# Navigate into your C project
cd my_c_project

# Clone the Unity framework from GitHub into a folder named "unity"
git clone https://github.com/ThrowTheSwitch/Unity.git unity
```

#### Step 2: Compile and Run!

The `Makefile.test` that Cirkitly created does all the hard work.

```bash
make -f Makefile.test run
```

You should see the tests compile and run, ending with a message like this:

```
-----------------------
17 Tests 0 Failures 0 Ignored
OK
```

**Congratulations! You've successfully used an AI copilot to write and run tests for your C code!**

---

### Troubleshooting

*   **API / Network Errors (Azure):** If the program hangs or shows a timeout error, double-check your `.env` file for typos in the endpoint and API key. Also, ensure your network firewall allows outbound connections to `*.openai.azure.com`.
*   **Connection Errors (Ollama):** Make sure the Ollama application is running on your computer before starting Cirkitly.
*   **`File not found`:** Make sure you typed the correct path to your project folder (e.g., `my_c_project`).
*   **C Compilation Errors:** While the new workflow makes this much less likely, the AI can still occasionally make a small mistake. If `make` fails, the C compiler error message will usually point to the exact line in `test_spi.c` that needs a minor fix.