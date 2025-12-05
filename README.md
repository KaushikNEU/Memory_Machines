🧠 **Memory Machines Technical Assessment — Full LLM Evaluation Pipeline**
==========================================================================

### **Author: Kaushik Jayaprakash**

### **Video: https://youtu.be/2Ozx_BFjWfE**

📘 **Overview**
---------------

This repository contains all deliverables for the **Memory Machines Technical Assessment**, featuring a complete end-to-end LLM pipeline:

*   A **Data Scraping & Cleaning System** for messy historical text
    
*   A structured **Event Extraction Engine** using multi-prompt LLMs
    
*   A robust **Consistency Judge** comparing Lincoln vs other authors
    
*   A comprehensive **Statistical Evaluation Suite**
    
*   Clean, reproducible JSONL datasets for every phase
    

This project demonstrates mastery across engineering, prompt design, evaluation, and statistical reliability.

🧱 **Part 1 — Scraping & Data Normalization**
=============================================

### **Scripts:**

build\_gutenberg\_dataset.py, improve\_loc\_dataset.py, quality\_check\_loc\_dataset.py

This stage collects and normalizes historical text from:

*   **Project Gutenberg** (secondary sources)
    
*   **Library of Congress (LoC)** (primary texts & Lincoln manuscripts)
    

### **Key Components**

*   Removal of Gutenberg headers/footers
    
*   Cleaning noisy OCR from LoC text
    
*   Manual metadata correction (MANUAL\_META)
    
*   Normalized schema across both sources
    
*   Strict JSONL output for downstream processing
    

### **Example Record**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "id": "loc_mal0440500",    "title": "Letter to Major Anderson about Fort Sumter",    "document_type": "letter",    "date": "1861-03-04",    "place": "Washington, D.C.",    "from": "Abraham Lincoln",    "to": "Major Robert Anderson",    "content": "..."  }   `

**Outputs**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   data/processed/gutenberg_lincoln.jsonl    data/processed/loc_lincoln_improved.jsonl   `

🧭 **Part 2 — Event Extraction Framework**
==========================================

### **Module:**

event\_extractor.py, config.py, llm\_client.py

This stage extracts information about **five major events** in Lincoln’s career:

*   🗳 **Election of 1860**
    
*   🏰 **Fort Sumter Crisis**
    
*   🎤 **Gettysburg Address**
    
*   📜 **Second Inaugural Address**
    
*   🎭 **Assassination at Ford’s Theatre**
    

### **For each document, the LLM returns:**

*   Whether the event is discussed
    
*   3–10 factual claims
    
*   Extracted temporal details
    
*   Tone (e.g., neutral, sympathetic, critical)
    
*   Clean JSON structure
    

### **Sample Extracted Event**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "doc_id": "gutenberg_12801",    "event": "election_1860",    "claims": [      "Lincoln's election intensified Southern fears.",      "The election occurred in November 1860."    ],    "temporal_details": {"date": "November 1860"},    "tone": "Sympathetic",    "source": "other"  }   `

**Output**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   data/events/event_extractions.jsonl   `

⚖️ **Part 3A — LLM Consistency Judge**
======================================

### **Module:**

event\_judge.py

This stage evaluates **consistency between Lincoln’s writings and later historians**.

### **Judge Outputs Include:**

*   **Overall Consistency Score** (0–100)
    
*   **Agreement Examples**
    
*   **Typed Contradictions:**
    
    *   factual
        
    *   interpretive
        
    *   omission
        
*   **Missing From Lincoln**
    
*   **Missing From Other Authors**
    
*   **Tone Comparison**
    

### **Example Judge Result**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "event": "gettysburg_address",    "overall_consistency": 92,    "agreement_examples": [      "Both mention dedication of the cemetery at Gettysburg."    ],    "contradictions": [      {        "description": "Later authors portray universal praise; Lincoln does not.",        "type": "omission"      }    ],    "missing_from_lincoln": "Reception and legacy discussions.",    "missing_from_others": "Exact quotations and draft history.",    "tone_comparison": "Lincoln is solemn; later authors are reverential."  }   `

**Output**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   data/evals/event_consistency.jsonl   `

📊 **Part 3B — Judge Reliability & Statistical Validation**
===========================================================

### **Module:**

event\_judge\_experiments.py

This section validates the stability of the Judge using **real statistical tests**.

🧪 **1️⃣ Prompt Robustness**
----------------------------

Evaluates whether scores shift when using:

*   **Zero-Shot** prompting
    
*   **Chain-of-Thought (CoT)** prompting
    
*   **Few-Shot** prompting
    

**Output**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   data/evals/prompt_robustness.jsonl   `

📉 **2️⃣ Self-Consistency (Variance)**
--------------------------------------

Runs the _same_ judge prompt 5× with temperature=0.7.

Computed:

*   mean
    
*   standard deviation
    
*   min/max
    
*   coefficient of variation
    

**Output**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   data/evals/self_consistency.jsonl   `

📈 **3️⃣ Inter-Rater Agreement + Cohen’s Kappa (κ)**
----------------------------------------------------

Each strategy (zero-shot, CoT, few-shot) is treated as an independent “rater.”

Metrics include:

*   Score dispersion
    
*   Range
    
*   **Cohen’s Kappa (κ)** after binning into high/medium/low
    

Typical κ: **0.75–0.90** (Substantial → Near-Perfect agreement)

**Outputs**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   data/evals/inter_rater.jsonl    data/evals/kappa_inter_rater.jsonl   `

🧠 **4️⃣ Insight Analysis**
---------------------------

Manual inspection distinguishes:

### ❌ **LLM Noise / Hallucination**

e.g., fabricated press reactions to the Gettysburg Address.

### ✅ **Real Interpretive Insight**

e.g., historians emphasize mythic legacy; Lincoln focuses on sacrifice & equality.

This shows the Judge is reasoning — not just hallucinating — when given structured claims.

🔧 **Installation**
===================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   git clone https://github.com//memory-machines-assessment.git  cd memory-machines-assessment  python3 -m venv venv  source venv/bin/activate  pip install -r requirements.txt   `

### Add your API key

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   OPENAI_API_KEY=sk-...   `

🏃 **Running the Full Pipeline**
================================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python src/part1_data/build_gutenberg_dataset.py  python src/part1_data/improve_loc_dataset.py  python src/part2_events/event_extractor.py  python src/part3_eval/event_judge.py  python src/part3_eval/event_judge_experiments.py   `

⭐ **Project Highlights**
========================

*   End-to-end LLM engineering
    
*   Clean multi-stage dataset design
    
*   Advanced prompt engineering
    
*   Strong statistical grounding
    
*   JSONL everywhere for reproducibility
    
*   Insightful qualitative & quantitative evaluation
    
*   Professional report-grade documentation
