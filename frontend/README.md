# DashAgent Frontend

Hotel dashboard and analytics frontend built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 📊 **Dashboard Overview** - Stats cards showing total guests, reservations, chats, and transactions
- 📁 **File Upload Area** - Drag & drop CSV upload with progress tracking
- 📋 **Recent Uploads Table** - View upload history and status
- 🤖 **AI Chatbot Modal** - Large modal interface for AI assistance (placeholder for now)
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Charts**: Recharts (ready for future analytics)

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Backend Integration

The frontend connects to the DashAgent backend API at `http://localhost:8000`. Make sure the backend is running before using the frontend.

## API Endpoints Used

- `GET /dashboard/stats` - Dashboard statistics
- `GET /dashboard/recent-uploads` - Recent file uploads
- `POST /csv/upload` - Upload CSV files

## Project Structure

```
src/
├── app/
│   ├── globals.css      # Global styles with Tailwind
│   ├── layout.tsx       # Root layout component
│   └── page.tsx         # Main dashboard page
```

## Future Enhancements

- 📈 **Analytics Charts** - Revenue, occupancy, and trend visualizations
- 🔐 **Authentication** - User login and role-based access
- 📊 **Data Tables** - Detailed data views with filtering
- 🤖 **AI Integration** - Real AI chatbot with data analysis capabilities

