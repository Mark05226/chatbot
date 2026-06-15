import os
import sys
import multiprocessing
import json
import threading
import customtkinter as ctk
from llama_cpp import Llama

# Set the overall theme
ctk.set_appearance_mode("System")  # Follows Windows Dark/Light mode
ctk.set_default_color_theme("blue")

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =====================================================================
# MEMORY SYSTEM
# =====================================================================
MEMORY_FILE = get_resource_path("bob_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(history):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Failed to save memory: {e}")

# =====================================================================
PERSONALITY = "You are bob my IT assistant"
MAX_HISTORY = 20
# =====================================================================

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Bob - Offline IT Assistant")
        self.geometry("900x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Chat Display Area ---
        self.chat_display = ctk.CTkTextbox(
            self,
            wrap="word",
            font=("Segoe UI", 15),
            state="disabled" # Prevent user from typing directly in the history
        )
        self.chat_display.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # --- Input Area (Bottom) ---
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.msg_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Ask Bob a question...",
            font=("Segoe UI", 14),
            height=40
        )
        self.msg_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.msg_entry.bind("<Return>", self.on_send_pressed) # Send on Enter key

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Send",
            font=("Segoe UI", 14, "bold"),
            width=80,
            height=40,
            command=self.on_send_pressed
        )
        self.send_btn.grid(row=0, column=1)

        # --- State Variables ---
        self.chat_history = []
        self.llm = None

        # Start loading the AI in the background so the UI boots up instantly
        self.append_to_chat("System", "Booting up Bob... Please wait a few seconds.\n")
        threading.Thread(target=self.load_ai_model, daemon=True).start()

    def load_ai_model(self):
        """Loads the model and memory without freezing the UI."""
        MODEL_PATH = get_resource_path("Llama-3.2-3B-Instruct-f16.gguf")
        try:
            self.llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            self.chat_history = load_memory()

            # Show past memory in the UI
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end") # Clear loading text
            for role, text in self.chat_history:
                name = "You" if role == "user" else "Bob"
                self.chat_display.insert("end", f"{name}:\n{text}\n\n")
            self.chat_display.configure(state="disabled")

            self.append_to_chat("System", "Bob is online and ready to help!")
            self.chat_display.yview("end") # Scroll to bottom

        except Exception as e:
            self.append_to_chat("System Error", f"Failed to load model: {e}")

    def on_send_pressed(self, event=None):
        """Triggered when the user clicks Send or presses Enter."""
        user_text = self.msg_entry.get().strip()
        if not user_text or self.llm is None:
            return

        # 1. Show user message
        self.append_to_chat("You", user_text)
        self.msg_entry.delete(0, "end") # Clear input box

        # 2. Disable input while Bob thinks
        self.msg_entry.configure(state="disabled")
        self.send_btn.configure(state="disabled", text="...")

        # 3. Generate response in a background thread so the app doesn't freeze
        threading.Thread(target=self.generate_response, args=(user_text,), daemon=True).start()

    def generate_response(self, user_text):
        """Handles the heavy AI processing."""
        try:
            full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{PERSONALITY}<|eot_id|>"
            for role, text in self.chat_history:
                full_prompt += f"<|start_header_id|>{role}<|end_header_id|>\n{text}<|eot_id|>"

            full_prompt += f"<|start_header_id|>user<|end_header_id|>\n{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"

            output = self.llm(full_prompt, max_tokens=256, stop=["<|eot_id|>", "<|begin_of_text|>"], echo=False)
            response = output['choices'][0]['text'].strip()

            # Save to memory
            self.chat_history.append(("user", user_text))
            self.chat_history.append(("assistant", response))
            if len(self.chat_history) > MAX_HISTORY:
                self.chat_history = self.chat_history[-MAX_HISTORY:]
            save_memory(self.chat_history)

            # Re-enable UI and show response
            self.after(0, self.finish_response, response)

        except Exception as e:
            self.after(0, self.finish_response, f"[Error generating response: {e}]")

    def finish_response(self, response_text):
        """Safely updates the UI after the thread finishes."""
        self.append_to_chat("Bob", response_text)
        self.msg_entry.configure(state="normal")
        self.send_btn.configure(state="normal", text="Send")
        self.msg_entry.focus() # Put cursor back in the box

    def append_to_chat(self, sender, text):
        """Helper to inject text into the chat history view."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}:\n{text}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.yview("end") # Auto-scroll to bottom

def main():
    app = ChatApp()
    app.mainloop()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()