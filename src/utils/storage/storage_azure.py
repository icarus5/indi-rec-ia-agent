from azure.storage.blob import BlobServiceClient, ContentSettings
import os


STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")


class StorageAzure:
    def __init__(self, container_name):
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        self.container_client = blob_service_client.get_container_client(container_name)

    def get_container_client(self):
        return self.container_client

    def upload(self, filename, img_byte_arr, type="image"):
        blob_client = self.container_client.get_blob_client(filename)
        if type == "image":
            blob_client.upload_blob(
                img_byte_arr,
                content_settings=ContentSettings(content_type="image/jpeg"),
                overwrite=True,
            )
        else:
            blob_client.upload_blob(img_byte_arr, overwrite=True)

    def get_and_apply_files(self, map_function, max_files=None, filter_name=None):
        blob_list = self.container_client.list_blobs()
        n = 0
        if filter_name:
            blob_list = [blob for blob in blob_list if blob.name == filter_name]
        for blob in blob_list:
            image = self.container_client.download_blob(blob).readall()

            map_function(image, blob.name)
            n = n + 1
            if max_files and max_files == n:
                break

    def get_all_file_names(self, file_type=None):
        blob_list = self.container_client.list_blobs()
        if file_type is None:
            return [blob.name for blob in blob_list]
        else:
            if file_type == "image":
                valid_extensions = (".png", ".jpg", ".jpeg")
                return [blob.name for blob in blob_list if blob.name.endswith(valid_extensions)]
