import pandas as pd
from transformers import MarianMTModel, MarianTokenizer
import torch
from tqdm.auto import tqdm

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Используемое устройство: {device}")

model_name = "Helsinki-NLP/opus-mt-en-ru"
print("Загрузка модели и токенизатора...")
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name).to(device)
print("Модель перевода загружена!")


def translate_text(text, max_length=512):
    if not isinstance(text, str) or text.strip() == "":
        return text

    try:
        inputs = tokenizer(
            [text],
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True
        ).to(device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            num_beams=5,
            early_stopping=True
        )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    except Exception as e:
        print(f"Ошибка перевода: {str(e)}")
        return text


print("Чтение CSV файла...")
file_path = "/Users/maksimkuznetsov/Downloads/Diseases_Symptoms.csv"
df = pd.read_csv(file_path, encoding='utf-8')
print(f"Прочитано строк: {len(df)}")

columns_to_translate = ['Name', 'Symptoms', 'Treatments']
translated_df = df.copy()

for column in columns_to_translate:
    print(f"\nНачало перевода колонки: {column}")
    translated_values = []

    for value in tqdm(df[column], desc=f"Перевод {column}", total=len(df)):
        translated_values.append(translate_text(value))

    translated_df[column] = translated_values

output_path = "/Users/maksimkuznetsov/Downloads/Diseases_Symptoms_ru.csv"
print(f"\nСохранение результата в: {output_path}")
translated_df.to_csv(output_path, index=False, encoding='utf-8-sig')
print("Готово! Перевод завершен.")