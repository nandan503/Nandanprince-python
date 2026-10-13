#!/usr/bin/env bash
# ==============================================================================
# Python Error Logger - Bash Automation & Execution Script
# ==============================================================================
# Convenience script to run, test, and manage the Python Error Logger system.
#
# Usage:
#   ./run.sh          # Interactive selector
#   ./run.sh demo     # Run all 8 demonstration scenarios
#   ./run.sh test     # Run all 13 automated unit tests
#   ./run.sh summary  # View error metrics summary
#   ./run.sh view     # View logs in terminal
#   ./run.sh clear    # Clear logs
#   ./run.sh web      # Start web dashboard
#   ./run.sh gui      # Start Tkinter GUI
# ==============================================================================

set -e

# Change to script directory
cd "$(dirname "$0")"

# Colors for terminal styling
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}========================================================================${NC}"
    echo -e "${CYAN}🛡️  PYTHON ERROR LOGGER - BASH RUNNER${NC}"
    echo -e "${CYAN}========================================================================${NC}"
}

# Check Python 3 availability
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[Error] Python 3 is not installed or not in your PATH.${NC}"
    exit 1
fi

ACTION="${1:-}"

case "$ACTION" in
    demo)
        print_header
        echo -e "${GREEN}[Running] All 8 Demonstration Scenarios...${NC}"
        python3 main.py --demo
        ;;
    test)
        print_header
        echo -e "${GREEN}[Running] Automated Unit Test Suite (13 tests)...${NC}"
        python3 -m unittest discover -s tests -v
        ;;
    summary)
        print_header
        echo -e "${GREEN}[Running] Diagnostic Error Summary Report...${NC}"
        python3 main.py --summary
        ;;
    view)
        print_header
        echo -e "${GREEN}[Viewing] Latest Log Entries (logs/app.log)...${NC}"
        python3 main.py --view
        ;;
    clear)
        print_header
        echo -e "${YELLOW}[Clearing] Resetting log file...${NC}"
        python3 main.py --clear
        ;;
    web)
        print_header
        echo -e "${GREEN}[Starting] Web Dashboard on http://127.0.0.1:8000...${NC}"
        python3 web_dashboard.py
        ;;
    gui)
        print_header
        echo -e "${GREEN}[Starting] Tkinter Desktop GUI Dashboard...${NC}"
        python3 gui.py
        ;;
    cli)
        python3 main.py
        ;;
    *)
        print_header
        echo "Choose an action to run:"
        echo "  1) 🚀 Run All 8 Demonstration Scenarios (demo)"
        echo "  2) 🧪 Run Automated Unit Tests (test)"
        echo "  3) 📊 View Error Summary Report (summary)"
        echo "  4) 📜 View Log File (view)"
        echo "  5) 🖥️ Interactive Python Menu (cli)"
        echo "  6) 🌐 Launch Web Dashboard (web)"
        echo "  7) 🧹 Clear Log File (clear)"
        echo "  0) 🚪 Exit"
        echo ""
        read -r -p "Enter choice [0-7]: " CHOICE

        case "$CHOICE" in
            1) python3 main.py --demo ;;
            2) python3 -m unittest discover -s tests -v ;;
            3) python3 main.py --summary ;;
            4) python3 main.py --view ;;
            5) python3 main.py ;;
            6) python3 web_dashboard.py ;;
            7) python3 main.py --clear ;;
            0) echo "Goodbye!"; exit 0 ;;
            *) echo -e "${RED}Invalid choice.${NC}"; exit 1 ;;
        esac
        ;;
esac
