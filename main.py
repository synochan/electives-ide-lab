"""Adaptive Coding Environment with an offline coding guide."""

from __future__ import annotations

import ast
import builtins
import io
import re
import textwrap
import tkinter as tk
from contextlib import redirect_stdout
from tkinter import ttk

from adaptation import adapt
from user_model import USER_MODELS, UserModel

STARTER_CODE = '''def greet(name):
    message = f"Hello, {name}!"
    print(message)


greet("CS 412")
'''

THEMES = {
    "VS Code Dark": {"app": "#1e1e1e", "surface": "#252526", "header": "#181818", "editor": "#1e1e1e", "gutter": "#252526", "text": "#d4d4d4", "muted": "#858585", "input": "#3c3c3c", "feedback": "#252526", "accent": "#007acc", "accent_dark": "#005a9e", "line": "#3c3c3c", "button": "#333333"},
    "VS Code Light": {"app": "#f3f3f3", "surface": "#ffffff", "header": "#e7e7e7", "editor": "#ffffff", "gutter": "#f3f3f3", "text": "#1f2937", "muted": "#6b7280", "input": "#f5f5f5", "feedback": "#f5f7f9", "accent": "#0b6bb3", "accent_dark": "#084f86", "line": "#d6dbe1", "button": "#e8edf2"},
    "Monokai": {"app": "#272822", "surface": "#2f3129", "header": "#1f201b", "editor": "#272822", "gutter": "#2f3129", "text": "#f8f8f2", "muted": "#a6a88d", "input": "#3e4038", "feedback": "#30322b", "accent": "#a6e22e", "accent_dark": "#7aa817", "line": "#494b40", "button": "#414339"},
}


