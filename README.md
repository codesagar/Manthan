# Digitizing medical reports

Just upload the photo of medical reports. The system uses OCR and segregates the data into a key-value store.
The aim is to create a repository of medical reports along with annotations (possibly from doctors). This can help with patient's history management. More importantly the data can be anonymised and used for medical discoveries.

### Stack
1. Python-Flask
2. Azure Blobs (images)
3. MongoDB (key-value store)
4. OCR API (HP haven on demand or Tesseract)
5. Apache NGINX
