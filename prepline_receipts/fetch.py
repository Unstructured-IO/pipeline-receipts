import requests
from tqdm import tqdm

CORD_V2_URL = """
https://datasets-server.huggingface.co/first-rows
?dataset=naver-clova-ix%2Fcord-v2&config=naver-clova-ix--cord-v2
&split=train
"""


def query_cord():
    response = requests.request("GET", CORD_V2_URL)
    return response.json()


def sample_cord(data, number_of_samples=0, version=1):
    """
    CORD is a dataset consists of thousands of Indonesian
    receipts, which contains images and box/text annotations for OCR,
    and multi-level semantic labels for parsing.

        - Is hosted on:
            https://datasets-server.huggingface.co/assets/naver-clova-ix/
        - Dataset original repository:
            https://github.com/clovaai/cord
    parameters:
    number_of_samples:
        0 for all available in fetch url
        (100 samples for cord datasets in huggingface)
    """
    urls = []
    responses_content = []
    for k, v in data.items():
        if k != "rows":
            pass
        else:
            print("number of available images in url: ", len(v))
            for ix, row in tqdm(enumerate(v, start=1)):
                img_url = row["row"]["image"]["src"]
                urls.append(img_url)
                response = requests.get(img_url)
                if response.status_code == 200:
                    responses_content.append(response.content)
                    if number_of_samples and ix >= number_of_samples:
                        break
    return urls, responses_content
