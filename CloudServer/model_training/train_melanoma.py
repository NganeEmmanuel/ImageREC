import torch
from torch import nn, optim
from tqdm import tqdm
from data_loader import get_dataloaders
from melanoma_model import create_model


def train_model(data_dir, batch_size, num_epochs, learning_rate, model_save_path):
    """
    Train the model on the dataset.

    Args:
        data_dir (str): Path to the dataset directory.
        batch_size (int): Batch size for training.
        num_epochs (int): Number of epochs.
        learning_rate (float): Learning rate for the optimizer.
        model_save_path (str): Path to save the trained model.
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    train_loader, val_loader, _ = get_dataloaders(data_dir, batch_size)
    num_classes = len(train_loader.dataset.classes)

    model = create_model(num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in tqdm(train_loader, desc=f"Training Epoch {epoch+1}/{num_epochs}"):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_accuracy = correct / total * 100
        val_accuracy = validate_model(model, val_loader, device)

        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss:.4f}, "
              f"Train Accuracy: {train_accuracy:.2f}%, Val Accuracy: {val_accuracy:.2f}%")

    torch.save(model.state_dict(), model_save_path)
    print(f"Model saved to {model_save_path}")


def validate_model(model, val_loader, device):
    """
    Validate the model on the validation set.

    Args:
        model (nn.Module): The trained model.
        val_loader (DataLoader): DataLoader for the validation set.
        device (torch.device): Device to use for evaluation.

    Returns:
        float: Validation accuracy.
    """
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    return correct / total * 100
