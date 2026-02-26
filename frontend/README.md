# Frontend Setup Guide

## Prerequisites

- Node.js 16 or higher
- npm or yarn package manager
- Backend server running on localhost:8000

## Installation Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

### 3. Build for Production

```bash
npm run build
```

Production build will be in the `dist/` directory.

### 4. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── UI.jsx                 # Reusable UI components
│   │   ├── UI.module.css          # UI styles
│   │   ├── Navbar.jsx             # Navigation bar
│   │   └── Navbar.module.css      # Navbar styles
│   ├── pages/
│   │   ├── LoginPage.jsx          # Login form
│   │   ├── RegisterPage.jsx       # Registration form
│   │   ├── DashboardPage.jsx      # Main dashboard
│   │   ├── InterviewSetupPage.jsx # Resume & JD setup
│   │   ├── InterviewSessionPage.jsx # Interview questions
│   │   ├── ResultsPage.jsx        # Results & analysis
│   │   ├── Auth.module.css        # Auth pages styles
│   │   ├── Dashboard.module.css   # Dashboard styles
│   │   ├── InterviewSetup.module.css
│   │   ├── InterviewSession.module.css
│   │   └── Results.module.css
│   ├── context/
│   │   ├── AuthContext.jsx        # Auth state management
│   │   └── InterviewContext.jsx   # Interview state management
│   ├── services/
│   │   └── api.js                 # API client with axios
│   ├── hooks/                     # Custom React hooks
│   ├── utils/                     # Utility functions
│   ├── styles/
│   │   └── globals.css            # Global styles
│   ├── App.jsx                    # Main app component
│   └── main.jsx                   # React entry point
├── index.html                     # HTML template
├── vite.config.js                 # Vite configuration
├── package.json                   # Dependencies
├── .gitignore                     # Git ignore
└── README.md                      # This file
```

## Component Overview

### UI Components (`components/UI.jsx`)
Reusable components for the entire app:
- **Button**: Primary, secondary, success, danger variants
- **Card**: Container component with shadow
- **Input**: Text input with labels and error handling
- **Select**: Dropdown select component
- **TextArea**: Multi-line text input
- **Spinner**: Loading animation
- **Badge**: Small label badges
- **ProgressBar**: Progress indicator
- **StatCard**: Statistics display card
- **Modal**: Modal dialog
- **Alert**: Alert messages (success, error, warning, info)

### Pages

#### Auth Pages
- **LoginPage**: User login with email/password
- **RegisterPage**: New user registration

#### Dashboard
- **DashboardPage**: Main hub showing analytics and recent interviews

#### Interview Flow
- **InterviewSetupPage**: Resume upload, JD input, interview configuration
  - Resume upload (PDF/DOCX)
  - Job role and domain selection
  - Job description input
  - Resume vs JD analysis preview
  - Number of questions selection

- **InterviewSessionPage**: Actual interview with questions and timer
  - Displays current question
  - Answer input area
  - Timer (2 minutes per question)
  - Progress bar
  - Submit/Skip buttons

- **ResultsPage**: Shows complete results with analysis
  - Overall score
  - Resume match analysis (THE KEY FEATURE)
  - ATS score
  - Matched/missing skills
  - Keyword gaps
  - Experience gap analysis
  - Resume improvement suggestions
  - ATS optimization tips
  - Question-wise performance

### Context Providers

#### AuthContext
- User login/logout
- Token management
- Profile data
- Global auth state

#### InterviewContext
- Interview data
- Current question tracking
- Answer submission
- Results fetching

## API Integration

The app uses Axios for HTTP requests. API calls are centralized in `services/api.js`:

```javascript
// Example API calls
import { authAPI, resumeAPI, interviewAPI, analyticsAPI } from './services/api';

// Auth
await authAPI.register(name, email, password);
await authAPI.login(email, password);

// Resume
await resumeAPI.upload(file);
await resumeAPI.list();

// Interview
await interviewAPI.create(setupData);
await interviewAPI.submitAnswer(interviewId, answerData);
await interviewAPI.complete(interviewId);

