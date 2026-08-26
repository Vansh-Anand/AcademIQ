import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

class SiameseRecurrentEncoder(nn.Module):
    """LSTM encoder for syscall sequences and flat features."""
    def __init__(self, vocab_size: int, embed_dim: int = 32, hidden_dim: int = 128, 
                 latent_dim: int = 64, num_numeric_features: int = 0):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=2, batch_first=True, dropout=0.1)
        
        # Combine LSTM final hidden state with numeric features to produce latent vector
        self.fc = nn.Linear(hidden_dim + num_numeric_features, latent_dim)
        
    def forward(self, seq: torch.Tensor, num_features: torch.Tensor) -> torch.Tensor:
        # seq: (batch, seq_len)
        embedded = self.embedding(seq)
        
        # lstm_out: (batch, seq_len, hidden_dim)
        lstm_out, (h_n, c_n) = self.lstm(embedded)
        
        # Take the top layer's final hidden state
        final_h = h_n[-1] # (batch, hidden_dim)
        
        if num_features.size(1) > 0:
            combined = torch.cat([final_h, num_features], dim=1)
        else:
            combined = final_h
            
        latent = self.fc(combined)
        return F.normalize(latent, p=2, dim=1)

class SiameseRecurrentAutoencoder(nn.Module):
    """
    Siamese network using shared encoder weights to compute contrastive distances.
    Although named autoencoder for historical reasons, its primary objective here is 
    contrastive embedding distance optimization.
    """
    def __init__(self, vocab_size: int, embed_dim: int = 32, hidden_dim: int = 128, 
                 latent_dim: int = 64, num_numeric_features: int = 0):
        super().__init__()
        self.encoder = SiameseRecurrentEncoder(
            vocab_size, embed_dim, hidden_dim, latent_dim, num_numeric_features
        )
        
    def forward(self, seq_a: torch.Tensor, num_a: torch.Tensor,
                seq_b: torch.Tensor, num_b: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        latent_a = self.encoder(seq_a, num_a)
        latent_b = self.encoder(seq_b, num_b)
        
        # L2 distance
        distance = F.pairwise_distance(latent_a, latent_b, p=2)
        return latent_a, latent_b, distance
        
    def encode(self, seq: torch.Tensor, num: torch.Tensor) -> torch.Tensor:
        return self.encoder(seq, num)