class AdaptiveCodingEnvironment(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Adaptive Coding Environment | CS 412")
        self.geometry("1280x820")
        self.minsize(980, 680)
        self.configure(bg="#e8eef2")
        self.profile_key = tk.StringVar(value="guided_builder")
        self.theme_key = tk.StringVar(value="VS Code Dark")
        self.status_text = tk.StringVar(value="Ready")
        self.connection_text = tk.StringVar(value="Offline workspace | no network")
        self.profile_display = {key: f"{model.name}  /  {model.experience}" for key, model in USER_MODELS.items()}
        self.style = None
        self._build_styles()
        self._build_login()
        self.app_shell = ttk.Frame(self, style="App.TFrame")
        self._build_ui()
        self._load_profile()
        self._show_login()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        self.style = style
        style.theme_use("clam")
        style.configure("App.TFrame", background="#1e1e1e")
        style.configure("Surface.TFrame", background="#252526")
        style.configure("Dark.TFrame", background="#181818")
        style.configure("Title.TLabel", background="#181818", foreground="#ffffff", font=("Segoe UI", 21, "bold"))
        style.configure("Subtitle.TLabel", background="#181818", foreground="#858585", font=("Segoe UI", 9))
        style.configure("Section.TLabel", background="#252526", foreground="#d4d4d4", font=("Segoe UI", 11, "bold"))
        style.configure("Body.TLabel", background="#252526", foreground="#d4d4d4", font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background="#252526", foreground="#858585", font=("Segoe UI", 8))
        style.configure("Pill.TLabel", background="#264f78", foreground="#ffffff", font=("Segoe UI", 8, "bold"), padding=(8, 4))
        style.configure("Primary.TButton", background="#007acc", foreground="#ffffff", padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.configure("Tool.TButton", background="#333333", foreground="#d4d4d4", padding=(10, 7), font=("Segoe UI", 9))
        style.configure("AI.TButton", background="#0e8a7d", foreground="#ffffff", padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.configure("LoginTitle.TLabel", background="#252526", foreground="#ffffff", font=("Segoe UI", 25, "bold"))
        style.configure("LoginBody.TLabel", background="#252526", foreground="#c8c8c8", font=("Segoe UI", 10))
        self.apply_theme()

    def _build_login(self) -> None:
        self.login_frame = ttk.Frame(self, style="App.TFrame", padding=40)
        card = ttk.Frame(self.login_frame, style="Surface.TFrame", padding=32)
        card.place(relx=0.5, rely=0.5, anchor="center", width=560, height=440)
        ttk.Label(card, text="Adaptive Coding Environment", style="LoginTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text="CS 412 laboratory workspace", style="LoginBody.TLabel").pack(anchor="w", pady=(4, 28))
        ttk.Label(card, text="Sign in as a survey-derived user model", style="LoginBody.TLabel").pack(anchor="w")
        ttk.Label(card, text="Your profile controls how much guidance, formatting, and AI assistance the workspace shows.", style="LoginBody.TLabel", wraplength=480).pack(anchor="w", pady=(6, 22))
        profile_buttons = ttk.Frame(card, style="Surface.TFrame")
        profile_buttons.pack(fill="x")
        ttk.Button(profile_buttons, text="Beginner  /  Guided Builder", command=lambda: self.login_as("guided_builder"), style="Primary.TButton").pack(fill="x", pady=5)
        ttk.Button(profile_buttons, text="Advanced  /  Independent Builder", command=lambda: self.login_as("independent_builder"), style="Tool.TButton").pack(fill="x", pady=5)
        theme_row = ttk.Frame(card, style="Surface.TFrame")
        theme_row.pack(fill="x", pady=(28, 0))
        ttk.Label(theme_row, text="Theme", style="LoginBody.TLabel").pack(side="left")
        self.login_theme_combo = ttk.Combobox(theme_row, textvariable=self.theme_key, state="readonly", values=list(THEMES), width=22)
        self.login_theme_combo.pack(side="right")
        self.login_theme_combo.bind("<<ComboboxSelected>>", lambda _event: self.apply_theme())
        ttk.Label(card, text="This workspace is fully offline and does not connect to an AI service.", style="Muted.TLabel", wraplength=480).pack(anchor="w", pady=(30, 0))

    def _show_login(self) -> None:
        self.app_shell.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def login_as(self, profile_key: str) -> None:
        self.profile_key.set(profile_key)
        self.login_frame.pack_forget()
        self.app_shell.pack(fill="both", expand=True)
        self._load_profile()
        self.status_text.set(f"Signed in as {USER_MODELS[profile_key].name}")

    def logout(self) -> None:
        self.app_shell.pack_forget()
        self._show_login()

    def change_theme(self, _event=None) -> None:
        self.apply_theme()

    def apply_theme(self) -> None:
        if self.style is None:
            return
        colors = THEMES[self.theme_key.get()]
        self.configure(bg=colors["app"])
        self.style.configure("App.TFrame", background=colors["app"])
        self.style.configure("Surface.TFrame", background=colors["surface"])
        self.style.configure("Dark.TFrame", background=colors["header"])
        self.style.configure("Title.TLabel", background=colors["header"], foreground=colors["text"])
        self.style.configure("Subtitle.TLabel", background=colors["header"], foreground=colors["muted"])
        self.style.configure("Section.TLabel", background=colors["surface"], foreground=colors["text"])
        self.style.configure("Body.TLabel", background=colors["surface"], foreground=colors["text"])
        self.style.configure("Muted.TLabel", background=colors["surface"], foreground=colors["muted"])
        self.style.configure("Pill.TLabel", background=colors["accent_dark"], foreground="#ffffff")
        self.style.configure("LoginTitle.TLabel", background=colors["surface"], foreground=colors["text"])
        self.style.configure("LoginBody.TLabel", background=colors["surface"], foreground=colors["text"])
        self.style.configure("Tool.TButton", background=colors["button"], foreground=colors["text"])
        self.style.configure("Primary.TButton", background=colors["accent"], foreground="#ffffff")
        self.style.configure("AI.TButton", background=colors["accent_dark"], foreground="#ffffff")
        if hasattr(self, "status_bar"):
            self.status_bar.configure(background=colors["header"], foreground=colors["muted"])
        for widget_name, options in {
            "model_text": {"bg": colors["input"], "fg": colors["text"]},
            "editor": {"bg": colors["editor"], "fg": colors["text"], "insertbackground": colors["text"], "selectbackground": colors["accent"]},
            "line_numbers": {"bg": colors["gutter"], "fg": colors["muted"]},
            "feedback": {"bg": colors["feedback"], "fg": colors["text"]},
            "chat_log": {"bg": colors["feedback"], "fg": colors["text"]},
            "chat_input": {"bg": colors["input"], "fg": colors["text"], "insertbackground": colors["text"]},
        }.items():
            if hasattr(self, widget_name):
                getattr(self, widget_name).configure(**options)

    def _build_ui(self) -> None:
        header = ttk.Frame(self.app_shell, style="Dark.TFrame", padding=(24, 18, 24, 17))
        header.pack(fill="x")
        title_row = ttk.Frame(header, style="Dark.TFrame")
        title_row.pack(fill="x")
        ttk.Label(title_row, text="Adaptive Coding Environment", style="Title.TLabel").pack(side="left")
        ttk.Button(title_row, text="Log out", command=self.logout, style="Tool.TButton").pack(side="right", padx=(8, 0))
        ttk.Label(title_row, textvariable=self.connection_text, style="Pill.TLabel").pack(side="right", pady=5)
        self.theme_combo = ttk.Combobox(title_row, textvariable=self.theme_key, state="readonly", values=list(THEMES), width=17)
        self.theme_combo.pack(side="right", padx=(8, 8))
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        ttk.Label(header, text="CS 412 Second Laboratory  |  user-modelled coding assistance", style="Subtitle.TLabel").pack(anchor="w", pady=(5, 0))

        body = ttk.Frame(self.app_shell, style="App.TFrame", padding=16)
        body.pack(fill="both", expand=True)
        sidebar = ttk.Frame(body, style="Surface.TFrame", padding=17, width=290)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)
        user_row = ttk.Frame(sidebar, style="Surface.TFrame")
        user_row.pack(fill="x")
        ttk.Label(user_row, text="CURRENT USER MODEL", style="Muted.TLabel").pack(side="left")
        ttk.Label(user_row, text="SIGNED IN", style="Pill.TLabel").pack(side="right")
        self.profile_combo = ttk.Combobox(sidebar, state="readonly", values=list(self.profile_display.values()))
        self.profile_combo.pack(fill="x", pady=(8, 18))
        self.profile_combo.bind("<<ComboboxSelected>>", self._profile_changed)
        self.profile_name = ttk.Label(sidebar, style="Section.TLabel", wraplength=250)
        self.profile_name.pack(anchor="w")
        self.profile_description = ttk.Label(sidebar, style="Body.TLabel", wraplength=250)
        self.profile_description.pack(anchor="w", pady=(6, 15))
        ttk.Label(sidebar, text="MODEL ATTRIBUTES", style="Muted.TLabel").pack(anchor="w")
        self.model_text = tk.Text(sidebar, height=13, relief="flat", bg="#f3f7f9", fg="#34495e", font=("Consolas", 9), padx=10, pady=10, wrap="word", highlightthickness=0)
        self.model_text.pack(fill="x", pady=(7, 0))
        self.model_text.configure(state="disabled")
        self.adaptation_label = ttk.Label(sidebar, style="Body.TLabel", wraplength=250)
        self.adaptation_label.pack(anchor="w", pady=(15, 0))
        ttk.Label(sidebar, text="Offline guide only. No network calls or project-file writes are used.", style="Muted.TLabel", wraplength=250).pack(anchor="w", side="bottom")

        workspace = ttk.Frame(body, style="Surface.TFrame", padding=17)
        workspace.pack(side="left", fill="both", expand=True)
        editor_heading = ttk.Frame(workspace, style="Surface.TFrame")
        editor_heading.pack(fill="x")
        ttk.Label(editor_heading, text="Code editor", style="Section.TLabel").pack(side="left")
        ttk.Label(editor_heading, text="Python  |  line numbers enabled", style="Muted.TLabel").pack(side="right", pady=2)

        editor_shell = ttk.Frame(workspace, style="Surface.TFrame")
        editor_shell.pack(fill="both", expand=True, pady=(9, 12))
        self.line_numbers = tk.Text(editor_shell, width=4, padx=8, pady=12, takefocus=0, borderwidth=0, highlightthickness=0, state="disabled", bg="#172d40", fg="#6f8b9c", font=("Consolas", 11), wrap="none")
        self.line_numbers.pack(side="left", fill="y")
        self.editor = tk.Text(editor_shell, undo=True, wrap="none", borderwidth=0, highlightthickness=0, bg="#102331", fg="#e7f1f4", insertbackground="#ffffff", selectbackground="#247f78", font=("Consolas", 11), padx=12, pady=12)
        self.editor.pack(side="left", fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(editor_shell, orient="vertical", command=self._scroll_editor)
        self.scrollbar.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=self._editor_scrolled)
        self.editor.insert("1.0", STARTER_CODE)
        self.editor.bind("<KeyRelease>", self._editor_changed)
        self.editor.bind("<MouseWheel>", self._editor_changed)
        self.editor.bind("<Button-4>", self._editor_changed)
        self.editor.bind("<Button-5>", self._editor_changed)
        self._update_line_numbers()

        tools = ttk.Frame(workspace, style="Surface.TFrame")
        tools.pack(fill="x")
        self.run_button = ttk.Button(tools, text="Run Code", command=self.run_code, style="Primary.TButton")
        self.run_button.pack(side="left", padx=(0, 6))
        ttk.Button(tools, text="Check Code", command=self.check_code, style="Tool.TButton").pack(side="left", padx=6)
        self.format_button = ttk.Button(tools, text="Format Code", command=self.format_code, style="Tool.TButton")
        self.format_button.pack(side="left", padx=6)
        ttk.Button(tools, text="Debug", command=self.debug_code, style="Tool.TButton").pack(side="left", padx=6)
        self.ai_button = ttk.Button(tools, text="Coding Guide", command=self.ai_help, style="AI.TButton")
        self.ai_button.pack(side="right")

        feedback_frame = ttk.Frame(workspace, style="Surface.TFrame")
        feedback_frame.pack(fill="both", expand=True, pady=(15, 0))
        feedback_heading = ttk.Frame(feedback_frame, style="Surface.TFrame")
        feedback_heading.pack(fill="x")
        ttk.Label(feedback_heading, text="Feedback and local AI assistance", style="Section.TLabel").pack(side="left")
        ttk.Label(feedback_heading, text="Analysis stays on this machine", style="Muted.TLabel").pack(side="right")
        self.feedback = tk.Text(feedback_frame, height=8, relief="flat", bg="#f3f7f9", fg="#34495e", font=("Segoe UI", 9), padx=12, pady=10, wrap="word", highlightthickness=0)
        self.feedback.pack(fill="both", expand=True, pady=(8, 0))
        self.feedback.configure(state="disabled")
        self.assistant_panel = ttk.Frame(workspace, style="Surface.TFrame")
        self.assistant_panel.pack(fill="x", pady=(14, 0))
        assistant_heading = ttk.Frame(self.assistant_panel, style="Surface.TFrame")
        assistant_heading.pack(fill="x")
        ttk.Label(assistant_heading, text="Coding Guide", style="Section.TLabel").pack(side="left")
        ttk.Label(assistant_heading, text="Ask about the current code", style="Muted.TLabel").pack(side="left", padx=(10, 0))
        self.chat_toggle = ttk.Button(assistant_heading, text="Hide", command=self.toggle_chat, style="Tool.TButton")
        self.chat_toggle.pack(side="right")
        self.chat_body = ttk.Frame(self.assistant_panel, style="Surface.TFrame")
        self.chat_body.pack(fill="x", pady=(7, 0))
        self.chat_log = tk.Text(self.chat_body, height=5, relief="flat", bg="#eef6f7", fg="#34495e", font=("Segoe UI", 9), padx=10, pady=8, wrap="word", highlightthickness=0)
        self.chat_log.pack(fill="x")
        self.chat_log.configure(state="disabled")
        chat_controls = ttk.Frame(self.chat_body, style="Surface.TFrame")
        chat_controls.pack(fill="x", pady=(7, 0))
        self.chat_input = tk.Text(chat_controls, height=2, relief="flat", bg="#f3f7f9", fg="#34495e", insertbackground="#17324d", font=("Segoe UI", 9), padx=10, pady=8, wrap="word", highlightthickness=0)
        self.chat_input.pack(side="left", fill="x", expand=True)
        self.chat_input.insert("1.0", "What should I fix or improve next?")
        self.chat_input.bind("<Control-Return>", lambda _event: self.ask_chat())
        self.chat_send_button = ttk.Button(chat_controls, text="Guide", command=self.ask_chat, style="AI.TButton")
        self.chat_send_button.pack(side="left", padx=(8, 0), fill="y")
        self.status_bar = ttk.Label(self.app_shell, textvariable=self.status_text, background="#d8e3e8", foreground="#34495e", padding=(16, 7), anchor="w")
        self.status_bar.pack(fill="x", side="bottom")
        self.apply_theme()

    def _profile_changed(self, _event=None) -> None:
        selected = self.profile_combo.get()
        self.profile_key.set(next(key for key, value in self.profile_display.items() if value == selected))
        self._load_profile()

    def _current(self) -> UserModel:
        return USER_MODELS[self.profile_key.get()]

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _write_feedback(self, value: str) -> None:
        self._set_text(self.feedback, value)

    def _append_chat(self, value: str) -> None:
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", value + "\n\n")
        self.chat_log.see("end")
        self.chat_log.configure(state="disabled")

    def toggle_chat(self) -> None:
        if self.chat_body.winfo_ismapped():
            self.chat_body.pack_forget()
            self.chat_toggle.configure(text="Show")
        else:
            self.chat_body.pack(fill="x", pady=(7, 0))
            self.chat_toggle.configure(text="Hide")

    def ask_chat(self) -> None:
        question = self.chat_input.get("1.0", "end-1c").strip()
        if not question:
            return
        self._append_chat(f"You: {question}")
        self.chat_input.delete("1.0", "end")
        answer = self._local_guidance(question)
        self._append_chat("Guide: " + answer)
        self.status_text.set("Offline coding guidance generated")

    def _update_line_numbers(self) -> None:
        line_count = int(self.editor.index("end-1c").split(".")[0])
        numbers = "\n".join(str(index) for index in range(1, line_count + 1))
        self._set_text(self.line_numbers, numbers)
        self.line_numbers.yview_moveto(self.editor.yview()[0])

    def _editor_changed(self, _event=None) -> None:
        self._update_line_numbers()
        return None

    def _scroll_editor(self, *args) -> None:
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def _editor_scrolled(self, first, last) -> None:
        self.scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def _load_profile(self) -> None:
        model = self._current()
        rules = adapt(model)
        self.profile_combo.set(self.profile_display[model.key])
        self.profile_name.configure(text=f"{model.name}  |  ACTIVE")
        self.profile_description.configure(text=model.description)
        summary = f"Experience: {model.experience}\nCoding: {model.coding_frequency}\nDuration: {model.programming_duration}\nAssistance: {model.assistance_preference}\nAI reliance: {model.ai_reliance:.0f}/5\nComfort without AI: {model.comfort_without_ai}\nFeature priority: {model.feature_priority}"
        self._set_text(self.model_text, summary)
        self.adaptation_label.configure(text=rules.assistance_text)
        self.format_button.state(["!disabled"] if rules.formatting_enabled else ["disabled"])
        self.ai_button.configure(text="Coding Guide  |  guided" if rules.ai_prominence == "primary" else "Coding Guide  |  optional")
        self.editor.configure(wrap="word" if rules.hints_visible else "none")
        self._write_feedback(rules.assistance_text + "\n\nUse Coding Guide for offline feedback about the current code.")
        self.status_text.set(f"Active profile: {model.name} | Adaptation updated")

    def _parse(self):
        try:
            return ast.parse(self.editor.get("1.0", "end-1c")), None
        except SyntaxError as error:
            return None, error

    def check_code(self) -> None:
        tree, error = self._parse()
        if error:
            message = f"Syntax error on line {error.lineno}: {error.msg}."
            if adapt(self._current()).detailed_feedback:
                message += " Guided tip: check indentation, brackets, and the line highlighted by the editor."
            self._write_feedback(message)
            self.status_text.set("Check complete: syntax needs attention")
            return
        names = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)})
        self._write_feedback("No syntax errors found.\n\nNames used: " + (", ".join(names) if names else "none") + ".")
        self.status_text.set("Check complete: no syntax errors")

    def run_code(self) -> None:
        tree, error = self._parse()
        if error:
            self.check_code()
            return
        if any(isinstance(node, (ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith, ast.Lambda)) for node in ast.walk(tree)):
            self._write_feedback("Run blocked: imports, context managers, and lambdas are disabled in this controlled laboratory runner.")
            return
        output = io.StringIO()
        safe_builtins = {name: getattr(builtins, name) for name in ("print", "len", "range", "str", "int", "float", "sum")}
        try:
            with redirect_stdout(output):
                exec(compile(tree, "<editor>", "exec"), {"__builtins__": safe_builtins}, {})
            self._write_feedback("Controlled run result:\n" + (output.getvalue().strip() or "Code completed without printed output."))
            self.status_text.set("Run complete")
        except Exception as error:
            self._write_feedback(f"Runtime feedback: {type(error).__name__}: {error}")
            self.status_text.set("Run stopped with handled runtime feedback")

    def format_code(self) -> None:
        formatted = textwrap.dedent(self.editor.get("1.0", "end-1c")).replace("\t", "    ").rstrip() + "\n"
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", formatted)
        self._update_line_numbers()
        self._write_feedback("Formatting applied for the active high-assistance profile.")

    def debug_code(self) -> None:
        tree, error = self._parse()
        if error:
            self.check_code()
            return
        functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assignments = [node.targets[0].id for node in ast.walk(tree) if isinstance(node, ast.Assign) and node.targets and isinstance(node.targets[0], ast.Name)]
        message = f"Debug scan:\nFunctions: {', '.join(functions) if functions else 'none'}\nAssigned names: {', '.join(assignments) if assignments else 'none'}\nNo structural issue detected by the prototype scan."
        if adapt(self._current()).detailed_feedback:
            message += "\nGuided tip: test one function at a time and print intermediate values."
        self._write_feedback(message)

    def ai_help(self) -> None:
        self._write_feedback(self._local_guidance("Review my current code and tell me what to improve next."))
        self.status_text.set("Offline coding guidance generated")

    def _local_guidance(self, question: str) -> str:
        """Provide predictable, offline guidance from the editor's AST and active profile."""
        tree, error = self._parse()
        model = self._current()
        if error:
            return f"Line {error.lineno} has a syntax error: {error.msg}. Check indentation, brackets, and the nearby statement."
        functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assignments = [node.targets[0].id for node in ast.walk(tree) if isinstance(node, ast.Assign) and node.targets and isinstance(node.targets[0], ast.Name)]
        lower = question.lower()
        if "explain" in lower:
            subject = ", ".join(functions) if functions else "the top-level statements"
            return f"This program contains {subject}. It assigns {', '.join(assignments) if assignments else 'no named variables yet'}. Read the code from top to bottom and trace each value before it is used."
        if "debug" in lower or "error" in lower or "fix" in lower:
            return f"The syntax tree is valid. Focus your next check on the functions {', '.join(functions) if functions else 'in the top-level code'}. Run Check Code, then test one small input at a time."
        if "write" in lower or "implement" in lower or "create" in lower:
            return "This offline guide does not generate arbitrary code. Write the smallest version in the editor, then use Check Code and Debug to refine it safely."
        return f"For the {model.name} profile, start with one small change, run Check Code, and then use Debug. The current editor has {len(functions)} function(s) and {len(assignments)} assignment(s)."


if __name__ == "__main__":
    AdaptiveCodingEnvironment().mainloop()
