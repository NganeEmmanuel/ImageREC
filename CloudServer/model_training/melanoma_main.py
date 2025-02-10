import os
from train_melanoma import train_model
from evaluate_melanoma import evaluate_model


def main():
    """
    Main function to manage the melanoma classification pipeline.
    """
    # Hardcoded paths and parameters
    current_file_path = os.path.dirname(os.path.abspath(__file__))

    train_dataset_path = os.path.join(os.getcwd(), "CloudServer/dataset/skin-lesions")
    model_save_path = os.path.join(os.getcwd(), "CloudServer/models/melanoma_model.pt")

    # Training parameters
    batch_size = 32  # Optimal batch size
    num_epochs = 20  # Number of training epochs
    learning_rate = 0.0001  # Best learning rate for small datasets

    # Start training
    print("Starting training process...")
    train_model(
        data_dir=train_dataset_path,
        batch_size=batch_size,
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        model_save_path=model_save_path,
    )

    # Evaluate the model after training
    print("\nTraining completed. Starting evaluation on the test set...")
    evaluate_model(
        data_dir=train_dataset_path,
        batch_size=batch_size,
        model_path=model_save_path,
    )


if __name__ == "__main__":
    main()
