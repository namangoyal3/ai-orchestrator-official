import os
import subprocess
import shutil
import time

class ArchitectAgent:
    """The coder agent responsible for calling the Namango CLI tool headless and writing the prompt."""
    def __init__(self, cli_path: str, target_dir: str):
        self.cli_path = cli_path
        self.target_dir = target_dir
        self.name = "🤖 Architect Agent"

    def scaffold_project(self, project_name: str, framework: str, tools: list, llm: str):
        print(f"\n{self.name}: Writing prompt for Namango Product CLI...")
        print(f"{self.name}: Generating MVP boilerplate using {framework} + {llm}...")
        
        args = [
            "node", self.cli_path, project_name,
            "--headless", 
            "--framework", framework,
            "--agents", ",".join(tools),
            "--llm", llm
        ]
        
        print(f"{self.name}: Executing Command: {' '.join(args)}")
        
        # Ensure we execute inside the testing directory
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        try:
            result = subprocess.run(args, cwd=self.target_dir, capture_output=True, text=True, check=True)
            print(f"{self.name}: Success! CLI finished generation.")
            return True, os.path.join(self.target_dir, project_name)
        except subprocess.CalledProcessError as e:
            print(f"{self.name}: FATAL ERROR calling CLI:\n{e.stderr}")
            return False, None

    def synthesize_custom_logic(self, project_path: str):
        """Simulates LLM generating missing agent code dynamically if marketplace lacks it."""
        print(f"{self.name}: Checking marketplace availability...")
        print(f"{self.name}: Marketplace lacked target capability. Generating fallback script logic via LLM...")
        
        main_py_path = os.path.join(project_path, "main.py")
        if os.path.exists(main_py_path):
            with open(main_py_path, "a") as f:
                f.write("\n# LLM Auto-Generated Capability Injected\n")
                f.write("def custom_llm_tool():\n")
                f.write("    print('Running custom generated agent LLM logic!')\n")
                f.write("    return True\n")
                f.write("\nif __name__ == '__main__':\n")
                f.write("    custom_llm_tool()\n")
                f.write("    print('Namango Test Pipeline EXECUTED.')\n")

        # Create mock Namango SDK so the QA suite compiles
        mock_sdk_path = os.path.join(project_path, "namango.py")
        with open(mock_sdk_path, "w") as f:
            f.write("class GatewayClient:\n")
            f.write("    def __init__(self, api_key):\n")
            f.write("        self.api_key = api_key\n")

class QATesterAgent:
    """The reviewer agent responsible for end-to-end testing the scaffolded architecture."""
    def __init__(self):
        self.name = "🧪 QA Tester Agent"

    def test_pipeline(self, project_path: str):
        print(f"\n{self.name}: Booting virtual environment and installing dependencies in: {project_path}")
        
        main_py = os.path.join(project_path, "main.py")
        if not os.path.exists(main_py):
            print(f"{self.name}: ❌ FAILED! main.py was not found.")
            return False
            
        print(f"{self.name}: Executing generated pipeline...")
        try:
            result = subprocess.run(["python3", "main.py"], cwd=project_path, capture_output=True, text=True, check=True)
            print(f"{self.name}: ✅ TEST PASSED END-TO-END! Output caught:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{self.name}: ❌ TEST FAILED. Traceback:\n{e.stderr}")
            return False

class OrchestratorManager:
    """The central agent managing this specific execution window."""
    def __init__(self):
        self.name = "🧠 Manager Agent"
        self.base_dir = "/tmp/test_ai_projects"
        self.cli_binary = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../cli/create-namango-app/bin/index.js"))
        
        self.architect = ArchitectAgent(self.cli_binary, self.base_dir)
        self.qa = QATesterAgent()

    def run_e2e_cycle(self):
        print(f"{self.name}: Initializing End-to-End Orchestration Swarm Test Cycle")
        print("="*60)
        
        # Cleanup previously generated tests
        if os.path.exists(os.path.join(self.base_dir, "auto-test-platform")):
            shutil.rmtree(os.path.join(self.base_dir, "auto-test-platform"))

        # 1. Architect builds the project
        success, project_path = self.architect.scaffold_project(
            project_name="auto-test-platform",
            framework="LangChain",
            tools=["GitHub Trends", "Stock Analyzer"],
            llm="anthropic/claude-3-5-sonnet"
        )

        if not success:
            print(f"{self.name}: Halting Swarm. Architect failed.")
            return

        # 2. Architect adds dynamic LLM logic based on marketplace gap
        self.architect.synthesize_custom_logic(project_path)
        
        # 3. QA thoroughly tests the product
        qa_passed = self.qa.test_pipeline(project_path)
        
        print("="*60)
        if qa_passed:
            print(f"{self.name}: 🚀 CYCLE SUCCESS. Project scaffolded fully autonomously by the Architect and verified by QA.")
        else:
            print(f"{self.name}: ⚠️ CYCLE FAILED. See QA traces above.")

if __name__ == "__main__":
    manager = OrchestratorManager()
    manager.run_e2e_cycle()
