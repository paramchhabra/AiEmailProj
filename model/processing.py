from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch

def qnamodel(content, question):
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-distilled-squad")
    model = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased-distilled-squad")

    inputs = tokenizer(question, content, return_tensors="pt")

    #get model outputs without gradient computation (inference mode)
    with torch.no_grad():
        outputs = model(**inputs)
    
    #extracting start and end logits (location of the answer)
    start_logits = outputs.start_logits
    end_logits = outputs.end_logits

    # Get the most likely start and end positions
    start_idx = torch.argmax(start_logits)
    end_idx = torch.argmax(end_logits) + 1

    #convert the answer into normal answer text
    answer_tokens = inputs["input_ids"][0][start_idx:end_idx]
    answer = tokenizer.decode(answer_tokens)

    return answer
