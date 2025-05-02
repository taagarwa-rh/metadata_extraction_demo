## Warnings

This application uses AI to extract structured data from PDFs. The extracted data may contain errors and should not be relied upon as a definitive source of information. Always verify the extracted data before using it in any critical applications.

If the uploaded PDF is too large to fit entirely within the context window of your LLM, the extracted data may be incomplete or inaccurate.

## Usage

1. On the **Upload PDF** Tab, you can upload a PDF by clicking the "X" in the Upload PDF widget. Review your PDF and confirm that everything looks ok.
2. In the **Configuration** Tab, you can configure your extraction models and methods.
   - Extraction Model: LLM to use for metadata extraction. If you're connected to vLLM, there may only be one option here.
   - OCR Method: OCR method to use in Docling to extract text from the PDF.
     - EasyOCR: Extract using the EasyOCR method. Fastest and fewest resources needed.
     - VLM: Extract using `ds4sd/SmolDocling-256M-preview` (or `ds4sd/SmolDocling-256M-preview-mlx-bf16` on Silicon) vision language model. Slowest and best accuracy. Does not work on all documents.
     - OCRMac: Extract using OCRMac. Slower but more accurate than EasyOCR. Available on Silicon only.
     - Server: Extract using a Docling Server. Available only if you've configured a Docling server.
   - Force Full Page OCR: Force OCR on the full page. If not enabled, OCR will only be used in areas where the text is not encoded in the PDF. Only affects EasyOCR and OCRMac methods
   - Metadata Structure: Specify your metadata structure. See the "Metadata Structure Schema" section below for more information on this format.
   - System Prompt: Specify an optional system prompt. You can use this space to instruct the LLM on its task and what the fields mean to improve the accuracy of results.
3. Once this is all configured, go to the **Metadata Extractor** tab and click the "Extract Text + Metadata" button. After a minute or so, the text and extracted metadata will be displayed!

Additionally, you can use the **Compare OCR Methods** tab to extract text from the document using different Docling OCR methods and compare the results side by side.

## Metadata Structure Schema

### Basic Format
```yaml
key1:
  type: [string, float, int, bool, object, array, enum]
key2:
  type: [string, float, int, bool, object, array, enum]
...
```

### Object Format
```yaml
key:
  type: object
  properties:
    key1:
      type: [string, float, int, bool, object, array, enum]
    key2:
      type: [string, float, int, bool, object, array, enum]
```

### Array Format
```yaml
key:
  type: array
  items: [string, float, int, bool, object, array, enum]
key:
  type: array
  items: object
  properties:
    key1:
      type: [string, float, int, bool, object, array, enum]
    key2:
      type: [string, float, int, bool, object, array, enum]
```

### Enum Format
```yaml
key:
  type: enum
  options: 
    - option1
    - option2
    ...
```