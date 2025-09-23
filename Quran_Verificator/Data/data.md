# Data
- Canonical Quran text (From KDN/JAKIM)	
    - Use Tanzil/Uthmani DB for now (temporary placeholder)
- Reference images/PDFs	(From certified Quran publications)	
    - Use open images from VerseByVerseQuran.com or Madani Mushaf for now
- Approved corpus hashes (Will be provided later for enforcement)	
    - Build the hash engine and test it on own normalized version
- Rules (rasm, tajwid, etc.) (From Lajnah Tashih)	
    - Don’t need full rules now; just basic normalisation + diacritic modes
- Sample submission (developers will submit them later)
    - Use test APK placeholders, dummy binaries, or PDFs

# Tech-stack from “Technical Architecture” section:
- Frontenn: React (for Developer Portal, Reviewer Console)
- Engines: Python for Text Diff, OCR, Malware, Crawlers     # current
- APIs: REST / GraphQL (microservices + event bus)
- Database: PostgreSQL (transactions)       # SQLite for now
- File Storage: S3-compatible (object store for binaries/docs)      # Local filesystem for now
- Search/Logs: Elasticsearch / OpenSearch
- Cache/Queues:	Redis	
- Security:	PKI, HSM, IAM, audit logs
- CI/CD: Gated pipelines, SAST/DAST
- Hosting: MyGovCloud / Cloud Selamat
