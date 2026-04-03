---
marp: true
theme: default
paginate: true
backgroundColor: #f8f9fa
---

# 1. Resume Analyzer AI
**An Intelligent Retrieval-Augmented Generation (RAG) Platform for HR and Recruitment**

---

# 2. Project Overview
**Resume Analyzer AI** is a state-of-the-art web application designed to significantly reduce the time HR professionals spend evaluating candidates. 

By leveraging **Retrieval-Augmented Generation (RAG)**, Large Language Models (LLMs), and semantic search, the platform allows recruiters to:
- Upload and intelligently parse bulk resumes.
- Instantly retrieve candidate information using conversational queries.
- Automatically find the best matching candidates based on specific skills and years of experience.

---

# 3. Core Modules
The system is divided into four highly-coupled core modules:
- **Authentication Module:** Secures the platform allowing only authorized HR admins to access data.
- **Document Ingestion Engine:** Extracts structured text from PDFs and Word documents, chunks the data, and tags it with candidate sources.
- **Vector Storage & RAG Engine:** Converts text chunks into mathematical embeddings stored persistently, facilitating high-speed semantic queries.
- **Interactive UI Dashboard (Frontend):** Provides a fluid, session-based interface for interacting with the AI using 'Single Resume' or 'Candidate Matcher' workflows.

---

# 4. System Architecture

