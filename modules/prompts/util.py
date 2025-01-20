def load_prompts(prompt_dict):
    prompts = {}

    for name, path in prompt_dict.items():
        with open(path) as f:
            print(f"Loading prompts[{name}] from {path}")
            prompts[name] = f.read().strip()
    
    return prompts