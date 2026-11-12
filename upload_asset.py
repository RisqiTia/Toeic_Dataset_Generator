import os
import requests


UPLOAD_URL = "https://toeic-prep.my.id/api/upload_asset.php"


def upload_file(file_path, folder):
    """
    Upload file ke hosting.

    file_path:
        lokasi file di komputer lokal

    folder:
        contoh:
        materials/images
        materials/audio
        part1/images
        part1/audio
        part2/audio/question
    """

    if not os.path.exists(file_path):
        raise Exception(f"File tidak ditemukan: {file_path}")

    with open(file_path, "rb") as file:

        response = requests.post(
            UPLOAD_URL,
            files={
                "file": file
            },
            data={
                "folder": folder
            }
        )

    data = response.json()

    if data["status"] != "success":
        raise Exception(data["message"])

    return data["path"]