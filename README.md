# Cirkitly: Your AI-Powered C Test Generator

Welcome to Cirkitly! This is an AI assistant that automatically writes unit tests for your C code. You give it a C project, and it gives you back a test file that you can immediately compile and run.

### What It Does (The Magic)

1.  **Reads Your Project:** Cirkitly scans your project folder to find all your `.c` and `.h` files.
2.  **Asks You What to Test:** It shows you a list of your source files and asks you which one you want to create tests for.
3.  **Thinks Like an Engineer:** It sends your code to a powerful AI (Large Language Model) and tells it to think like an expert C programmer.
4.  **Writes the Test Code:** The AI writes a complete `test_*.c` file, including tests for normal cases (like good inputs) and edge cases (like `NULL` pointers or invalid values).
5.  **Creates a Build File:** It also generates a `Makefile.test` so you don't have to figure out how to compile the new test.

---

### Requirements (What You Need Before You Start)

1.  **Python:** You'll need Python 3.10 or newer.
2.  **Ollama (The AI Brain):** This project uses a free, open-source tool called **Ollama** to run the AI models on your own computer.
    *   **What it is:** Ollama lets you download and use powerful AIs without needing an account or paying for an API.
    *   **How to get it:** Download it from the official website: [https://ollama.com/](https://ollama.com/)

---

### Step-by-Step Installation Guide

#### Step 1: Get the Cirkitly Code

First, you need to download the Cirkitly project files.

```bash
# Clone the repository from GitHub
git clone https://github.com/Cirkitly/x-hardware-design

# Navigate into the project directory
cd x-hardware-design
```

#### Step 2: Set Up the AI Brain (Ollama)

Before you can run Cirkitly, you need to download the two AI models it uses. Make sure Ollama is running, then open your terminal and run these two commands.

```bash
# 1. Download the main language model (for writing code)
ollama pull llama3

# 2. Download the embedding model (for understanding text)
ollama pull mxbai-embed-large
```
> **Note:** This might take a few minutes and will download a few gigabytes of data, but you only have to do this once!

#### Step 3: Install the Python Packages

Cirkitly depends on a few Python libraries. The `requirements.txt` file lists them all.

```bash
# Install all required Python packages
pip install -r requirements.txt
```

---

### 🏃‍♀️ How to Use It (The Fun Part!)

#### Step 1: Prepare Your C Project

Cirkitly needs a C project to test. You can use your own, or start with the example we provide. The structure should look like this:

```
my_c_project/
├── include/
│   └── spi.h       <-- Your header files go here
└── src/
    └── spi.c       <-- Your source code files go here
```
> The repository already includes this `my_c_project` folder for you to try!

#### Step 2: Run Cirkitly

Make sure you are in the main `cirkitly` directory, then run the program.

```bash
python main.py
```

#### Step 3: Follow the Prompts

The program will ask you a couple of questions:

1.  `Enter the path to the repository:`
    *   Type: `my_c_project` and press Enter.

2.  `Which file would you like to generate tests for?`
    *   It will show you a numbered list. Type the number for `spi.c` (e.g., `1`) and press Enter.

#### Step 4: See the Results!

Cirkitly will think for a moment and then tell you it's done.

```
====================
Test Generation Complete!
Tests written to my_c_project/src/test_spi.c
Makefile generated at my_c_project/Makefile.test
====================
```
You now have two new files in your `my_c_project` folder!

---

### How to Run Your New Tests

You've generated the tests, now let's run them to check your C code!

#### Step 1: Get the Unity Testing Tool

The generated tests use a popular C testing tool called **Unity**. You need to download it into your C project folder.

```bash
# Navigate into your C project
cd my_c_project

# Clone the Unity framework from GitHub into a folder named "unity"
git clone https://github.com/ThrowTheSwitch/Unity.git unity
```

#### Step 2: Compile and Run!

The `Makefile.test` that Cirkitly created does all the hard work. Just run this command:

```bash
make -f Makefile.test run
```

You should see the tests compile and then run, ending with a message like this:

```
-----------------------
3 Tests 0 Failures 0 Ignored
OK
```
**Congratulations! You've successfully used AI to write and run tests for your C code!**

---

### Troubleshooting

*   **Error: `Ollama connection error`**: Make sure the Ollama application is running on your computer.
*   **Error: `File not found`**: Make sure you typed the correct path to your project folder (e.g., `my_c_project`).
*   **C compilation error (`make: *** ... Error 1`)**: Sometimes the AI makes a small mistake. Open the generated `test_*.c` file. The C compiler error message will usually tell you exactly which line to fix. This is a normal part of working with AI assistants (this will be solved in the upcoming version of this project).