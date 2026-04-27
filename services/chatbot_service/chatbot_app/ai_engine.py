import tensorflow as tf
import pandas as pd
import numpy as np
import os
import keras

# CRITICAL FIX for Keras 3: Allow Lambda deserialization
# The user's model uses Lambda layers which are blocked by default in new Keras versions.
try:
    if hasattr(keras, 'config'):
        keras.config.enable_unsafe_deserialization()
    elif hasattr(tf.keras, 'config'):
        tf.keras.config.enable_unsafe_deserialization()
except Exception as e:
    print(f">>> Warning: Could not enable unsafe deserialization: {e}")

class AIEngine:
    def __init__(self):
        self.model_path = "/app/ai_model/best_model.h5"
        self.csv_path = "/data_user500.csv"
        self.model = None
        self.action_encoder = None
        self.product_encoder = None
        self.max_seq_len = 16

        if os.path.exists(self.model_path) and os.path.exists(self.csv_path):
            self._initialize()
        else:
            print(f">>> AI Engine: Files missing. Model: {os.path.exists(self.model_path)}, CSV: {os.path.exists(self.csv_path)}")

    def _initialize(self):
        try:
            print(f">>> Initializing Encoders from {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            
            # Simple Label Encoding based on the CSV used for training
            actions = df['action'].unique().tolist()
            products = df['product_id'].unique().tolist()
            
            self.action_to_idx = {a: i for i, a in enumerate(actions)}
            self.product_to_idx = {p: i for i, p in enumerate(products)}
            self.idx_to_product = {i: p for p, i in self.product_to_idx.items()}
            
            print(f">>> Max Sequence Length: {self.max_seq_len}")
            print(f">>> Loading Model from {self.model_path}")
            
            # Load the model with safe_mode=False as a fallback
            self.model = tf.keras.models.load_model(self.model_path, compile=False)
            print(">>> Model loaded successfully!")
        except Exception as e:
            print(f">>> Error loading model: {e}")

    def _normalize_action(self, action):
        a = str(action).strip().lower()
        if 'view' in a:
            return 'view'
        if 'add_to_cart' in a or 'cart' in a:
            return 'add_to_cart'
        if 'search' in a:
            return 'search'
        if 'click' in a:
            return 'click'
        if 'purchase' in a or 'bought' in a:
            return 'purchase'
        return a

    def predict_next_product(self, action_history, product_history):
        if not self.model: return None
        
        # Preprocessing
        act_seq = [self.action_to_idx.get(self._normalize_action(a), 0) for i, a in enumerate(action_history)]
        prod_seq = [self.product_to_idx.get(int(p), 0) for i, p in enumerate(product_history)]
        
        # Pad sequences
        act_seq = (act_seq + [0] * self.max_seq_len)[:self.max_seq_len]
        prod_seq = (prod_seq + [0] * self.max_seq_len)[:self.max_seq_len]
        
        # Predict
        try:
            preds = self.model.predict([np.array([act_seq]), np.array([prod_seq])], verbose=0)
            
            # Get top 3 product indices
            top_3_idx = np.argsort(preds[0])[-3:][::-1]
            top_3_products = [int(self.idx_to_product.get(idx, 0)) for idx in top_3_idx if idx in self.idx_to_product]
            
            return {
                "top_1": top_3_products[0] if len(top_3_products) > 0 else None,
                "top_3": top_3_products
            }
        except Exception as e:
            print(f"Prediction Error: {e}")
            return None

# Singleton
_ai_instance = None
def get_ai_engine():
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = AIEngine()
    return _ai_instance
