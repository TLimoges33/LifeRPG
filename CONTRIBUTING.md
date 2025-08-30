# Contributing to LifeRPG

Thank you for your interest in contributing to LifeRPG! This guide will help you get started with contributing to our modern habit-tracking RPG system.

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- **Backend**: Python 3.10+ with FastAPI, SQLAlchemy, and Alembic
- **Frontend**: Node.js 18+ with React, Vite, and TailwindCSS v4
- **Mobile**: Expo SDK 53+ for React Native development
- **Database**: SQLite for development, PostgreSQL for production
- **Tools**: Docker, Git, and your favorite code editor

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TLimoges33/LifeRPG.git
   cd LifeRPG/modern
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   python demo_app.py  # Starts server on http://localhost:8000
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev  # Starts server on http://localhost:5173
   ```

4. **Mobile Setup** (optional):
   ```bash
   cd mobile
   npm install
   npx expo start
   ```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes**:
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests (when implemented)
   cd frontend && npm test
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Project Structure

```
modern/
├── backend/           # FastAPI backend
│   ├── demo_app.py   # Main application demo
│   ├── models/       # SQLAlchemy models
│   ├── api/          # API endpoints
│   └── tests/        # Backend tests
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/      # Custom hooks
│   │   └── utils/      # Utility functions
│   └── public/        # Static assets
├── mobile/           # React Native (Expo) app
└── ops/              # Deployment and monitoring
```

## Coding Standards

### Backend (Python)

- Follow **PEP 8** style guide
- Use **type hints** for all function parameters and returns
- Write **docstrings** for all public functions and classes
- Use **async/await** for I/O operations
- Handle errors gracefully with proper exception types

Example:
```python
async def create_habit(
    db: AsyncSession,
    user_id: int,
    habit_data: HabitCreate
) -> Habit:
    """Create a new habit for a user.
    
    Args:
        db: Database session
        user_id: ID of the user creating the habit
        habit_data: Habit creation data
        
    Returns:
        Created habit instance
        
    Raises:
        ValueError: If habit data is invalid
    """
```

### Frontend (React/TypeScript)

- Use **functional components** with hooks
- Follow **React best practices** (proper key props, avoid side effects in render)
- Use **TypeScript** for type safety
- Implement **proper error boundaries**
- Follow **accessibility guidelines** (WCAG 2.1)

Example:
```tsx
interface HabitCardProps {
  habit: Habit;
  onComplete: (habitId: number) => Promise<void>;
}

export const HabitCard: React.FC<HabitCardProps> = ({ habit, onComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const handleComplete = async () => {
    setIsLoading(true);
    try {
      await onComplete(habit.id);
    } catch (error) {
      // Handle error appropriately
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card>
      {/* Component content */}
    </Card>
  );
};
```

## Types of Contributions

### 🐛 Bug Reports
- Use the bug report template
- Include steps to reproduce
- Provide error messages and logs
- Test with the latest version

### ✨ Feature Requests
- Use the feature request template
- Explain the use case clearly
- Consider backward compatibility
- Discuss implementation approach

### 📝 Documentation
- Fix typos and unclear explanations
- Add examples and use cases
- Update outdated information
- Improve API documentation

### 🧪 Testing
- Add unit tests for new features
- Improve test coverage
- Add integration tests
- Performance testing

### 🎨 Design & UX
- Improve accessibility
- Enhance user experience
- Create design mockups
- Implement responsive design

## Release Process

1. **Version Bumping**: Follow [Semantic Versioning](https://semver.org/)
2. **Changelog**: Update CHANGELOG.md with user-facing changes
3. **Testing**: Ensure all tests pass and manual testing is complete
4. **Documentation**: Update relevant documentation
5. **Security**: Run security scans and address any issues

## Getting Help

- **Discord**: Join our [community Discord](https://discord.gg/liferpg) (placeholder)
- **Issues**: Check existing [GitHub Issues](https://github.com/TLimoges33/LifeRPG/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/TLimoges33/LifeRPG/discussions) for questions

## Recognition

Contributors are recognized in:
- **README.md** contributors section
- **CHANGELOG.md** for major contributions
- **GitHub Contributors** graph
- Annual contributor highlights

Thank you for helping make LifeRPG better! 🎮✨
