import argparse
import torch
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

from l4_divergence.dataset.loader import DatasetBuilder
from l4_divergence.features.vocabulary import SyscallVocabulary
from l4_divergence.hpc.aligner import HPCWindowAligner
from l4_divergence.features.extractor import BehaviorFeatureExtractor
from l4_divergence.features.normalizer import FeatureNormalizer
from l4_divergence.siamese.model import SiameseRecurrentAutoencoder
from l4_divergence.isolation_forest.detector import IsolationForestDetector
from l4_divergence.ensemble.divergence import DivergenceEnsemble
from l4_divergence.ece.manager import ECEManager

def handle_l4_train(args):
    print("Building L4 Dataset...")
    builder = DatasetBuilder("cli_agent")
    dataset = builder.build_dataset(num_legit=500, num_attack=100) # smaller for quick demo
    
    vocab = SyscallVocabulary()
    aligner = HPCWindowAligner()
    extractor = BehaviorFeatureExtractor(vocab, aligner)
    
    print("Extracting features...")
    legit_features = [extractor.extract(seq, hpc) for seq, hpc in dataset["legitimate"]]
    
    normalizer = FeatureNormalizer()
    numeric_flat = [f.to_flat_numeric() for f in legit_features]
    normalizer.fit(numeric_flat)
    
    print("Training Siamese Autoencoder...")
    # 10 is length of num features
    num_numeric = len(numeric_flat[0])
    model = SiameseRecurrentAutoencoder(vocab.size(), num_numeric_features=num_numeric)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # Very basic training loop to prove architecture runs
    for epoch in range(5):
        # Sample random pairs (we want them to be close)
        optimizer.zero_grad()
        idx_a, idx_b = np.random.randint(0, len(legit_features), 2)
        seq_a = torch.tensor([legit_features[idx_a].sequence_features], dtype=torch.long)
        num_a = torch.tensor([normalizer.transform(legit_features[idx_a].to_flat_numeric())], dtype=torch.float32)
        
        seq_b = torch.tensor([legit_features[idx_b].sequence_features], dtype=torch.long)
        num_b = torch.tensor([normalizer.transform(legit_features[idx_b].to_flat_numeric())], dtype=torch.float32)
        
        la, lb, dist = model(seq_a, num_a, seq_b, num_b)
        loss = dist.mean() # Minimize distance for legit-legit pairs
        loss.backward()
        optimizer.step()
    
    print("Training Isolation Forest...")
    iso = IsolationForestDetector()
    normalized_numeric = np.array([normalizer.transform(f) for f in numeric_flat])
    iso.fit(normalized_numeric)
    
    print("Training ECE...")
    ensemble = DivergenceEnsemble()
    # Mock scores for ECE baseline
    iso_scores = iso.score(normalized_numeric)
    # Fit calibrator
    siam_scores = [0.1] * len(iso_scores) # Mock for now
    ensemble.calibrator.fit(siam_scores, list(iso_scores))
    
    final_scores = [ensemble.evaluate(0.1, iso_s)["score"] for iso_s in iso_scores]
    
    ece = ECEManager()
    ece.initialize(final_scores)
    
    print(f"Training complete. ECE Threshold (99th percentile): {ece.threshold:.4f}")
    
def setup_parser(subparsers):
    l4_parser = subparsers.add_parser("l4", help="L4 Behavioral Divergence commands")
    l4_subs = l4_parser.add_subparsers(dest="l4_cmd", required=True)
    
    train_parser = l4_subs.add_parser("train", help="Train the L4 anomaly models")
