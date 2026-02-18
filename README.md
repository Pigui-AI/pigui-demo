# Pigui Demo - Business Intelligence Chat Application

## Project Overview

Pigui Demo is a Streamlit-based chat application that provides an AI-powered Business Intelligence interface for analyzing business performance, customer behavior, sales, marketing campaigns, and operational metrics.

## Project Structure

```
pigui-demo/
├── streamlit_chat_branch.py    # Main application file (729 lines)
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── .streamlit/
│   └── config.toml             # Streamlit configuration
└── assets/
    └── PuguiChat-ziCgELVp.svg  # Assistant avatar image
```

## Architecture

### Technology Stack
- **Framework**: Streamlit
- **HTTP Client**: Requests
- **Python Version**: 3.11
- **Backend API**: https://backdev.pigui.ai/ (development environment)

### Page Configuration
- **Layout**: Wide mode with centered content (max-width: 1200px)
- **Theme**: Dark theme enforced globally
- **Sidebar**: Expanded by default
- **Title**: "Chat Pigui"
- **Icon**: Chat emoji

## Features

### 1. Custom Styling System

#### CSS Customizations
- Dark theme forced across all components
- Color scheme:
  - Background: #0E1117
  - Secondary background/Sidebar: #262730
  - Text: #FAFAFA
  - Borders: #4A4A4A
- Rounded chat input (border-radius: 1.5rem)
- Hidden Deploy button and menu options
- Reduced font sizes in sidebar
- Content centered with max-width constraint

#### JavaScript Enhancements
- DOM observer for dynamic content centering
- Periodic execution (100ms) as fallback
- Ensures consistent layout across page updates

### 2. Session State Management

Key session variables:
- `client_id`: Client identifier (from URL parameters)
- `branch_id`: Branch identifier (from URL parameters)
- `user_id`: User identifier (defaults to client_id)
- `current_conversation_id`: Active conversation ID
- `messages`: Chat message history
- `conversations_list`: List of user conversations
- `conversations_loaded`: Loading state flag

### 3. API Integration

#### Conversation Endpoints
- `GET /ai/conversations` - List user conversations
- `GET /ai/conversations/{id}` - Get conversation details
- `POST /ai/conversations/start` - Start new conversation
- `POST /ai/conversations/{id}/continue` - Continue existing conversation
- `PATCH /ai/conversations/{id}` - Update conversation (title/status)

#### Audio Endpoints
- `POST /ai/asr` - Audio transcription (Speech-to-Text)
- `POST /ai/tts` - Text-to-Speech synthesis

### 4. Core Functions

#### Conversation Management
- `fetch_conversations()` - Retrieve conversation list
- `fetch_conversation_detail()` - Load conversation details
- `start_new_conversation()` - Create new conversation
- `continue_conversation()` - Continue existing conversation
- `load_conversation()` - Load conversation into UI
- `update_conversation_title()` - Edit conversation title
- `archive_conversation()` - Archive conversation
- `start_new_chat()` - Start new chat (archives current)

#### Message Processing
- `process_message()` - Process user message (start or continue conversation)
- `transcribe_audio()` - Convert audio to text (ASR)
- `synthesize_speech()` - Convert text to audio (TTS)

### 5. User Interface

#### Main Chat Area
- Application title and description
- Message history with custom avatar
- Rounded chat input field
- "Play" button for TTS on assistant responses
- Automatic greeting on initialization (sends "Hello" message)

#### Sidebar - 9 Collapsible Sections

**1. Conversation History**
- List of all conversations
- Active conversation indicator (blue circle)
- Message count per conversation
- Title editing capability
- "New Conversation" button

**2. Customers & Behavior** (6 predefined questions)
- Who are my most valuable customers?
- What do they buy, when and why?
- Purchase frequency and average ticket
- Behavior before and after a reward
- New vs recurring customers
- Preferences by product, service or branch

**3. Sales & Revenue** (5 predefined questions)
- Sales by product / service
- Sales by campaign
- Real impact of promotions and rewards
- Best and worst performing products
- Upsell and cross-sell opportunities

