import torch
from tqdm import tqdm
from data_loader import get_dataloaders
from melanoma_model import create_model


def evaluate_model(data_dir, batch_size, model_path):

    """
    Evaluate the trained model on the test set.

    Args:
        data_dir (str): Path to the dataset directory.
        batch_size (int): Batch size for evaluation.
        model_path (str): Path to the trained model file.
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    _, _, test_loader = get_dataloaders(data_dir, batch_size)
    num_classes = len(test_loader.dataset.classes)

    model = create_model(num_classes).to(device)
    model.load_state_dict(torch.load(model_path))
    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="Evaluating"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += int((predicted == labels).sum().item())

    accuracy = correct / total * 100
    print(f"Test Accuracy: {accuracy:.2f}%")
