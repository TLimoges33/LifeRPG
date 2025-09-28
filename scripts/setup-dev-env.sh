#!/bin/bash

# LifeRPG Development Environment Setup Script
# Automatically sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Setting up LifeRPG Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in supported environment
check_environment() {
    print_status "Checking environment compatibility..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "Linux detected ✓"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "macOS detected ✓"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        print_warning "Windows detected - using WSL/Git Bash is recommended"
    else
        print_warning "Unknown OS: $OSTYPE - proceeding anyway"
    fi
}

# Check for required system dependencies
check_dependencies() {
    print_status "Checking system dependencies..."
    
    # Required commands
    required_commands=("python3" "node" "npm" "git" "curl")
    missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        else
            print_success "$cmd found ✓"
        fi
    done
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        print_error "Missing required dependencies:"
        printf '%s\n' "${missing_commands[@]}"
        echo
        print_status "Please install missing dependencies and run this script again."
        echo
        echo "Installation guides:"
        echo "- Python 3.8+: https://www.python.org/downloads/"
        echo "- Node.js 18+: https://nodejs.org/en/download/"
        echo "- Git: https://git-scm.com/downloads"
        exit 1
    fi
    
    print_success "All system dependencies found!"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    cd modern/backend
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $python_version"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created!"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    if [ -f "requirements_ai.txt" ]; then
        pip install -r requirements_ai.txt
        print_success "AI dependencies installed!"
    fi
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Core dependencies installed!"
    fi
    
    cd ../..
}

# Setup Node.js environment
setup_node_env() {
    print_status "Setting up Node.js environment..."
    
    cd modern/frontend
    
    # Check Node version
    node_version=$(node --version)
    print_status "Node.js version: $node_version"
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    print_success "Node.js dependencies installed!"
    
    cd ../..
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    cd modern/backend
    
    # Activate Python environment
    source venv/bin/activate
    
    # Create database if it doesn't exist
    if [ ! -f "modern_dev.db" ]; then
        print_status "Creating database..."
        python -c "
import sqlite3
import os

# Create database
conn = sqlite3.connect('modern_dev.db')
cursor = conn.cursor()

# Read and execute schema
if os.path.exists('schema.sql'):
    with open('schema.sql', 'r') as f:
        schema = f.read()
    cursor.executescript(schema)
    print('Database schema created!')
else:
    print('No schema.sql found - creating basic tables')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

conn.commit()
conn.close()
print('Database setup complete!')
"
        print_success "Database created and initialized!"
    else
        print_status "Database already exists"
    fi
    
    cd ../..
}

# Download AI models
setup_ai_models() {
    print_status "Setting up AI models..."
    
    cd modern/backend
    source venv/bin/activate
    
    # Download models using Python script
    python -c "
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

print('Downloading AI models...')

# Create models directory
os.makedirs('ai_models', exist_ok=True)
os.chdir('ai_models')

try:
    # Download sentiment analysis model
    print('Downloading sentiment analysis model...')
    tokenizer = AutoTokenizer.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment-latest')
    model = AutoModelForSequenceClassification.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment-latest')
    
    tokenizer.save_pretrained('sentiment-model')
    model.save_pretrained('sentiment-model')
    print('Sentiment analysis model downloaded!')
    
    # Download classification model using pipeline
    print('Downloading text classification model...')
    classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
    # Save the model and tokenizer from the pipeline
    classifier.model.save_pretrained('classification-model')
    classifier.tokenizer.save_pretrained('classification-model')
    print('Text classification model downloaded!')
    
    print('All AI models downloaded successfully!')
    
except Exception as e:
    print(f'Error downloading models: {e}')
    print('Models will be downloaded on first use.')
"
    
    print_success "AI models setup complete!"
    cd ../..
}

# Create development configuration
create_dev_config() {
    print_status "Creating development configuration..."
    
    # Backend environment file
    if [ ! -f "modern/backend/.env.dev" ]; then
        cat > modern/backend/.env.dev << EOF
# Development Environment Configuration
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=sqlite:///modern_dev.db
SECRET_KEY=dev-secret-key-change-in-production
AI_MODELS_PATH=./ai_models
LOG_LEVEL=DEBUG

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# AI Configuration
HUGGINGFACE_CACHE_DIR=./ai_models
MAX_MODEL_MEMORY_MB=2048
ENABLE_AI_CACHING=true

# Performance Monitoring
ENABLE_METRICS=true
METRICS_EXPORT_INTERVAL=300
EOF
        print_success "Backend development config created!"
    fi
    
    # Frontend environment file
    if [ ! -f "modern/frontend/.env.local" ]; then
        cat > modern/frontend/.env.local << EOF
# Frontend Development Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
REACT_APP_ENABLE_AI_FEATURES=true
REACT_APP_ENABLE_DEBUG=true
GENERATE_SOURCEMAP=true
EOF
        print_success "Frontend development config created!"
    fi
}

# Setup development scripts
create_dev_scripts() {
    print_status "Creating development scripts..."
    
    # Backend start script
    cat > scripts/start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting LifeRPG Backend..."
cd modern/backend
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn app:app --reload --host 0.0.0.0 --port 8000
EOF
    
    # Frontend start script  
    cat > scripts/start-frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting LifeRPG Frontend..."
cd modern/frontend
npm start
EOF
    
    # Full stack start script
    cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting LifeRPG Full Stack Development Environment..."

# Start backend in background
echo "Starting backend..."
./scripts/start-backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
echo "Starting frontend..."
./scripts/start-frontend.sh &
FRONTEND_PID=$!

echo "✅ LifeRPG Development Environment Started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    print_success "Development scripts created!"
}

# Verify installation
verify_setup() {
    print_status "Verifying installation..."
    
    # Check Python environment
    cd modern/backend
    if [ -d "venv" ]; then
        source venv/bin/activate
        python_deps=$(pip list | wc -l)
        print_success "Python environment: $python_deps packages installed"
    else
        print_error "Python virtual environment not found!"
        return 1
    fi
    cd ../..
    
    # Check Node environment
    cd modern/frontend
    if [ -d "node_modules" ]; then
        node_deps=$(ls node_modules | wc -l)
        print_success "Node.js environment: $node_deps packages installed"
    else
        print_error "Node.js modules not found!"
        return 1
    fi
    cd ../..
    
    # Check database
    if [ -f "modern/backend/modern_dev.db" ]; then
        print_success "Database: Initialized"
    else
        print_warning "Database: Not found (will be created on first run)"
    fi
    
    print_success "✅ Setup verification complete!"
}

# Main execution
main() {
    echo
    echo "╔══════════════════════════════════════╗"
    echo "║        LifeRPG Setup Script          ║"
    echo "║   Complete Development Environment   ║"
    echo "╚══════════════════════════════════════╝"
    echo
    
    check_environment
    check_dependencies
    setup_python_env
    setup_node_env
    setup_database
    setup_ai_models
    create_dev_config
    create_dev_scripts
    verify_setup
    
    echo
    print_success "🎉 LifeRPG Development Environment Setup Complete!"
    echo
    echo "Next Steps:"
    echo "1. Run './scripts/start-dev.sh' to start the full development environment"
    echo "2. Visit http://localhost:3000 to access the application"
    echo "3. Visit http://localhost:8000/docs to see API documentation"
    echo
    echo "Individual Services:"
    echo "- Backend only: './scripts/start-backend.sh'"
    echo "- Frontend only: './scripts/start-frontend.sh'"
    echo
    print_status "Happy coding! 🚀"
}

# Run main function
main "$@"