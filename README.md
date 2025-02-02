# CandyCrushGeminiBot

An intelligent bot that plays Candy Crush Saga using Google's Gemini AI for move analysis and strategic gameplay.

## Features

- Automated gameplay using computer vision and AI analysis
- Strategic move planning with 3-move lookahead
- Special candy creation and combination optimization
- Automated screenshot capture and analysis
- Interactive game board region selection
- Configurable screenshot intervals and retention
- Detailed move analysis and logging

## Requirements

- Python 3.8+
- Google Cloud Gemini API key
- Pillow >= 10.0.0
- PyYAML >= 6.0.1
- requests
- pyautogui

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CandyCrushGeminiBot.git
cd CandyCrushGeminiBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Gemini API key:
   - Obtain an API key from Google Cloud Console
   - Replace `GEMINI_API_KEY` in `play-game.py` with your actual key

## Configuration

Edit `config.yaml` to customize bot behavior:

```yaml
interval_ms: 10000        # Screenshot interval in milliseconds
save_dir: "screenshots"   # Directory to save screenshots
region: []               # Leave empty to select region at runtime
file_prefix: "screenshot" # Prefix for screenshot filenames
selection_mode: "manual"  # 'manual' or 'interactive'
retention_minutes: 1      # How long to keep images (in minutes)
```

## Usage

1. Start the game and navigate to a Candy Crush Saga level
2. Run the bot:
```bash
python play-game.py
```
3. Select the game board area when prompted
4. The bot will begin analyzing and playing automatically

## How It Works

1. **Screenshot Capture**: Takes periodic screenshots of the game board
2. **AI Analysis**: Uses Gemini AI to:
   - Analyze the current game state
   - Identify special candies and combinations
   - Plan strategic moves with cascade effects
   - Optimize for level objectives
3. **Move Execution**: Automatically performs the best calculated move
4. **Monitoring**: Provides detailed analysis and logging of each move

## Project Structure

- `play-game.py`: Main bot logic and Gemini AI integration
- `screenshot_lib.py`: Screenshot capture and management utilities
- `config.yaml`: Bot configuration settings
- `requirements.txt`: Project dependencies
- `screenshot_tool.log`: Operation logs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational purposes only. Use at your own risk and ensure compliance with game terms of service.
