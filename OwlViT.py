import requests
from PIL import Image
import torch
import torch.nn as nn

from transformers import OwlViTProcessor, OwlViTForObjectDetection

class OWL_ViT(nn.Module):

    def __init__(self) -> None:
        super().__init__()

        self.processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
        self.model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")

    def get_complete_results(self, x: dict):
        texts = [x["texts"]]
        inputs = self.processor(text=texts, images=x["image"], return_tensors="pt")
        outputs = self.model(**inputs)

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
        # print(outputs)

        target_sizes = torch.Tensor([image.size[::-1]])

        # Convert outputs (bounding boxes and class logits) to COCO API
        return self.processor.post_process(outputs=outputs, target_sizes=target_sizes)

    def forward(self, x: dict):
        texts = [x["texts"]]
        inputs = self.processor(text=texts, images=x["image"], return_tensors="pt")
        outputs = self.model(**inputs)

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
        # print(outputs)

        target_sizes = torch.Tensor([x["image"].size[::-1]])

        # Convert outputs (bounding boxes and class logits) to COCO API
        results = self.processor.post_process(outputs=outputs, target_sizes=target_sizes)[0]
        all_boxes, all_scores, all_labels = results["boxes"].detach(), results["scores"].detach(), results["labels"].detach()

        best_bboxes = torch.zeros((len(x["texts"]), 4), dtype=torch.int16)

        for object_id in range(len(x["texts"])):
            boxes = all_boxes[all_labels==object_id]
            scores = all_scores[all_labels==object_id]

            best_choice = torch.argmax(scores)
            best_bboxes[object_id,:] = torch.round(boxes[best_choice])

        if len(x["texts"]) == 1:
            return best_bboxes[0]
        return best_bboxes


if __name__ == "__main__":
    from utils import draw_bounding_boxes, open_image
    owl = OWL_ViT()

    # url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    # image = Image.open(requests.get(url, stream=True).raw)
    image = open_image("/home/pita/Downloads/MicrosoftTeams-image.png")
    image.show()

    # text = ["cat", "a photo of a remote"]
    text = ["toaster"]

    x = {
        "texts": text,
        "image": image,
    }

    # results = owl.get_complete_results(x)

    # print(results)

    # i = 0  # Retrieve predictions for the first image for the corresponding text queries
    # boxes, scores, labels = results[i]["boxes"], results[i]["scores"], results[i]["labels"]

    # score_threshold = 0.1
    # for box, score, label in zip(boxes, scores, labels):
    #     box = [round(i, 2) for i in box.tolist()]
    #     if score >= score_threshold:
    #         print(f"Detected {text[label]} with confidence {round(score.item(), 3)} at location {box}")

    bboxes = owl(x)

    draw_bounding_boxes(image, bboxes)
    image.show()