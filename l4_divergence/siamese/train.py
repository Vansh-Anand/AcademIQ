import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from l4_divergence.dataset.loader import DatasetBuilder
from l4_divergence.features.vocabulary import SyscallVocabulary
from l4_divergence.features.extractor import BehaviorFeatureExtractor
from l4_divergence.hpc.aligner import HPCWindowAligner
from l4_divergence.siamese.model import SiameseRecurrentAutoencoder

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

class SiameseDataset(torch.utils.data.Dataset):
    def __init__(self, seq_pairs, num_pairs, labels):
        self.seq_a = torch.tensor([p[0] for p in seq_pairs], dtype=torch.long)
        self.seq_b = torch.tensor([p[1] for p in seq_pairs], dtype=torch.long)
        self.num_a = torch.tensor([p[0] for p in num_pairs], dtype=torch.float32)
        self.num_b = torch.tensor([p[1] for p in num_pairs], dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)
        
    def __len__(self):
        return len(self.labels)
        
    def __getitem__(self, idx):
        return self.seq_a[idx], self.num_a[idx], self.seq_b[idx], self.num_b[idx], self.labels[idx]

def extract_all(dataset_seqs, extractor):
    seq_tensors = []
    num_tensors = []
    for seq, hpc_seq in dataset_seqs:
        vec = extractor.extract(seq, hpc_seq)
        seq_tensors.append(vec.sequence_features)
        num_tensors.append(vec.to_flat_numeric())
    return seq_tensors, num_tensors

class ContrastiveLoss(nn.Module):
    def __init__(self, margin=2.0):
        super().__init__()
        self.margin = margin

    def forward(self, distance, label):
        # label=0 (similar), label=1 (dissimilar)
        loss = (1 - label) * torch.pow(distance, 2) + \
               label * torch.pow(torch.clamp(self.margin - distance, min=0.0), 2)
        return loss.mean()

def train_siamese_model(
    num_legit=800, num_attack=150, window_size=256, epochs=10, batch_size=32, lr=0.001, seed=42
):
    print(f"--- Training Siamese Recurrent Ensemble (Seed: {seed}) ---")
    set_seed(seed)
    
    # 1. Dataset Generation
    from benchmarks.experiments.exp5_behavioral_divergence import Exp5DatasetBuilder
    builder = Exp5DatasetBuilder(agent_id="train_agent")
    dataset = builder.build_dataset(num_legit=num_legit, num_attack=num_attack, window_size=window_size)
    
    train_legit = dataset["legitimate"][:int(num_legit * 0.8)]
    val_legit = dataset["legitimate"][int(num_legit * 0.8):]
    train_anom = dataset["attack"][:int(num_attack * 0.8)]
    val_anom = dataset["attack"][int(num_attack * 0.8):]
    
    vocab = SyscallVocabulary()
    aligner = HPCWindowAligner()
    extractor = BehaviorFeatureExtractor(vocab, aligner)
    
    # 2. Extract Features
    tr_legit_seq, tr_legit_num = extract_all(train_legit, extractor)
    tr_anom_seq, tr_anom_num = extract_all(train_anom, extractor)
    val_legit_seq, val_legit_num = extract_all(val_legit, extractor)
    val_anom_seq, val_anom_num = extract_all(val_anom, extractor)
    
    num_features_dim = len(tr_legit_num[0])
    
    def make_pairs(legit_seq, legit_num, anom_seq, anom_num, num_pairs=1000):
        seq_pairs = []
        num_pairs_list = []
        labels = []
        for _ in range(num_pairs):
            if random.random() < 0.5:
                # Positive pair (legit, legit)
                idx1 = random.randint(0, len(legit_seq) - 1)
                idx2 = random.randint(0, len(legit_seq) - 1)
                seq_pairs.append((legit_seq[idx1], legit_seq[idx2]))
                num_pairs_list.append((legit_num[idx1], legit_num[idx2]))
                labels.append(0)
            else:
                # Negative pair (legit, anom)
                idx1 = random.randint(0, len(legit_seq) - 1)
                idx2 = random.randint(0, len(anom_seq) - 1)
                seq_pairs.append((legit_seq[idx1], anom_seq[idx2]))
                num_pairs_list.append((legit_num[idx1], anom_num[idx2]))
                labels.append(1)
        return seq_pairs, num_pairs_list, labels
        
    tr_seq, tr_num, tr_lab = make_pairs(tr_legit_seq, tr_legit_num, tr_anom_seq, tr_anom_num, num_pairs=1000)
    val_seq, val_num, val_lab = make_pairs(val_legit_seq, val_legit_num, val_anom_seq, val_anom_num, num_pairs=300)
    
    train_ds = SiameseDataset(tr_seq, tr_num, tr_lab)
    val_ds = SiameseDataset(val_seq, val_num, val_lab)
    
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    # 3. Model Initialization
    device = torch.device("cpu")
    model = SiameseRecurrentAutoencoder(
        vocab_size=vocab.size(), 
        num_numeric_features=num_features_dim
    ).to(device)
    
    criterion = ContrastiveLoss(margin=2.0)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # 4. Training Loop
    best_val_loss = float('inf')
    best_weights = None
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for sa, na, sb, nb, lab in train_loader:
            optimizer.zero_grad()
            la, lb, dist = model(sa.to(device), na.to(device), sb.to(device), nb.to(device))
            loss = criterion(dist, lab.to(device))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for sa, na, sb, nb, lab in val_loader:
                la, lb, dist = model(sa.to(device), na.to(device), sb.to(device), nb.to(device))
                loss = criterion(dist, lab.to(device))
                val_loss += loss.item()
                
        avg_train_loss = total_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        print(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_weights = model.state_dict().copy()
            
    # 5. Save Model and Compute Centroid
    model.load_state_dict(best_weights)
    model.eval()
    
    print("Computing benign centroid for inference...")
    with torch.no_grad():
        t_seq = torch.tensor(tr_legit_seq, dtype=torch.long)
        t_num = torch.tensor(tr_legit_num, dtype=torch.float32)
        encoded_legit = model.encode(t_seq, t_num)
        centroid = encoded_legit.mean(dim=0, keepdim=True)
        
    ckpt_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config", "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)
    
    model_path = os.path.join(ckpt_dir, "l4_siamese.pt")
    centroid_path = os.path.join(ckpt_dir, "l4_benign_centroid.pt")
    
    torch.save(model.state_dict(), model_path)
    torch.save(centroid, centroid_path)
    print(f"Saved weights to {model_path} and centroid to {centroid_path}")
    
    return {
        "epochs": epochs,
        "best_val_loss": best_val_loss,
        "vocab_size": vocab.size(),
        "num_numeric_features": num_features_dim
    }

if __name__ == "__main__":
    train_siamese_model()
