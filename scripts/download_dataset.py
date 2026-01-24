import kagglehub

# Download latest version
path = kagglehub.dataset_download("abhayayare/e-commerce-dataset")

print("Path to dataset files:", path)