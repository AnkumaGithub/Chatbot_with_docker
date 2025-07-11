from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import argparse

def generate_text(prompt: str, device: torch.device) -> str:
    MODEL_NAME = "Qwen/Qwen2.5-0.5B"

    if not prompt.strip():
        return "Пустой запрос. Пожалуйста, введите текст."

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device)

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    output = model.generate(
        input_ids=inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=128,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    print(f"Generated tokens: {output}")

    result = tokenizer.decode(output[0], skip_special_tokens=True)
    print(f"Decoded text: {result}")
    return result

def main():
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    elif torch.backends.mps.is_available():
        device = torch.device("mps:0")
    else:
        device = torch.device("cpu")

    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True)
    args = parser.parse_args()

    result = generate_text(args.prompt, device)
    print(result)


if __name__ == '__main__':
    main()