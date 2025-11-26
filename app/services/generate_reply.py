from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load model once
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

# Ensure pad token is set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Put model in eval mode for faster inference
model.eval()
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def reply(text: str, max_length: int = 50) -> str:
    """Generate a response from DialoGPT-small quickly"""
    with torch.no_grad():  # no gradient, faster
        # Tokenize input
        inputs = tokenizer(text, return_tensors="pt", padding=True).to(device)
        # Generate response
        reply_ids = model.generate(
            **inputs,
            max_length=max_length,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,           # optional: adds variety
            top_k=50,                 # optional: limits token choices
            top_p=0.95,
            temperature=0.7
        )
        # Decode generated ids to text
        reply_text = tokenizer.decode(reply_ids[:, inputs['input_ids'].shape[-1]:][0], skip_special_tokens=True)
    return reply_text

# Example usage
if __name__ == "__main__":
    print(reply("Hi!"))
