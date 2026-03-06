"""
Groww RAG Chatbot - Main Entry Point

Usage:
    python run.py scrape      - Run Phase 1: Scrape data from Groww
    python run.py process     - Run Phase 2: Process and structure data
    python run.py embed       - Run Phase 3: Build embeddings
    python run.py serve       - Run Phase 4: Start the server
    python run.py update      - Run full data update (scrape + process + embed)
    python run.py scheduler   - Run Phase 5: Start scheduler daemon
    python run.py test        - Run tests
    python run.py all         - Run full pipeline (update + serve)
"""

import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_scrape():
    """Run Phase 1: Scraping"""
    print("\n" + "=" * 60)
    print("Running Phase 1: Web Scraping")
    print("=" * 60)
    
    from phase1_scraper import GrowwScraper
    scraper = GrowwScraper()
    scraper.run()


def run_process():
    """Run Phase 2: Processing"""
    print("\n" + "=" * 60)
    print("Running Phase 2: Data Processing")
    print("=" * 60)
    
    from phase2_processing import DataProcessor
    processor = DataProcessor()
    processor.run()


def run_embed():
    """Run Phase 3: Embeddings"""
    print("\n" + "=" * 60)
    print("Running Phase 3: Building Embeddings")
    print("=" * 60)
    
    from phase3_rag import EmbeddingManager
    manager = EmbeddingManager(load_existing=False)
    manager.run()


def run_serve():
    """Run Phase 4: Server"""
    print("\n" + "=" * 60)
    print("Running Phase 4: Starting Server")
    print("=" * 60)
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    from phase4_backend.main import run_server
    run_server()


def run_update():
    """Run full data update"""
    print("\n" + "=" * 60)
    print("Running Full Data Update")
    print("=" * 60)
    
    run_scrape()
    run_process()
    run_embed()
    
    print("\n" + "=" * 60)
    print("[OK] Data update complete!")
    print("=" * 60)


def run_scheduler():
    """Run Phase 5: Scheduler"""
    print("\n" + "=" * 60)
    print("Running Phase 5: Scheduler")
    print("=" * 60)
    
    from phase5_scheduler.scheduler import run_scheduler
    run_scheduler()


def run_tests():
    """Run tests"""
    print("\n" + "=" * 60)
    print("Running Tests")
    print("=" * 60)
    
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])


def run_all():
    """Run full pipeline"""
    run_update()
    run_serve()


def print_help():
    """Print help message"""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        "scrape": run_scrape,
        "process": run_process,
        "embed": run_embed,
        "serve": run_serve,
        "update": run_update,
        "scheduler": run_scheduler,
        "test": run_tests,
        "all": run_all,
        "help": print_help,
        "-h": print_help,
        "--help": print_help,
    }
    
    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