// Analytics
await analyticsAPI.getDashboard();
```

## Styling

The app uses CSS Modules for component-scoped styling:

```css
/* Component.module.css */
.button {
  /* styles */
}

.button:hover {
  /* hover styles */
}

@media (max-width: 768px) {
  /* Mobile styles */
}
```

Global styles are in `styles/globals.css` with CSS custom properties:

```css
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  /* ... other vars */
}
```

## Routing

Routes are defined in `App.jsx` using React Router:

```
/                 → Dashboard (or login if not authenticated)
/login            → Login page
/register         → Registration page
/dashboard        → Main dashboard
/setup            → Interview setup
/interview/:id    → Interview session
/results/:id      → Results page
```

Protected routes require authentication. Unauthenticated users are redirected to `/login`.

## State Management

### Global State
- **Auth**: AuthContext for user data and authentication
- **Interview**: InterviewContext for interview data and session

### Local State
- Individual page components maintain their own local state using `useState`

### Optimization
- Contexts are wrapped at the root level in `App.jsx`
- State updates trigger re-renders only for components that consume that context

## Environment Variables

Set API base URL in `vite.config.js` proxy section or directly in API calls:

```javascript
// In vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

## Development Workflow

### 1. Hot Module Replacement (HMR)
Changes to React components are automatically reflected in the browser without page reload.

### 2. Debugging
Use React DevTools browser extension for debugging:
```bash
# Install React DevTools extension in Chrome or Firefox
```

### 3. Network Debugging
Use browser DevTools Network tab to inspect API calls and responses.

### 4. Console Debugging
```javascript
console.log('Debug message:', variable);
console.error('Error message:', error);
console.table(arrayOfObjects);
```

## Building and Deployment

### Build for Production
```bash
npm run build

# Creates optimized bundle in dist/
```

### Deploy to Vercel
```bash
npm install -g vercel
vercel
# Follow prompts
```

### Deploy to Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir dist
```

### Deploy to GitHub Pages
```bash
# Update vite.config.js with base path
# Then build
npm run build

# Deploy dist folder to GitHub Pages
```

## Performance Optimization

### Code Splitting
Vite automatically splits code for each route to reduce initial bundle size.

### CSS Optimization
CSS Modules are scoped and minified in production builds.

### Image Optimization
Use optimized image formats (WebP, AVIF). Vite handles this automatically.

### Lazy Loading
Routes are lazy loaded:
```javascript
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
```

## Common Issues & Solutions

### API Connection Error
```
Error: Failed to connect to backend
```
- Ensure backend server is running on port 8000
- Check proxy settings in vite.config.js
- Verify CORS is enabled on backend

### Token Expiration
```
Error: Invalid token
```
- Token is automatically refreshed via interceptor
- Check token expiration time in backend

### Resume Upload Fails
```
Error: Failed to upload resume
```
- Verify file is PDF or DOCX
- Check file size (max 10MB)
- Ensure upload endpoint is working

### Styling Issues
```
Styles not applying
```
- Check CSS Module import in component
- Verify class names match CSS file
- Clear browser cache (Ctrl+Shift+Delete)

## Testing Your Changes

### Test Login Flow
1. Go to http://localhost:5173/login
2. Click "Register now"
3. Fill registration form
4. Should redirect to dashboard

### Test Interview Flow
1. Dashboard → "Start New Interview"
2. Upload a test resume
3. Enter job role, domain, JD
4. Review analysis
5. Start interview
6. Answer questions
7. View results

### Test Responsive Design
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test different screen sizes

## Browser Support

- Chrome/Edge: Latest versions ✅
- Firefox: Latest versions ✅
- Safari: Latest versions ✅
- Mobile browsers: iOS Safari, Chrome on Android ✅

## Useful Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code (if ESLint configured)
npm run lint

# Format code (if Prettier configured)
npm run format
```

## Next Steps

1. Start the backend server
2. Run `npm run dev`
3. Open http://localhost:5173
4. Create an account
5. Try the interview platform!

---

## Support

For help:
1. Check browser console for errors (F12)
2. Check network tab for API errors
3. Verify backend is running
4. Check backend logs for detailed errors
5. Create an issue on GitHub

Happy interviewing! 🚀
