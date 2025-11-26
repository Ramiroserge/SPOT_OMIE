# 🧾 SPOT-to-OMIE Product Sync

This project syncs products from the SPOT system to OMIE ERP using their public APIs. It ensures accurate product registration and prevents duplicates.

## 🚀 Features

- Authenticates with SPOT and OMIE
- Fetches and transforms SPOT product data
- Avoids re-inserting existing OMIE products
- Handles NCM and description constraints
- 100% test coverage with `pytest`

## 🛠 Setup

```bash
# Install dependencies
pip install -r requirements.txt
