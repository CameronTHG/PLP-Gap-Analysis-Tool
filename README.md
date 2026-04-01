# SEO Opportunity Finder

This tool helps SEO specialists identify content gaps and optimization opportunities by analyzing keyword data from Ahrefs exports.

## How it Works

The tool takes two CSV files as input:

1.  **Existing Pages & Keywords:** A list of top-ranking keywords for your website's pages.
2.  **Full Topic Attack List:** A comprehensive list of keywords for a specific topic.

The backend logic then compares these two lists to identify keywords that are either underperforming or not targeted at all. The output is a downloadable CSV file with a list of "actions" (`Optimise` or `Create New Page`) for each keyword.

## Project Structure

-   `frontend/`: Contains the HTML, CSS, and JavaScript for the user interface.
-   `backend/`: Contains the Python/Flask application for the backend logic.

## How to Run

### Backend Setup (First Time Only)

1.  **Open your computer's terminal.** (On macOS, search for "Terminal"; on Windows, search for "Command Prompt" or "PowerShell").

2.  **Navigate to the backend directory.** Since the project is on your Desktop, use this command:
    ```bash
    cd Desktop/seo-tool/backend
    ```

3.  **Create a virtual environment and install the required packages.** This command sets up the necessary dependencies.

    **For macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install Flask pandas flask-cors google-generativeai scikit-learn
    ```

    **For Windows:**
    > **Note:** The most common issue on Windows is not having Python installed or not having it in your system's PATH. If you don't have Python, download it from [python.org](https://www.python.org/downloads/) and **make sure to check the box that says "Add Python to PATH"** during installation.

    Open PowerShell and run:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    pip install Flask pandas flask-cors google-generativeai scikit-learn
    ```

### Running the Application

**Step 1: Start the Backend Server**

*   **Open Terminal.**

*   **Navigate to the backend folder:**
    ```bash
    cd ~/Desktop/seo-tool/backend
    ```

*   **(Optional but recommended) Activate your Python virtual environment.**
    If you created one and it's called `venv`, activate it.

    **For macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```
    **For Windows (in PowerShell):**
    ```powershell
    .\venv\Scripts\activate
    ```
    If you're unsure, check for a `venv` folder first using `ls` (macOS/Linux) or `dir` (Windows).

*   **Run the backend server:**
    ```bash
    python app.py
    ```
    🟡 You should see something like:
    ```
     * Running on http://127.0.0.1:5001/ (Press CTRL+C to quit)
    ```
    **Keep that Terminal window open.** The server must stay running for your frontend or requests to work.

**Step 2: Use the Frontend Application**

1.  **Open the frontend.** Open the `frontend/index.html` file in your web browser.
2.  **Enter your Gemini API Key.** Paste your key into the input box at the top of the page.
3.  **Upload your files.**
    *   Upload your "Existing Pages & Keywords" CSV in Step 1.
    *   Upload your "Full Topic Attack List" CSV in Step 2.
4.  **Run the analysis.** Click the "Find Opportunities" button.
5.  **Download results.** Once the analysis is complete, a "Download Opportunities CSV" button will appear. Click it to download your results.
