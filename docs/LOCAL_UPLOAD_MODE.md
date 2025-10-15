# Local Upload Mode - User Guide

## 📄 Overview

Local Upload Mode allows you to upload your own financial documents (10-K, 10-Q PDFs) for private analysis without using live SEC data.

---

## 🚀 How to Use

### 1. Switch to Local Mode
- Go to **Financial Reports** tab
- Click the **"Local"** button in the top-right corner

### 2. Upload PDF Documents
- Click **"Choose PDF Files"**
- Select one or more PDF files (10-K or 10-Q reports)
- Click **"📤 Upload"** button

### 3. Document Analysis
The system will automatically:
- ✅ Upload files to secure S3 bucket (`bankiq-uploaded-docs`)
- ✅ Analyze the document to identify:
  - Bank name (e.g., "Webster Bank")
  - Document type (10-K or 10-Q)
  - Year (e.g., 2024)
- ✅ Display: "You uploaded Webster Bank, 10-K document for the year 2024"

### 4. Chat with Documents
Once uploaded, you can:
- Ask questions about the documents
- Get AI-powered analysis
- Generate full reports

**Sample Questions:**
- "What are the key risk factors?"
- "How is the financial performance?"
- "What are the main revenue sources?"
- "Any regulatory concerns?"

### 5. Generate Full Report
- Click **"🚀 Generate Full Analysis"**
- Get comprehensive financial analysis
- Download the report as a text file

---

## 🔒 Security

- **Private Storage**: Documents stored in private S3 bucket
- **Secure Access**: Only accessible via IAM roles
- **No Public Access**: Files never publicly accessible
- **Encrypted**: S3 server-side encryption (AES256)

---

## 📊 Features

### Same as Live Mode
- ✅ AI-powered chat
- ✅ Full report generation
- ✅ Markdown-formatted responses
- ✅ 2-paragraph concise answers
- ✅ Source citations

### Additional Benefits
- ✅ Upload any bank's documents
- ✅ Analyze private/internal reports
- ✅ No SEC filing limitations
- ✅ Works with any financial institution

---

## 🛠️ Technical Details

### Backend Endpoint
```
POST /api/upload-pdf
Content-Type: application/json

{
  "files": [
    {
      "name": "webster_10k_2024.pdf",
      "size": 5242880,
      "content": "base64_encoded_content..."
    }
  ],
  "bankName": "Webster Bank" // optional hint
}
```

### Response
```json
{
  "success": true,
  "documents": [
    {
      "bank_name": "Webster Bank",
      "form_type": "10-K",
      "year": "2024",
      "filename": "webster_10k_2024.pdf",
      "size": 5242880
    }
  ]
}
```

### S3 Structure
```
s3://bankiq-uploaded-docs/
  └── uploads/
      └── {uuid}/
          └── {filename}.pdf
```

---

## 🧪 Testing

### Test Upload
1. Download a sample 10-K from SEC EDGAR
2. Go to Local mode
3. Upload the PDF
4. Verify it shows: "Bank Name, 10-K, Year"

### Test Chat
1. After upload, ask: "What are the key risk factors?"
2. Should get 2-paragraph response
3. No DATA: line visible

### Test Report
1. Click "Generate Full Analysis"
2. Should get 5-6 paragraph comprehensive report
3. Can download as text file

---

## 🐛 Troubleshooting

### Upload Fails
- Check file size (max 50MB)
- Ensure PDF format
- Check backend logs: `tail -f backend/server.log`

### Document Not Recognized
- System will use filename hints
- Manually specify bank name if needed
- Check if PDF is text-based (not scanned image)

### Chat Not Working
- Verify document uploaded successfully
- Check that analyzedDocs array is populated
- Ensure backend is running on port 3001

---

## 📝 Limitations

- **File Size**: Max 50MB per file
- **Format**: PDF only (text-based, not scanned images)
- **Processing Time**: 10-30 seconds per document
- **Storage**: Files stored indefinitely (manual cleanup needed)

---

## 🔄 Comparison: Live vs Local

| Feature | Live Mode | Local Mode |
|---------|-----------|------------|
| Data Source | SEC EDGAR | Your PDFs |
| Banks | Public companies only | Any bank |
| Documents | 2024-2025 filings | Any year |
| Upload Required | No | Yes |
| Privacy | Public data | Private |
| Speed | Instant | 10-30s upload |

---

## ✅ Status

- [x] S3 bucket created: `bankiq-uploaded-docs`
- [x] Backend endpoint: `/api/upload-pdf`
- [x] Frontend upload UI
- [x] Document analysis
- [x] Chat functionality
- [x] Full report generation
- [x] Same UX as live mode

**Status**: ✅ **FULLY FUNCTIONAL**

---

**Last Updated**: October 15, 2025