**4. Marketing & Campaigns** (5 predefined questions)
- Which campaign type works best? (discount, gift, coupon, promo)
- When to launch a campaign?
- Who to target?
- Campaign ROI analysis
- Best channels: email, push notifications, QR

**5. Rewards & Loyalty** (5 predefined questions)
- Which rewards work best?
- How much incentive without affecting margin?
- Activation vs retention strategies
- Customer loyalty analysis
- Pigui Points usage and effectiveness

**6. Products & Services** (5 predefined questions)
- Most and least profitable products
- Margin by product
- Products that attract new customers
- Services that generate recurrence
- Data-driven pricing adjustments

**7. Operations & Branch Performance** (5 predefined questions)
- Performance by branch
- Comparison between branches
- Peak sales hours
- Capacity vs demand analysis
- Operational efficiency metrics

**8. Customer Experience** (5 predefined questions)
- Customer feedback analysis
- Friction points in customer journey
- Rewards as part of the experience
- Personalization by customer
- Brand perception and sentiment

**9. Growth & Strategy** (5 predefined questions)
- New customer activation strategies
- Retention and churn analysis
- Organic growth opportunities
- What to scale and what to optimize
- Data-driven decisions, not intuition

**Total: 41 predefined business analysis questions**

### 6. Error Handling

- Required parameter validation (client_id and branch_id)
- Specific handling for ForeignKeyViolationError (invalid user/branch)
- Configured timeouts:
  - ASR: 20 seconds
  - Standard API calls: 60 seconds
  - Conversation operations: 120 seconds
- User-friendly error messages

### 7. AI Configuration

- **Model**: GPT-4-1106-preview
- **Context Type**: contextual
- **Temperature**: 0.7
- **Max Tokens**: 1024
- **TTS Model**: tts-1-hd
- **TTS Voice**: nova
- **Audio Format**: MP3
- **TTS Speed**: 1.0

## Deployment

### Docker Configuration

```dockerfile
FROM python:3.11-slim
WORKDIR /app
EXPOSE 8080
CMD ["streamlit", "run", "streamlit_chat_branch.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

### Dependencies

```
streamlit
requests
audio-recorder-streamlit
```

### Running Locally

```bash
streamlit run streamlit_chat_branch.py
```

Access the application with required URL parameters:
```
http://localhost:8501/?client_id=<CLIENT_ID>&branch_id=<BRANCH_ID>
```

### Running with Docker

```bash
docker build -t pigui-demo .
docker run -p 8080:8080 pigui-demo
```

## Application Flow

1. User accesses application with URL parameters: `?client_id=xxx&branch_id=yyy`
2. Parameters are validated (both required)
3. Conversation history is loaded from API
4. Automatic greeting sent if no active conversation ("Hello" message)
5. User interactions:
   - Type free-form messages
   - Select predefined questions
   - Load previous conversations
   - Edit conversation titles
   - Start new conversations
   - Play audio responses (TTS)

## Configuration Files

### .streamlit/config.toml

```toml
[client]
toolbarMode = "minimal"
showErrorDetails = false

[ui]
hideTopBar = false

[server]
headless = true

[browser]
gatherUsageStats = false

[runner]
fastReruns = true

[theme]
base = "dark"
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
```

## Current Status

### Implemented Features
- Dark theme forced globally across all components
- Wide layout with centered content (1200px max-width)
- Rounded chat input styling
- Complete conversation management system
- 41 organized predefined questions
- Text-to-Speech (TTS) functionality
- Conversation history with editing capabilities
- Automatic greeting on initialization

### Known Limitations
- ASR (Speech-to-Text) function exists but not implemented in UI
- JavaScript centering code may be redundant with CSS implementation

## API Environments

- **Development**: https://backdev.pigui.ai/
- **Staging**: https://backstagg.pigui.ai/
- **Production**: https://backprd.pigui.ai/

Current configuration points to development environment.

## Security Notes

- Client and branch IDs are required for all operations
- User ID defaults to client ID if not provided
- Foreign key validation ensures valid user/branch references
- All API calls include timeout protection
