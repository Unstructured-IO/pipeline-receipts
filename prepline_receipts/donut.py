import pathlib
import torch
import re

from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image

DONUT_PRETRAINED_CORD_V2 = "unstructuredio/donut-base-labelstudio-A1.0"


def image_generator_from_local(path: str = "."):  # pragma: no cover
    """generator function for image files inside path"""
    for filename in pathlib.Path(path).glob("*.jpg"):
        with Image.open(filename) as image:
            yield image, filename


def donut_predict(model, processor, image):
    """extracts pixel values using DonutProcessor from an image and generates
    outputs using VisionEncoderDecoderModel"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    # prepare decoder inputs
    task_prompt = "<s>"
    decoder_input_ids = processor.tokenizer(
        task_prompt, add_special_tokens=False, return_tensors="pt"
    ).input_ids

    # donut block
    image_ = processor(Image.open(image), return_tensors="pt")
    pixel_values = image_.pixel_values
    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(
        processor.tokenizer.pad_token, ""
    )
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()
    output = processor.token2json(sequence)
    return output


def generate_outputs(model="donut", image=None, filename: str = ""):
    """Load the models and processor from pretrained and predicts
    the outputs using a donut model. Documents are parsed sequentially
    from an image file, filename and image_dir"""
    if model == "donut":
        processor = DonutProcessor.from_pretrained(DONUT_PRETRAINED_CORD_V2)
        model = VisionEncoderDecoderModel.from_pretrained(DONUT_PRETRAINED_CORD_V2)
    else:
        raise NotImplementedError("we are working on improving this functionality.")
    if image:
        output = donut_predict(model, processor, image)
    elif filename:
        output = donut_predict(model, processor, open(filename, "rb"))
    else:
        raise ValueError("neither image file nor filename!")
    return output[0] if isinstance(output, list) else output


def extract_fields(parsed_receipt):
    """helper function to extract fields by depth in a dictionary structure
    from a parsed document"""
    return extract_donut_fields(parsed_receipt)


def extract_donut_fields(target_dict):
    """helper function to extract fields by depth in a dictionary structure
    from a document parsed by donut model"""
    first_level_fields = list(target_dict.keys())
    second_level_fields = []
    for v in target_dict.values():
        if isinstance(v, dict):
            second_level_fields.extend(list(v.keys()))
        elif isinstance(v, list):
            for v_i in v:
                if isinstance(v_i, dict):
                    second_level_fields.extend(list(v_i.keys()))
    return first_level_fields, second_level_fields


def select_fields(parsed_receipt, selected_fields: list):
    """filter fields for a list of 'selected_fields' in a structured parsed document"""
    return select_donut_fields(parsed_receipt, selected_fields)


def select_donut_fields(target_dict, selected_fields: list):
    """filter fields for a list of 'selected_fields' in a structured document
    parsed by donut model"""
    filtered_dict = {
        field: target_dict[field] for field in target_dict.keys() if field in selected_fields
    }
    for k, v in filtered_dict.items():
        if isinstance(v, dict):
            filtered_v = {
                field: field_value for field, field_value in v.items() if field in selected_fields
            }
            filtered_dict[k] = filtered_v
        elif isinstance(v, list):
            for ix, v_i in enumerate(v):
                filtered_v_i = {
                    field: v_i[field] for field in v_i.keys() if field in selected_fields
                }
                filtered_dict[k][ix].update(filtered_v_i)
    return filtered_dict


def price_rule(ch):
    """returns a True if the char value is numeric or '.'"""
    if ch.isnumeric():
        return True
    elif ch == ".":
        return True
    else:
        return False


def apply_rule(s: str, rule):
    """apply boolean function 'rule' to a string to clean it"""
    if not isinstance(s, str):
        return s
    return "".join([ch for ch in s if rule(ch)])


def clean_fields(parsed_receipt, rule):
    """apply cleaning rule to all fields in a structured parsed document"""
    if rule == "price_rule":
        return clean_donut_fields(parsed_receipt, price_rule)
    return parsed_receipt


def clean_donut_fields(target_dict, rule):
    """apply cleaning rule to all fields in a structured document parsed by donut model"""
    filtered_dict = {field: target_dict[field] for field in target_dict.keys()}
    for k, v in filtered_dict.items():
        if isinstance(v, str):
            filtered_dict[k] = apply_rule(v, rule)
        elif isinstance(v, dict):
            filtered_v = {field: apply_rule(field_value, rule) for field, field_value in v.items()}
            filtered_dict[k] = filtered_v
        elif isinstance(v, list):
            for ix, v_i in enumerate(v):
                if isinstance(v_i, str):
                    filtered_dict[k][ix] = apply_rule(v_i, rule)
                else:
                    filtered_v_i = {field: apply_rule(v_i[field], rule) for field in v_i.keys()}
                    filtered_dict[k][ix].update(filtered_v_i)
    return filtered_dict
