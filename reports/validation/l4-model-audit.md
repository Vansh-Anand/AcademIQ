# L4 Model Validation Audit

## 1. Feature Representation
- **Input Features**: `SyscallVocabulary` tokenizes system calls. HPC alignments scale numerically.
- **Dimensionality**: Sequence embeddings generated via `SyscallVocabulary.vocab_size` (dynamically bounded).
- **Window Size**: Hardcoded / configured to 64 tokens per event sequence slice.
- **Stride**: Slided at stride=1 for the benchmark evaluations.

## 2. Model: SiameseRecurrentAutoencoder
- **Training**: Contrastive Loss + MSE reconstruction.
- **Inference**: Returns a distance metric against the centroid.
- **Thresholding**: Hand-tuned based on the `agent_test` synthetic data distribution, usually 95th percentile of the legitimate dataset reconstruction errors.
- **Limitation**: Uses synthetic data loops. Not generalized to real, unseen attacks on production environments.

## 3. Model: IsolationForestDetector
- **Training**: Fits directly on the flattened and scaled feature vectors.
- **Inference**: Returns an anomaly score (negative vs positive).
- **Limitation**: Prone to statistical noise during very small training splits (observed intermittently during CI testing).

## 4. ECES Poisoning Defense
- **Validation Status**: INTEGRATION TESTED.
- **Test Strategy**: Introduced an "attack" sequence incrementally over an established baseline window. The pipeline successfully flags it without permanently widening the threshold envelope to admit future attacks.
