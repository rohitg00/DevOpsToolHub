# DevOps Tool Hub 🛠️

A comprehensive collection of DevOps tools and resources for the community. This platform helps developers discover, compare, and choose the right tools for their DevOps pipeline.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18.0-green.svg)](https://nodejs.org/)

## 🌟 Features

- **Comprehensive Tool Collection**: Access a curated list of over 2,500 DevOps tools
- **Categorized Browsing**: Find tools by categories like CI/CD, Monitoring, Security, etc.
- **Community Driven**: Upvote system to highlight the most valuable tools
- **Detailed Information**: Access tool descriptions, documentation, and GitHub READMEs
- **Open Source Focus**: Filter for open-source tools to support the community
- **Modern UI**: Clean, responsive interface for easy navigation

## 🚀 Quick Start

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Supabase account for database

### Installation

1. Clone the repository:
```bash
git clone https://github.com/rohitg00/DevOpsToolHub.git
cd DevOpsToolHub
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your Supabase credentials and other configurations.

4. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## 🐳 Docker Setup

### Using Docker Compose (Recommended)

1. Build and start the containers:
```bash
docker-compose up --build
```

2. Run in detached mode:
```bash
docker-compose up -d
```

3. View logs:
```bash
docker-compose logs -f
```

4. Stop the application:
```bash
docker-compose down
```

### Using Docker Directly

1. Build the Docker image:
```bash
docker build -t devops-tool-hub .
```

2. Run the container:
```bash
docker run -d \
  -p 3000:3000 \
  -p 5173:5173 \
  --name devops-tool-hub \
  -e VITE_SUPABASE_URL=your_supabase_url \
  -e VITE_SUPABASE_ANON_KEY=your_supabase_anon_key \
  -e DATABASE_URL=your_database_url \
  -v $(pwd)/logs:/app/logs \
  devops-tool-hub
```

3. View container logs:
```bash
docker logs -f devops-tool-hub
```

4. Stop the container:
```bash
docker stop devops-tool-hub
```

5. Remove the container:
```bash
docker rm devops-tool-hub
```

### Development with Local Services

1. Uncomment the `db` and `cache` services in `docker-compose.yml`
2. Start all services:
```bash
docker-compose up -d
```

3. Access the services:
   - Application: http://localhost:5173
   - API: http://localhost:3000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

### Environment Variables

Make sure to set up your environment variables before running Docker:
1. Copy the example env file:
```bash
cp .env.example .env
```

2. Update the variables in `.env`:
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
DATABASE_URL=your_database_url
```

### Docker Tips

- Clear all containers and volumes:
```bash
docker-compose down -v
```

- Rebuild specific service:
```bash
docker-compose up -d --build app
```

- View container status:
```bash
docker-compose ps
```

## 🏗️ Tech Stack

- **Frontend**:
  - React 18
  - TypeScript
  - Vite
  - Tailwind CSS
  - Shadcn UI
  - Tanstack Query

- **Backend**:
  - Node.js
  - Express
  - TypeScript
  - Supabase

- **Database**:
  - PostgreSQL (via Supabase)

## 📚 Project Structure

```
DevOpsToolHub/
├── client/               # Frontend React application
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   └── lib/         # Utilities and types
├── server/              # Backend Express server
│   ├── api/            # API routes
│   └── db/             # Database configuration
├── db/                 # Database migrations and schema
└── scripts/            # Utility scripts
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📖 Documentation

- [API Documentation](docs/api.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## 🔑 Environment Variables

Required environment variables:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
DATABASE_URL=your_database_url
```

## 🌐 Community

- Join our [Twitter Community](https://x.com/i/communities/1523681883384549376)

## 📈 Roadmap

- [ ] Tool comparison feature
- [ ] User reviews and ratings
- [ ] Tool integration guides
- [ ] API documentation generator
- [ ] Tool recommendation engine

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all the tool creators and maintainers
- The DevOps community for their valuable feedback
- All our contributors and supporters

## 🔗 Related Projects

- [Awesome DevOps](https://github.com/awesome-devops)
- [DevOps Resources](https://github.com/rohitg00/devopscommunity)
- [Cloud Native Landscape](https://landscape.cncf.io/)

## 📧 Contact

- Website: https://tools.devopscommunity.in

---

Made with ❤️ by the DevOps community 