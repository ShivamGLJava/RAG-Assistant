# RAG Assistant Frontend - React UI

## Overview

Professional React-based chat interface for the Technical Support RAG Assistant. This is Engineer 5's (SYS) responsibility: building a production-ready UI for querying the RAG system.

## Features

✅ **Chat Interface** - Clean, professional conversation view
✅ **Source Attribution** - Shows which documents answered each question
✅ **Confidence Scoring** - Displays retrieval confidence levels
✅ **Mock Data Support** - Works standalone while backend is being built
✅ **Error Handling** - Graceful error messages and fallbacks
✅ **Responsive Design** - Mobile-friendly UI
✅ **Loading States** - Visual feedback during query processing

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx      # Main chat orchestrator
│   │   ├── MessageList.jsx        # Display messages & history
│   │   ├── SourceAttribution.jsx  # Show sources with scores
│   │   └── InputField.jsx         # Query input field
│   ├── services/
│   │   └── api.js                 # Backend API calls & mock data
│   ├── styles/
│   │   ├── ChatInterface.css
│   │   ├── MessageList.css
│   │   ├── InputField.css
│   │   └── SourceAttribution.css
│   ├── App.js
│   ├── App.css
│   ├── index.css
│   └── index.js
├── public/
│   └── index.html
├── package.json
└── .env (optional)
```

## Getting Started

### Prerequisites
- Node.js v16+
- npm v8+

### Installation

```bash
cd frontend
npm install
```

### Running the App

**Development Mode** (with hot reload):
```bash
npm start
```
Opens on `http://localhost:3000`

**Production Build**:
```bash
npm run build
```

### Configuration

Backend API URL can be set via environment variable:

```bash
# .env file
REACT_APP_API_URL=http://localhost:8000
```

If not set, defaults to `http://localhost:8000`

## Component Architecture

### ChatInterface
**Main orchestrator** - manages conversation state and API calls
- Detects if backend is available
- Falls back to mock data if backend is unreachable
- Routes queries to real API or mock data
- Handles different response statuses (success, no_reliable_answer, error)

### MessageList
**Display component** - renders conversation history
- Alternates between user and assistant messages
- Auto-scrolls to latest message
- Shows empty state with example questions
- Integrates source attribution for each response

### SourceAttribution
**Metadata display** - shows answer provenance
- Lists source documents and chunk IDs
- Displays relevance scores
- Shows confidence levels (Low/Medium/High/Very High)
- Color-coded confidence badges

### InputField
**User input** - text entry and submission
- Enter to send, Shift+Enter for new line
- Disabled state during API calls
- Loading spinner during query processing
- Input validation (prevents empty queries)

### API Service (api.js)
**Backend communication layer**
- `api.query()` - sends real query to backend
- `api.health()` - checks if backend is available
- `api.mockQuery()` - returns demo responses (for testing)

## API Contract

### /query Endpoint

**Request**:
```javascript
{
  "user_query": "How do I fix a 502 error?",
  "metadata_filter": {
    "department": "Engineering"  // optional
  }
}
```

**Response**:
```javascript
{
  "answer": "To fix a 502 Bad Gateway error...",
  "sources": [
    {
      "document": "troubleshooting_guide.md",
      "chunk_id": "doc_001_chk_1",
      "relevance_score": 0.92
    }
  ],
  "status": "success",
  "confidence_score": 0.92
}
```

**Response Statuses**:
- `success` - Answer generated successfully
- `no_reliable_answer` - Hallucination firewall blocked (insufficient evidence)
- `error` - Server-side error occurred

## Mock Data

When backend is unavailable, the app uses mock responses for these keywords:
- "crashloopbackoff" → Kubernetes pod issue
- "502" → Bad Gateway troubleshooting
- "imagepullbackoff" → Image pull failure
- Default → Generic technical response

## Styling

Uses modern CSS with:
- **Color Scheme**: Purple gradient (`#667eea` → `#764ba2`)
- **Responsive**: Mobile-first design
- **Animations**: Smooth transitions and slide-in effects
- **Accessibility**: Proper contrast ratios and semantic HTML

## Features to Add (For Integration)

When backend is ready:
1. Replace mock queries with real backend calls
2. Add message persistence (localStorage or DB)
3. Add feedback collection (Helpful/Not Helpful buttons)
4. Add export conversation feature
5. Add theme switching (light/dark mode)
6. Add metadata filtering UI

## Testing

### Manual Testing
1. Start the app: `npm start`
2. Type a query: "How do I fix a 502 error?"
3. Verify response appears with sources
4. Check source attribution displays correctly
5. Test error states by stopping backend

### Unit Tests (Future)
```bash
npm test
```

## Performance Notes

- **Bundle Size**: ~150KB (gzipped)
- **Lazy Loading**: Components load on demand
- **Auto-scroll**: Efficient scroll-to-bottom implementation
- **API Caching**: Consider adding with SWR/React Query

## Known Limitations

- Currently uses mock data when backend unavailable
- No message persistence (clears on page refresh)
- No offline mode
- Single conversation (no conversation history)

## Integration with Other Engineers

| Engineer | Component | Integration Point |
|----------|-----------|-------------------|
| Engineer 1 (DI) | Document Parsing | Uses parsed chunks from RRF |
| Engineer 2 (SR) | Vector DB | Indirectly via RRF results |
| Engineer 3 (BA-A) | FastAPI | Calls `/query` endpoint |
| Engineer 4 (BA-B) | RRF Engine | Receives ranked results |

## Troubleshooting

**Issue**: Backend connection failed
**Solution**: Check if backend is running on port 8000, or app will use mock data

**Issue**: Styles not applying
**Solution**: Clear browser cache and restart dev server

**Issue**: Port 3000 already in use
**Solution**: 
```bash
lsof -ti:3000 | xargs kill -9  # Unix/Mac
netstat -ano | findstr :3000   # Windows
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari 12+, Chrome Android Latest

## Future Enhancements

- [ ] Real-time chat updates (WebSocket)
- [ ] Voice input/output
- [ ] Multi-turn conversations with context
- [ ] Conversation history & management
- [ ] Feedback collection for RLHF
- [ ] Dark mode
- [ ] Export conversations as PDF
- [ ] User authentication
