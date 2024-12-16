from modules.shared import opts
import modules.scripts as scripts
import gradio as gr
import subprocess
import os

# Read the text file, expecting 5 lines.
# Each line follows the scheme: Program name, script path and filename, commandline parameters (if any)
# Example of a line in the text file:
# My Program, /path/to/script.py, --option=xyz
#
# Please place the text file "scripts_list.txt" in the same directory as this script.

class Script(scripts.Script):
    def title(self):
        return "External Script Launcher"

    def __init__(self):
        super().__init__()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.script_list_file = os.path.join(script_dir, "scripts_list.txt")
        
        self.scripts_data = []
        if os.path.exists(self.script_list_file):
            with open(self.script_list_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) == 3:
                            prog_name, script_path, params = parts
                            self.scripts_data.append((prog_name, script_path, params))
        else:
            for i in range(5):
                self.scripts_data.append((f"Program {i+1}", f"/path/to/script{i+1}.py", ""))

        if len(self.scripts_data) < 5:
            for i in range(len(self.scripts_data), 5):
                self.scripts_data.append((f"Program {i+1}", f"/path/to/script{i+1}.py", ""))
        elif len(self.scripts_data) > 5:
            self.scripts_data = self.scripts_data[:5]

    def run_external_script(self, button_index, script_path, params):
        param_list = []
        if params:
            param_list = params.split()
        python_exe = "python"
        try:
            subprocess.run([python_exe, script_path] + param_list, check=True)
            return "Script executed successfully."
        except Exception as e:
            # Print an error to the console only
            print(f"Error: Could not execute script '{script_path}' at button {button_index+1}. Reason: {e}")
            # Return an empty string or a neutral message so the UI doesn't show an error.
            return ""

    def ui(self, is_img2img):
        outputs = []
        with gr.Group():
            with gr.Box():
                gr.Markdown("### Start external programs")
                result = gr.Textbox(label="Result", value="", interactive=False)
                for i, (prog_name, script_path, params) in enumerate(self.scripts_data):
                    btn = gr.Button(value=prog_name)
                    # Pass button index to the function
                    btn.click(fn=lambda idx=i, sp=script_path, pa=params: self.run_external_script(idx, sp, pa), inputs=[], outputs=[result])
                outputs.append(result)
        return outputs

    def run(self, p):
        return p
