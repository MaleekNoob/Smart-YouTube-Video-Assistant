import tensorflow as tf
import numpy as np
import os
from tqdm import tqdm


model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, pooling='avg')

def load_and_preprocess_image(image_path):
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=(224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    return img_array

# Function to extract features from an image
def extract_features(image_path):
    img_array = load_and_preprocess_image(image_path)
    features = model.predict(img_array)
    return features.flatten()

folder_path = r'C:\Users\grace\Downloads\aimLabv2.0\static\images'
image_paths = [os.path.join(folder_path, img_name) for img_name in os.listdir(folder_path) if img_name.lower().endswith('.jpg')]

features = []
for img_path in tqdm(image_paths):
    try:
        features.append(extract_features(img_path))
    except Exception as e:
        print(f"Error processing {img_path}: {str(e)}")

distances = []
for i in range(len(features)):
    for j in range(i + 1, len(features)):
        distance = np.linalg.norm(features[i] - features[j])  # Euclidean distance
        distances.append((distance, image_paths[i], image_paths[j]))

distances.sort(reverse=True, key=lambda x: x[0])

# Print top 5 most different images
top_n = 5
for dist, img1, img2 in distances[:top_n]:
    print(f"Distance: {dist:.2f}\nImage 1: {img1}\nImage 2: {img2}\n")