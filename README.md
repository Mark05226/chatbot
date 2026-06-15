first 
# Create the virtual environment
python -m venv .venv

# Activate the environment (Windows)
.\.venv\Scripts\activate

# Install the required packages
pip install customtkinter llama-cpp-python pyinstaller

second
https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/blob/main/Llama-3.2-3B-Instruct-f16.gguf 
download this llm and put it in script

third
python script/main.py

for compiling 
python -m PyInstaller --clean --noconfirm --collect-all llama_cpp --noconsole script/main.py

than put you llm in the dist/main folder

run the exe file
