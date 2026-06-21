# VIL Architecture

## Overview

Visual Intelligence Layer (VIL) is a premium-grade image processing and publishing pipeline designed for WordPress-based content management systems. It provides intelligent image selection, metadata generation, optimization, and seamless integration with WordPress media libraries.

## System Components

### Core Pipeline (`src/core/`)

1. **Orchestrator** (`yo_orchestrator.py`)
   - Main command handler
   - Parses user commands and orchestrates full pipeline
   - Manages workflow between different modules

2. **Image Processor** (`yo_image_processor.py`)
   - Image loading and validation
   - Format conversion and optimization
   - Quality assessment

3. **Metadata Generator** (`yo_metadata_generator.py`)
   - EXIF data extraction
   - AI-powered tagging
   - SEO optimization

4. **WordPress Uploader** (`yo_wp_uploader.py`)
   - REST API integration
   - Batch upload handling
   - Media library management

5. **Media Publish** (`media_publish.py`)
   - Content embedding
   - Slug generation
   - Path management

6. **Cloud Vision** (`yo_cloud_vision.py`)
   - Google Cloud Vision integration
   - Image recognition
   - Automatic tagging

### Visual Memory (`src/visual_memory/`)

- Persistent image metadata storage
- Semantic search capabilities
- Image relationship tracking
- Deposit management

### Utilities (`src/utils/`)

- Deep verification tools
- Image distribution helpers
- Repair utilities

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  POST ID    │ ──► │ Orchestrator  │ ──► │  Fetch Post │
│  Input      │     │               │     │  Context    │
└─────────────┘     └──────────────┘     └─────────────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  WordPress  │ ◄── │   Upload     │ ◄── │  Process    │
│   Media     │     │   Images     │     │  & Optimize │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Technology Stack

- **Language**: Python 3.9+
- **Image Processing**: PIL/Pillow, OpenCV
- **AI/ML**: Google Cloud Vision, CLIP
- **Database**: SQLite (Visual Memory)
- **Testing**: pytest, pytest-cov
- **CI/CD**: GitHub Actions

## Security Considerations

- Environment-based configuration (`.env`)
- SQL injection prevention (parameterized queries)
- Input validation on all user inputs
- Secure credential management

## Performance

- Batch processing for efficiency
- Caching mechanisms
- Parallel processing where applicable
- Memory-efficient image handling

## Extensibility

The architecture supports:
- Custom AI providers
- Additional image sources
- New optimization algorithms
- Third-party integrations

For implementation details, see individual module documentation in `src/`.
