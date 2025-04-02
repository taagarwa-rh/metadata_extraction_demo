## Warnings

This application uses AI to extract structured data from PDFs. The extracted data may contain errors and should not be relied upon as a definitive source of information. Always verify the extracted data before using it in any critical applications.

If the uploaded PDF is too large to fit entirely within the context window of your LLM, the extracted data may be incomplete or inaccurate.

## Usage

1. Select a model from the dropdown. If you're connected to vLLM, there may only be one option here
2. (Optional) Enable Force Full Page OCR to extract text using only OCR. If you notice there is information missing in the output, try enabling this setting.
3. To run the demo:
   1. Simply click the "Extract Metadata" button.
   2. You can play around with different models and different metadata structures and see how the outputs are affected.
4. To run your own PDF:
   1. Click the "X" button in the Upload PDF window
   2. Click "Click to Upload" and browse for your PDF file.
   3. Clear the Metadata Structure field and write your own metadata structure following the schema below.
   4. Click the "Extract Metadata" button and review the extracted metadata.

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