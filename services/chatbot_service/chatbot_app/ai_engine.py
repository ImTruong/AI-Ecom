import os
import pickle
import numpy as np
from typing import Any, Optional, List, Dict

try:
    import tensorflow as tf
    import keras
    # CRITICAL FIX for Keras 3: Allow Lambda deserialization
    if hasattr(keras, 'config'):
        keras.config.enable_unsafe_deserialization()
    elif hasattr(tf.keras, 'config'):
        tf.keras.config.enable_unsafe_deserialization()
except Exception as e:
    tf = None
    print(f">>> Warning: Could not import TensorFlow or configure deserialization: {e}")

class AIEngine:
    def __init__(self):
        self.model_path = "/app/AI/new/GRU_best_model.h5"
        self.encoder_path = "/app/AI/new/encoders.pkl"
        self.model = None
        self.encoders = {}
        self.max_seq_len = 20
        self._initialize()

    def _initialize(self):
        if tf is None:
            print(">>> AIEngine: TensorFlow is not available, prediction disabled.")
            return
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.encoder_path):
                self.model = tf.keras.models.load_model(self.model_path)
                with open(self.encoder_path, "rb") as f:
                    self.encoders = pickle.load(f)
                print(f">>> AIEngine: GRU Model loaded successfully from {self.model_path}")
            else:
                print(f">>> AIEngine: Files missing. Model: {os.path.exists(self.model_path)}, Encoders: {os.path.exists(self.encoder_path)}")
        except Exception as e:
            print(f">>> Error loading GRU model in chatbot: {e}")

    @property
    def ready(self) -> bool:
        return self.model is not None and bool(self.encoders)

    def _encode(self, encoder_name: str, raw_value: Any, offset: int = 0) -> Optional[int]:
        if raw_value is None:
            return None
        encoder = self.encoders.get(encoder_name)
        if encoder is None:
            return None
        try:
            return int(encoder.transform([raw_value])[0]) + offset
        except Exception:
            try:
                return int(encoder.transform([str(raw_value)])[0]) + offset
            except Exception:
                return None

    def _normalize_action(self, action):
        a = str(action).strip().lower()
        if 'view' in a or 'pv' in a:
            return 'pv'
        if 'add_to_cart' in a or 'cart' in a:
            return 'cart'
        if 'purchase' in a or 'buy' in a or 'bought' in a:
            return 'buy'
        return 'pv'

    def predict_purchase_probability(self, history: list, target_id: int, products_info: dict) -> Optional[float]:
        """
        Predict purchase probability of target_id based on user history.
        history: list of dicts, each having 'action', 'product_id', 'category_id'.
        """
        if not self.ready:
            return None

        target_encoded = self._encode("item_encoder", target_id, offset=1)
        if target_encoded is None:
            return None

        # Build chronological sequences (history is sorted oldest first)
        encoded_behaviors = []
        encoded_items = []
        encoded_categories = []

        for h in history[-self.max_seq_len:]:
            pid = h.get('product_id')
            action = self._normalize_action(h.get('action') or h.get('behavior'))
            
            # Fetch category ID either from history item, or from products_info
            cat_id = h.get('category_id')
            if cat_id is None and products_info and pid in products_info:
                cat_id = products_info[pid].get('category_id')

            behavior = self._encode("behavior_encoder", action)
            item = self._encode("item_encoder", pid, offset=1)
            category = self._encode("category_encoder", cat_id, offset=1)

            if behavior is None or item is None or category is None:
                continue

            encoded_behaviors.append(behavior)
            encoded_items.append(item)
            encoded_categories.append(category)

        # Pad sequences (pre-padding with 0s)
        pad_len = self.max_seq_len - len(encoded_behaviors)
        if pad_len > 0:
            encoded_behaviors = [0] * pad_len + encoded_behaviors
            encoded_items = [0] * pad_len + encoded_items
            encoded_categories = [0] * pad_len + encoded_categories

        try:
            inputs = [
                np.array([encoded_behaviors], dtype=np.int32),
                np.array([encoded_items], dtype=np.int32),
                np.array([encoded_categories], dtype=np.int32),
                np.array([[target_encoded]], dtype=np.int32),
            ]
            return float(self.model.predict(inputs, verbose=0)[0][0])
        except Exception as e:
            print(f"AIEngine prediction error for target {target_id}: {e}")
            return None

# Singleton
_ai_instance = None
def get_ai_engine():
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = AIEngine()
    return _ai_instance
