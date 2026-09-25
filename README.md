# From User Preferences to an Adaptive Coding Environment

CS 412 Second Laboratory project based on the supplied `Form Responses.xlsx` survey. The project turns actual respondent differences into two explicit user models and a small adaptive Tkinter coding environment.

## Requirements

- Python 3.10 or newer
- Tkinter, normally included with the standard Windows Python installation
- Python standard library only; no network or AI service is required

## Run

From this folder:

```text
python generate_report.py
python main.py
```

`generate_report.py` reads all 20 populated workbook responses, writes `data/analysis.json`, regenerates the SVG charts, and creates both `report/laboratory_report.md` and `report/laboratory_report.docx`.

The editor includes a one-click Coding Guide and a collapsible offline message panel. Ask questions such as `What should I fix next?`, `Explain this function`, or `How can I make this safer?`. Press `Ctrl+Enter` in the message box to generate deterministic guidance from the current syntax tree.

The app opens with a local login screen. Choose Beginner for Guided Builder or Advanced for Independent Builder, then use `Log out` to return to the profile screen. The workspace includes VS Code Dark, VS Code Light, and Monokai themes.

The Coding Guide is intentionally offline and deterministic. It does not generate arbitrary code or write files; it only analyzes the current in-memory editor and suggests safe next steps.

## Project structure

- `main.py`: runnable adaptive coding environment
- `user_model.py`: respondent-derived profile structures
- `adaptation.py`: explicit adaptation rules
- `data_analysis.py`: standard-library XLSX parser, calculations, and chart generation
- `generate_report.py`: report and DOCX generation
- `data/survey_data.xlsx`: supplied survey workbook copy
- `data/analysis.json`: reproducible calculated findings
- `charts/`: generated SVG charts
- `report/`: five-section laboratory report in Markdown and DOCX

## Demonstration profiles

The Guided Builder uses actual respondent row 19: Beginner, Rarely, 6 months - 1 year, high assistance, AI reliance 5/5, and Not comfortable without AI. It receives detailed hints, enabled formatting, wrapped editing, and prominent offline guidance.

The Independent Builder uses actual respondent row 15: Advanced, A few times a week, 3+ years, minimal assistance, AI reliance 2/5, and Somewhat comfortable without AI. It receives compact editing, reduced prompts, disabled automatic formatting, and optional offline guidance. Check Code and Debug remain available in both profiles.

## Safety boundary

Run Code is a controlled demonstration runner. It blocks imports, context managers, and lambdas and exposes only a small set of built-ins. It is not a security sandbox and should not be treated as one for untrusted code.

## Data integrity

The analysis code fails if the workbook does not contain exactly 20 populated responses. Percentages, averages, cross-tabs, profiles, and chart values are generated from the workbook rather than typed into the report.