``![UML Diagram](https://kroki.io/mermaid/png/eJxlUcFqwzAMve8rdBotowx6GewwaJJmLbTMbbLtEHZwEy01Te1gO0sL-fgpTtaGNWAiPT9Jfk_fharTPdcW4uAO6PMLgdImn7gDT6vaoIZQK2lRZl8wmbw0izhmwN6iGN7LQvGsgbDg5jBjy5ELIEL9Q1Wzshy7jn_XbTUEXjKKNithkcJn4hojlDRwD_6e2_HXbcVS5mgskZJLBEyUWAiJHf2Kt3wWhIFKGdf09ISdKZ3CIxB0gg7sioY0pyvGk4UHiHluGpgfd5hlQubJospz-oc8xStquh6X3A3-wNQqHdFB0tgJ60FoUZ5jr29g9D9Lt7NX2FSoz1dXbx0ZDHKXg9y189t1kRh_X8kDiWFaHUvrVaLIWktcBnNJshA1vb43ZMhyc1ar9Wgof1OjhKep162Vbt20NdeHTNUStmhKWiU2vbRfnkPCWA==)``

---

# 5. UML Diagrams (Structural & Behavioral)

### Class Diagram
``![UML Diagram](https://kroki.io/mermaid/png/eJxtUcFKBDEMvfsVObrI_sAchIUFEVaQ1XvItnEodjpjk2FXxH830xVbYXIqL8l7ea8uksg-UJ9puAErtwCwm6YYHGkYE3wVfKm7kIKiP91uKjRPcSSPmWUeuG2QvOPHzLJw_OLfjcKelE4k3NK7zKSMwiJ16UrmPfrRmUTSFu9ZcbBx6llWRB5Tfz2gVZny6GwF30L8WyoNvmgmp6j2WCE77h5eKZtiS1bMh-T50jKZ7_yJMQ7_aNpQt9v7GkEHz5wliAqIWgKr09VLBy-cvEAxsDpbT-3gyOUXBA6HJ6AkZ5P6Ac5Okew=)``

---

# 5. UML Diagrams (Continued)

### Activity Diagram
``![UML Diagram](https://kroki.io/mermaid/png/eJxdkbFOwzAQhnee4mZQhMTYgYGYTEUKTWGpOpjkV2KR2NH5EiVvj7lQVNXb-f--850cxQqMsy3bIZuf7iid0_2ZsuyZPsY-2KZwPaLeX9Wavy7CtpYjFtlRuZameCxX6YLPTKgXVa4QVfJu8t_Ot4lnjPANnaowcQ3StmeVLtD2yPCFplElD8M4CegTtQTeZvqPFa7sDPOyoyrlIOepQowueCpC34DV2JhtwQh-n8Drtt6l0uwAYYcZefCiC1ZucL1lJ2vqarnuVLrBVN3v3373S9MKPdDRcguhP0ClBChoXBx7ux4Qx-AjNLu5Uy59yA_HvIgQ)``

---

# 6. UML Diagrams (Actors & Workflows)

### Use Case Diagram & Sequence Diagram

``![UML Diagram](https://kroki.io/mermaid/png/eJxl0E1PwzAMBuA7v8LiwAUm7j1MYpSqkzYxuo-7m1pd1LQpcYJWIf47TsYmpOVQpcqT13aYPgMNinKNrcP-DmSh8tZBWaWfEZ3XSo84eNgvARkKZwdPQwM58rG26Job-LI5S4PcwQJVJ_wGHfJFRAdK5XL0WCPTDVut1pGVoW310BaoKMYnlj5lNZvP98sMtmQkCu4LLb0tiD2s0avjfVL7pSi5l8HmfbuD59jYN3faGH4COo3kdHyGn4TFiZb-MvgI5CagvqamkfIM9QSse23QaT8lLW52Cd_ZEfpYVSyoYxg6_pcoo8Q2pb3X-IQnD4-wcbYffUJyfA16-0IT0JNQHBrdyPY8zjXub-rCOikYYUUcjOfLuHJeVhnkmkeD0_kyPMDWBqeIfwH8S5wQ)``

---

# 7. Database Design
The platform uses **SQLite** for robust local persistence, preventing data loss across sessions.

**Tables:**
1. `sessions`: 
   - `id` (UUID), `hr_username`, `session_name`, `created_at`
2. `documents`: 
   - `id`, `session_id` (FK), `filename`, `file_path`
3. `messages`:
   - `id`, `session_id` (FK), `role` (user/assistant), `content`, `timestamp`

---

# 8. Frontend Development
The user interface operates as a responsive Single Page Application (SPA).
- **HTML5 & Vanilla CSS Variables:** Driven by modern design concepts like glassmorphism and dynamic gradients to mimic premium corporate tools (e.g., ChatGPT/OpenAI styling).
- **Vanilla Javascript:** Handles drag-and-drop mechanics, asynchronous API fetch calls, and dynamic mode swapping (Single vs. Multi-Resume workflows) without page reloads.
- **Marked.js:** Compiles raw Markdown output from the AI into beautifully formatted HTML headers, bold text, and bulleted lists.

---

# 9. Backend Development
The foundation of the architecture lies in a lightweight, robust Python server.
- **Flask:** Routes all web traffic, secures sessions, and serves API endpoints (`/upload`, `/ask`, `/history`).
- **Python Document Parsers:** Utilizes `PyPDF2` and `python-docx` to safely ingest varying document formats into raw UTF-8 text strings.
- **File System Handling:** Generates unique session folders (`data/sessions/<id>`) to permanently isolate candidate data pools from one another.

---

# 10. Working Process of RAG
**Retrieval-Augmented Generation** fundamentally solves AI hallucination by limiting the LLM to only answer based on documents we provide.

1. **Indexing:** A candidate's uploaded resume is shredded into 500-word "chunks." Each chunk is tagged (e.g., `[Source: Smith_CV.pdf]`) and mapped into a multidimensional vector space.
2. **Retrieval:** When HR asks: *"Who has Python skills?"*, the system checks the vector space for mathematical proximity to "Python skills" and retrieves those exact chunks.
3. **Generation:** The retrieved chunks are forcefully injected into the LLM's prompt. The AI evaluates the provided text and formulates a direct answer, citing the candidate's exact filename.

---

# 11. Integration and Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript (Fetch API, Marked.js)
- **Backend Frameowrk:** Python, Flask, Jinja2
- **Database:** SQLite (Relational structure for chat/session storage)
- **NLP / Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`)
- **LLM Pipeline:** Hugging Face REST Router API (`Qwen/Qwen2.5-72B-Instruct`)
- **Document Processing:** `PyPDF2`, `python-docx`, `langchain` (Text Splitters)

---

# 12. Advantages of Our Website

1. **Drastic Time Reduction:** Automatically parses dozens of resumes instantly instead of manual reading.
2. **Skill-Based Objectivity:** Removes human bias by cross-comparing candidate raw data explicitly against matching skills.
3. **Data Privacy First:** Candidate embeddings are isolated strictly by HR Session ID on internal storage.
4. **Resumable Workflows:** True operational persistence. If a recruiter closes the tab, their entire batch analysis and chat history is saved securely in the SQLite DB and restored upon next login.
5. **Modern Elegance:** Boasts an extremely fast, responsive, and beautiful UI comparable to enterprise AI leaders.

---

# 13. UI - Main Dashboard
*(Displays the highly modern dual-mode RAG Interface with Session Tracking)*

![](/c:/Users/akash/.gemini/antigravity/brain/8785f474-d18a-4c2e-b3af-44e056456138/resume_ai_dashboard_1774971052143.png)

---

# 14. UI - RAG Action & Chat
*(Displays the interactive chat sequence and precise candidate retrieval mechanics)*

![](/c:/Users/akash/.gemini/antigravity/brain/8785f474-d18a-4c2e-b3af-44e056456138/rag_qa_final_working_1774959788127.webp)

---

# 15. UI - Candidate Matcher Filter Panel
*(Displays the customized query builder for the Candidate Skill Matcher workflow)*

![](/c:/Users/akash/.gemini/antigravity/brain/8785f474-d18a-4c2e-b3af-44e056456138/rag_app_qa_fixed_1774958912851.webp)
