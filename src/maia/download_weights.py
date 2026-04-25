import os
import requests
from tqdm import tqdm

MAIA_MODELS = {
    "maia-1100": "https://github.com/CSSLab/maia-chess/releases/download/v1.0/maia-1100.pb.gz",
    "maia-1200": "https://github.com/CSSLab/maia-chess/releases/download/v1.0/maia-1200.pb.gz",
    "maia-1300": "https://github.com/CSSLab/maia-chess/releases/download/v1.0/maia-1300.pb.gz",
    "maia-1900": "https://github.com/CSSLab/maia-chess/releases/download/v1.0/maia-1900.pb.gz",
}

def download_file(url, dest_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    with open(dest_path, "wb") as f, tqdm(
        desc=os.path.basename(dest_path),
        total=total_size,
        unit='iB',
        unit_scale=True,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            bar.update(f.write(data))

def main():
    os.makedirs("checkpoints/maia", exist_ok=True)
    for name, url in MAIA_MODELS.items():
        dest = f"checkpoints/maia/{name}.pb.gz"
        if not os.path.exists(dest):
            print(f"Downloading {name}...")
            download_file(url, dest)
        else:
            print(f"{name} already exists.")

if __name__ == "__main__":
    main()
