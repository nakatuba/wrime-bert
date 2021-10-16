import torch
import torch.optim as optim
from sklearn.metrics import accuracy_score, mean_absolute_error
from torch.utils.data import DataLoader
from transformers import BertForSequenceClassification, BertJapaneseTokenizer

from utils.dataset import WrimeDataset


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_dataset = WrimeDataset(split="train")
    valid_dataset = WrimeDataset(split="dev")
    test_dataset = WrimeDataset(split="test")

    tokenizer = BertJapaneseTokenizer.from_pretrained(
        "cl-tohoku/bert-base-japanese-whole-word-masking"
    )
    model = BertForSequenceClassification.from_pretrained(
        "cl-tohoku/bert-base-japanese-whole-word-masking", num_labels=4
    ).to(device)

    batch_size = 32

    def collate_batch(batch):
        input_list = tokenizer(
            [text for text, _ in batch],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        label_list = torch.tensor([label for _, label in batch])
        return input_list.to(device), label_list.to(device)

    train_dataloader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_batch
    )
    valid_dataloader = DataLoader(
        valid_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_batch
    )
    test_dataloader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_batch
    )

    optimizer = optim.Adam(model.parameters(), lr=2e-5)

    num_epochs = 3
    for epoch in range(num_epochs):
        train_loss, train_acc = train(model, train_dataloader, optimizer)
        valid_loss, valid_acc = evaluate(model, valid_dataloader)
        print(f"Epoch {epoch + 1}/{num_epochs}", end=" ")
        print(f"| train | Loss: {train_loss:.4f} Accuracy: {train_acc:.4f}", end=" ")
        print(f"| valid | Loss: {valid_loss:.4f} Accuracy: {valid_acc:.4f}")

    model.eval()
    y_true = []
    y_pred = []

    with torch.no_grad():
        for input, label in test_dataloader:
            output = model(**input)
            y_true += label.tolist()
            y_pred += output.logits.argmax(dim=1).tolist()

    print("Accuracy:", accuracy_score(y_true, y_pred))
    print("MAE:", mean_absolute_error(y_true, y_pred))


def train(model, dataloader, optimizer):
    model.train()
    epoch_loss = 0
    epoch_acc = 0

    for input, label in dataloader:
        output = model(**input, labels=label)

        loss = output.loss

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        pred = output.logits.argmax(dim=1)
        acc = (pred == label).sum() / len(pred)

        epoch_loss += loss.item()
        epoch_acc += acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)


def evaluate(model, dataloader):
    model.eval()
    epoch_loss = 0
    epoch_acc = 0

    with torch.no_grad():
        for input, label in dataloader:
            output = model(**input, labels=label)

            loss = output.loss

            pred = output.logits.argmax(dim=1)
            acc = (pred == label).sum() / len(pred)

            epoch_loss += loss.item()
            epoch_acc += acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)


if __name__ == "__main__":
    main()