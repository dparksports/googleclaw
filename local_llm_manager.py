import os
import sys
import json
import time
import zipfile
import io
import shutil
import subprocess
import requests

CONFIG_FILE = "assistant_config.json"

# Curated App-Store Style Catalog for Non-Technical Users
# All models point to highly optimized 4-bit Unsloth GGUF exports.
CATALOG = [
    {
        "brand": "DeepSeek (Best for Logic, Math & Advanced Coding)",
        "models": [
            {"name": "DeepSeek R1 (8B)  - Fast, needs ~6GB VRAM", "repo": "unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF", "file": "DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "DeepSeek R1 (14B) - Smarter, needs ~10GB VRAM", "repo": "unsloth/DeepSeek-R1-Distill-Qwen-14B-GGUF", "file": "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "DeepSeek R1 (32B) - Genius, needs ~22GB VRAM", "repo": "unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF", "file": "DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf", "engine": "llama.cpp"}
        ]
    },
    {
        "brand": "Google Gemma (Best for Creative Writing & General Tasks)",
        "models": [
            {"name": "Gemma 4 (31B) - Genius, needs ~18GB VRAM", "repo": "unsloth/gemma-4-31B-it-GGUF", "file": "gemma-4-31B-it-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Gemma 4 (26B) - Genius, needs ~16GB VRAM", "repo": "unsloth/gemma-4-26B-A4B-it-GGUF", "file": "gemma-4-26B-A4B-it-UD-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Gemma 3 (27B) - Genius, needs ~16GB VRAM", "repo": "unsloth/gemma-3-27b-it-GGUF", "file": "gemma-3-27b-it-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Gemma 3 (12B) - Smarter, needs ~8GB VRAM", "repo": "unsloth/gemma-3-12b-it-GGUF", "file": "gemma-3-12b-it-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Gemma 3 (4B)  - Fast, needs ~3GB VRAM", "repo": "unsloth/gemma-3-4b-it-GGUF", "file": "gemma-3-4b-it-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Gemma 2 (27B) - Genius, needs ~16GB VRAM", "repo": "unsloth/gemma-2-27b-it-GGUF", "file": "gemma-2-27b-it-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Gemma 2 (9B)  - Fast, needs ~6GB VRAM", "repo": "unsloth/gemma-2-9b-it-GGUF", "file": "gemma-2-9b-it-Q4_K_M.gguf", "engine": "llama.cpp"}
        ]
    },
    {
        "brand": "Meta Llama 3 (Great All-Around Assistant)",
        "models": [
            {"name": "Llama 3.2 (3B) - Ultra Fast, needs ~3GB VRAM", "repo": "unsloth/Llama-3.2-3B-Instruct-GGUF", "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Llama 3.1 (8B) - Smart & Reliable, needs ~6GB VRAM", "repo": "unsloth/Meta-Llama-3.1-8B-Instruct-GGUF", "file": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf", "engine": "llama.cpp"}
        ]
    },
    {
        "brand": "Alibaba Qwen (Fast, Multilingual, Highly Capable)",
        "models": [
            {"name": "Qwen 2.5 (7B)  - Fast, needs ~6GB VRAM", "repo": "unsloth/Qwen2.5-7B-Instruct-GGUF", "file": "Qwen2.5-7B-Instruct-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Qwen 2.5 (14B) - Smarter, needs ~10GB VRAM", "repo": "unsloth/Qwen2.5-14B-Instruct-GGUF", "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf", "engine": "llama.cpp"},
            {"name": "Qwen 2.5 (32B) - Genius, needs ~22GB VRAM", "repo": "unsloth/Qwen2.5-32B-Instruct-GGUF", "file": "Qwen2.5-32B-Instruct-Q4_K_M.gguf", "engine": "llama.cpp"}
        ]
    }
]

def ensure_hf_login():
    import huggingface_hub
    from dotenv import load_dotenv
    load_dotenv()
    env_token = os.getenv("HF_TOKEN")
    try:
        if env_token:
            huggingface_hub.login(token=env_token)
            return
        if not huggingface_hub.get_token():
            print("\n\033[93m[Warning] Models are gated. Log in to Hugging Face.\033[0m")
            huggingface_hub.login()
    except:
        huggingface_hub.login()

def build_llama_cpp_from_source():
    print("\n\033[93m[System]\033[0m Attempting to build llama.cpp from source (CUDA)...")
    print("This may take 2-5 minutes depending on your hardware.")
    try:
        if os.path.exists("llama.cpp_source"):
            try: shutil.rmtree("llama.cpp_source")
            except: pass
        
        print("Cloning repository...")
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/ggerganov/llama.cpp", "llama.cpp_source"], check=True)
        
        build_dir = os.path.join("llama.cpp_source", "build")
        os.makedirs(build_dir, exist_ok=True)
        
        print("Configuring CMake...")
        subprocess.run(["cmake", "..", "-DGGML_CUDA=ON"], cwd=build_dir, check=True)
        
        print("Building (this takes time)...")
        subprocess.run(["cmake", "--build", ".", "--config", "Release"], cwd=build_dir, check=True)
        
        # Locate the built executable
        built_exe = os.path.join(build_dir, "bin", "Release", "llama-server.exe")
        if not os.path.exists(built_exe):
            built_exe = os.path.join(build_dir, "bin", "llama-server.exe")
            
        shutil.copy(built_exe, "llama-server.exe")
        
        try: shutil.rmtree("llama.cpp_source")
        except: pass
        print("\033[92m[System]\033[0m Successfully built and installed llama-server.exe from source!")
        return True
    except Exception as e:
        print(f"\033[91m[Error]\033[0m Failed to build from source: {e}")
        return False

def download_llama_cpp():
    if os.path.exists("llama-server.exe"):
        return

    has_cmake = shutil.which("cmake") is not None
    has_nvcc = shutil.which("nvcc") is not None
    
    if has_cmake and has_nvcc:
        print("\n\033[96m[System]\033[0m Compiler tools (CMake & CUDA) detected on your system.")
        build_choice = input("Would you like to build llama.cpp from source for maximum hardware optimization? (Y/n): ").strip().lower()
        if build_choice in ['y', '']:
            if build_llama_cpp_from_source():
                return
            else:
                print("Falling back to downloading pre-compiled binary...")

    print("\n\033[94m[System]\033[0m Downloading the inference engine (llama.cpp) for Windows...")
    api_url = "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
    try:
        release_info = requests.get(api_url).json()
        assets = release_info.get("assets", [])
        
        # New naming convention: llama-<hash>-bin-win-cuda-<version>-x64.zip
        download_url = next((a["browser_download_url"] for a in assets if a["name"].startswith("llama-") and "bin-win-cuda" in a["name"]), None)
        
        # Fallback to Vulkan if CUDA is not found
        if not download_url:
            download_url = next((a["browser_download_url"] for a in assets if a["name"].startswith("llama-") and "bin-win-vulkan" in a["name"]), None)
            
        # Check if there is a cudart dependency zip
        cudart_url = next((a["browser_download_url"] for a in assets if a["name"].startswith("cudart-llama-") and "bin-win-cuda" in a["name"]), None)

        if download_url:
            print(f"Downloading Engine: {download_url.split('/')[-1]}")
            r = requests.get(download_url)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall("llama_cpp_bin")
            
            if cudart_url:
                print(f"Downloading CUDA dependencies: {cudart_url.split('/')[-1]}")
                r_cudart = requests.get(cudart_url)
                z_cudart = zipfile.ZipFile(io.BytesIO(r_cudart.content))
                z_cudart.extractall("llama_cpp_bin")
                
            for f in os.listdir("llama_cpp_bin"):
                if f.endswith(".exe") or f.endswith(".dll"):
                    shutil.move(os.path.join("llama_cpp_bin", f), f)
            shutil.rmtree("llama_cpp_bin")
            print("\033[92m[System]\033[0m Engine installed successfully!")
        else:
            print("\033[91m[Error]\033[0m Could not find a suitable Windows binary in the latest release.")
    except Exception as e:
        print(f"\033[91m[Error]\033[0m Failed to download engine: {e}")

def setup_interactive():
    print("\n\033[96m" + "="*50)
    print("🤖 Welcome to the Local AI Model Downloader")
    print("="*50 + "\033[0m")
    print("Select a model family to explore:")
    
    for i, category in enumerate(CATALOG, 1):
        print(f"  {i}. {category['brand']}")
    print(f"  {len(CATALOG) + 1}. [Advanced] Custom Hugging Face Link (e.g. your own Unsloth export)")
    
    try:
        cat_choice = int(input(f"\nEnter choice (1-{len(CATALOG)+1}): "))
    except:
        print("Invalid choice."); return

    selected_model = None

    if cat_choice == len(CATALOG) + 1:
        # Advanced / Custom Flow
        print("\n\033[93m--- Custom Model --- \033[0m")
        print("You can paste any Hugging Face repository here. We recommend Unsloth GGUF exports.")
        repo_id = input("1. Enter Repo ID (e.g., 'unsloth/Llama-3.2-3B-Instruct-GGUF'): ").strip()
        filename = input("2. Enter exact .gguf filename (e.g., 'Llama-3.2-3B-Instruct-Q4_K_M.gguf'): ").strip()
        selected_model = {"name": f"Custom ({repo_id})", "repo": repo_id, "file": filename, "engine": "llama.cpp"}
    
    elif 1 <= cat_choice <= len(CATALOG):
        # Category Flow
        category = CATALOG[cat_choice-1]
        print(f"\n\033[96m--- {category['brand']} ---\033[0m")
        for i, m in enumerate(category['models'], 1):
            print(f"  {i}. {m['name']}")
            
        try:
            m_choice = int(input(f"\nEnter choice (1-{len(category['models'])}): "))
            selected_model = category['models'][m_choice-1]
        except:
            print("Invalid choice."); return
    else:
        print("Invalid choice."); return

    ensure_hf_login()
    download_llama_cpp()
    
    from huggingface_hub import hf_hub_download
    print(f"\n\033[94m[Download]\033[0m Fetching {selected_model['name']}...")
    print("Please wait. This is a large file and may take a few minutes...")
    
    model_path = hf_hub_download(repo_id=selected_model['repo'], filename=selected_model['file'])
    print(f"\033[92m[Success]\033[0m Model downloaded to: {model_path}")

    # Save Config
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: config = json.load(f)
            except: pass
            
    config.update({
        "provider": "local",
        "engine": selected_model['engine'],
        "model": model_path,
        "model_name_display": selected_model['name'],
        "local_url": "http://localhost:8000"
    })
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
        
    print("\n\033[92m[Setup Complete]\033[0m Config saved! Your assistant will now use this model.")

def start_server():
    if not os.path.exists(CONFIG_FILE):
        print("Config not found. Run setup first.")
        return
        
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        
    engine = config.get("engine", "llama.cpp")
    model = config.get("model")
    
    print(f"\n\033[94m[Server]\033[0m Starting AI Engine...")
    
    if engine == "vllm":
        cmd = [sys.executable, "-m", "vllm.entrypoints.openai.api_server", "--model", model, "--port", "8000", "--dtype", "half"]
    else:
        # Ensure llama-server.exe exists, if not, download it now.
        download_llama_cpp()
        
        # Ask user about GPU offloading
        print("\n\033[95m[Hardware Choice]\033[0m")
        print("Would you like to offload ALL layers to your GPU?")
        print("  (Y) Yes - Fastest, requires enough VRAM.")
        print("  (N) No  - Slower, splits model between GPU and system RAM.")
        gpu_choice = input("\nOffload all to GPU? (Y/n): ").strip().lower()
        
        # -ngl (number of GPU layers). 99 usually covers all layers for most models.
        # 0 means CPU only.
        ngl = "99" if gpu_choice in ['y', ''] else "0"
        
        if ngl == "0":
            print("\033[93m[Note]\033[0m Splitting enabled. Performance will be slower.")
        else:
            print("\033[92m[Note]\033[0m Full GPU mode enabled. Using maximum VRAM.")

        # Ensure we use the exact path to the executable in the current directory
        llama_exe = os.path.join(os.getcwd(), "llama-server.exe")
        cmd = [llama_exe, "-m", model, "--port", "8000", "--ctx-size", "8192", "-ngl", ngl]
        
    try:
        process = subprocess.Popen(cmd)
        
        # Wait for health check
        for _ in range(60):
            try:
                if requests.get("http://localhost:8000/v1/models").status_code == 200:
                    print(f"\n\033[92m[Server]\033[0m Ready! You can start chatting.")
                    return process
            except: pass
            time.sleep(2)
            print(".", end="", flush=True)
            
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            p = start_server()
            if p:
                try: p.wait()
                except KeyboardInterrupt: p.terminate()
        elif sys.argv[1] == "wait":
            print("Waiting for local AI server to load into memory...", end="", flush=True)
            for _ in range(300): # Give it up to 10 minutes to load massive 31B models
                try:
                    if requests.get("http://localhost:8000/v1/models").status_code == 200:
                        print("\n\033[92m[System]\033[0m Server is fully loaded and ready!")
                        sys.exit(0)
                except:
                    pass
                time.sleep(2)
                print(".", end="", flush=True)
            print("\nTimeout waiting for server.")
    else:
        setup_interactive()