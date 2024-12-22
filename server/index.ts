import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { createServer } from 'http';

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;
const server = createServer(app);

// Middleware
app.use(cors());
app.use(express.json());

// Import and use API routes
import toolsRouter from './api/tools';
app.use('/api/tools', toolsRouter);

// Add a test endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
server.listen(port, () => {
  console.log('=================================');
  console.log(`Server running at http://localhost:${port}`);
  console.log('Environment:', process.env.NODE_ENV);
  console.log('=================================');
});
