import pytest
from src_llm.llm import generate_text
from unittest.mock import patch, MagicMock


@patch("src_llm.llm.AutoModelForCausalLM.from_pretrained")
@patch("src_llm.llm.AutoTokenizer.from_pretrained")
def test_text_generation(mock_tokenizer, mock_model):
    mock_tokenizer.return_value = MagicMock()
    mock_model.return_value = MagicMock()
    mock_model.return_value.generate.return_value = [[1, 2, 3]]
    mock_tokenizer.return_value.decode.return_value = "Generated text"

    result = generate_text("test", device="cpu")
    assert result == "Generated text"

def test_empty_prompt():
    result = generate_text("", device="cpu")
    assert "Пустой запрос" in result