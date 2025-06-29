from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import argparse

def main():
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    elif torch.backends.mps.is_available():
        device = torch.device("mps:0")

    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True)
    args = parser.parse_args()

    MODEL_NAME = "facebook/opt-125m"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    inputs = tokenizer(args.prompt, return_tensors="pt")

    result = model.generate(
        input_ids=inputs["input_ids"].to(device),
        max_new_tokens= 50
    )
    print(result)

if __name__ == '__main__':
    main()